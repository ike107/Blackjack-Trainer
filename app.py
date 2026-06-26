# app.py
import streamlit as st
from config import DEFAULT_BET_AMOUNT
from logic import draw_card, calculate_total, generate_hard_mode_hand, get_correct_action
from views import render_simulation_page, render_counting_page

st.title("Blackjack Trainer")

# --- 1. サイドバーで設定（常に表示） ---
st.sidebar.header("賭け金設定")
bet_amount = st.sidebar.number_input(
    "1ゲームのベット額（円）:",
    min_value=500,       # 最低ベット
    max_value=1000000,   # 最高ベット
    value=DEFAULT_BET_AMOUNT,  # 👈 初期値として3500を設定
    step=500,            # 500円刻みで増減
)

# --- 2. モード選択 ---
mode = st.radio(
    "🎲 プレイモードを選択してください",
    [
        "通常モード（完全ランダム）", 
        "特訓モード（難問・嫌な手札限定）", 
        "高速自動シミュレーション（期待値検証）", 
        "カウンティング練習"
    ]
)

st.write("---")

# --- 3. セッション状態の初期化 ---
# 「現在ゲームがアクティブ（プレイ中）かどうか」を管理するフラグを追加
if "game_active" not in st.session_state:
    st.session_state.game_active = False

if "total_profit" not in st.session_state: st.session_state.total_profit = 0
if "wins" not in st.session_state: st.session_state.wins = 0
if "losses" not in st.session_state: st.session_state.losses = 0
if "draws" not in st.session_state: st.session_state.draws = 0
if "total_actions" not in st.session_state: st.session_state.total_actions = 0
if "correct_actions" not in st.session_state: st.session_state.correct_actions = 0


# サイドバーの戦績表示
st.sidebar.metric("通算収支", f"{st.session_state.total_profit:,} 円")
st.sidebar.metric("勝敗内訳", f"{st.session_state.wins}勝 {st.session_state.losses}敗 {st.session_state.draws}分")
if st.session_state.total_actions > 0:
    accuracy = (st.session_state.correct_actions / st.session_state.total_actions) * 100
    st.sidebar.metric("ストラテジー正解率", f"{accuracy:.1f} %")
else:
    st.sidebar.metric("ストラテジー正解率", "0.0 %")

if st.sidebar.button("データをリセット"):
    st.session_state.total_profit = 0
    st.session_state.wins = 0
    st.session_state.losses = 0
    st.session_state.draws = 0
    st.session_state.total_actions = 0
    st.session_state.correct_actions = 0
    st.session_state.game_active = False # リセット時は非アクティブに
    st.rerun()

# --- 4. 特殊モードの割り振りとゲーム開始前画面の制御 ---

# 【A. シミュレーションモード】※シミュレーション自体がボタン制御なのでそのまま呼び出し
if mode == "高速自動シミュレーション（期待値検証）":
    render_simulation_page(bet_amount)

# 【B. カウンティングモード】※こちらも内部に開始ボタンがあるためそのまま呼び出し
elif mode == "カウンティング練習":
    render_counting_page(bet_amount)

# 【C. 通常モード ＆ 特訓モード】★ここにゲーム開始ボタンを挟むロジックを追加
else:
    # モードに応じた説明文を、開始前・プレイ中問わず上部に表示
    if mode == "通常モード）":
        st.header("通常モード")
        st.write(f"本番を想定した完全ランダムな配布で、ベーシックストラテジーに基づく最適なアクションを実戦形式で練習します。")
    elif mode == "特訓モード":
        st.header("特訓モード（難問・ペア・ソフトハンド限定）")
        st.write(f"判断に迷いやすい「ペアハンド」や「ソフトハンド」、勝率が分かれる「難問手札」を集中して引き当て、弱点を克服します。")

    st.info(f"現在の設定 ➡ **{mode}** / ベット額: **{bet_amount:,} 円**")

    # 🌟 モードを切り替えたら、一旦ゲームを未開始状態に戻すための安全弁
    # （前のモードの手札を引き継いでバグるのを防ぐ）
    if "last_mode" not in st.session_state:
        st.session_state.last_mode = mode
    if st.session_state.last_mode != mode:
        st.session_state.game_active = False
        st.session_state.last_mode = mode

    # 🌟 まだゲームを開始していない（決定ボタンを押していない）場合
    if not st.session_state.game_active:
        st.write("上の設定を確認し、よろしければ「ゲームを開始する」ボタンを押してください。")
        if st.button("🎮 この設定でゲームを開始する", type="primary", use_container_width=True):
            # カードを配って初期化し、アクティブ状態にする
            st.session_state.dealer_hand = [draw_card(), draw_card()]
            st.session_state.player_hands = [generate_hard_mode_hand()] if "特訓モード" in mode else [[draw_card(), draw_card()]]
            st.session_state.hand_bets = [bet_amount]
            st.session_state.current_hand_idx = 0
            st.session_state.history = []
            st.session_state.game_status = "player_turn"
            st.session_state.game_active = True  # 👈 プレイ中フラグをONにする
            st.rerun()

    # 🌟 「決定」されてゲームが動いている間のみ、以下のプレイ画面を描画する
    else:
        # ストラテジー表（カンペ）の表示
        with st.expander("ストラテジー表を確認（カンペ）"):
            columns = ["自分の手", "2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]
            st.caption("🇸🇬 マリーナベイ・サンズ（MBS）公式ルール（制限なしダブル / A以外サレンダーあり）")
            
            st.markdown("**【ハードハンド】**")
            sg_hard = [
                ["17以上", "S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
                ["16",    "S", "S", "S", "S", "S", "H", "H", "R", "R", "H"], 
                ["15",    "S", "S", "S", "S", "S", "H", "H", "H", "R", "H"], 
                ["13-14", "S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
                ["12",    "H", "H", "S", "S", "S", "H", "H", "H", "H", "H"],
                ["11",    "D", "D", "D", "D", "D", "D", "D", "D", "D", "D"],
                ["10",    "D", "D", "D", "D", "D", "D", "D", "D", "H", "H"],
                ["9",     "H", "D", "D", "D", "D", "H", "H", "H", "H", "H"],
                ["8以下",  "H", "H", "H", "H", "H", "H", "H", "H", "H", "H"]
            ]
            st.table([dict(zip(columns, row)) for row in sg_hard])
            
            st.markdown("**【ソフトハンド】**")
            sg_soft = [
                ["A,8以上", "S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
                ["A,7",    "S", "D", "D", "D", "D", "S", "S", "H", "H", "H"],
                ["A,6",    "H", "D", "D", "D", "D", "H", "H", "H", "H", "H"],
                ["A,4 / A,5", "H", "H", "D", "D", "D", "H", "H", "H", "H", "H"],
                ["A,2 / A,3", "H", "H", "H", "D", "D", "H", "H", "H", "H", "H"]
            ]
            st.table([dict(zip(columns, row)) for row in sg_soft])
            
            st.markdown("**【ペアハンド】**")
            sg_pair = [
                ["A,A", "P", "P", "P", "P", "P", "P", "P", "P", "P", "P"],
                ["10,10", "S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
                ["9,9",   "P", "P", "P", "P", "P", "S", "P", "P", "S", "S"],
                ["8,8",   "P", "P", "P", "P", "P", "P", "P", "P", "P", "P"],
                ["7,7",   "P", "P", "P", "P", "P", "P", "H", "H", "H", "H"],
                ["6,6",   "P", "P", "P", "P", "P", "H", "H", "H", "H", "H"],
                ["5,5",   "D", "D", "D", "D", "D", "D", "D", "D", "H", "H"],
                ["4,4",   "H", "H", "H", "P", "P", "H", "H", "H", "H", "H"],
                ["2,2 / 3,3", "P", "P", "P", "P", "P", "P", "H", "H", "H", "H"]
            ]
            st.table([dict(zip(columns, row)) for row in sg_pair])

        dealer_up = st.session_state.dealer_hand[0]
        st.subheader("【ディーラーのアップカード】")
        st.markdown(f"### ` [ {dealer_up} ] `")
        st.write("---")
        st.subheader("【あなたの手札】")

        for idx, hand in enumerate(st.session_state.player_hands):
            total = calculate_total(hand)
            hand_str = " ".join([f"`[ {c} ]`" for c in hand])
            if st.session_state.game_status == "player_turn" and idx == st.session_state.current_hand_idx:
                st.markdown(f"👉 **手札 {idx+1}:** {hand_str} (合計: **{total}**) ※操作中")
            else:
                st.markdown(f"  **手札 {idx+1}:** {hand_str} (合計: **{total}**)")

        st.write("---")
        for msg, msg_type in st.session_state.history:
            if msg_type == "success": st.success(msg)
            elif msg_type == "error": st.error(msg)
            else: st.info(msg)

        # --- プレイヤーのターン処理 ---
        if st.session_state.game_status == "player_turn":
            idx = st.session_state.current_hand_idx
            current_hand = st.session_state.player_hands[idx]
            correct_action = get_correct_action(current_hand, dealer_up)

            allow_split = len(current_hand) == 2 and current_hand[0] == current_hand[1]
            allow_double = (len(current_hand) == 2)
            allow_surrender = (len(current_hand) == 2 and len(st.session_state.player_hands) == 1 and dealer_up != 'A')

            col1, col2, col3, col4, col5 = st.columns(5)
            action = None
            with col1:
                if st.button("H: ヒット", use_container_width=True): action = "H"
            with col2:
                if st.button("S: スタンド", use_container_width=True): action = "S"
            with col3:
                if st.button("D: ダブル", disabled=not allow_double, use_container_width=True): action = "D"
            with col4:
                if st.button("P: スプリット", disabled=not allow_split, use_container_width=True): action = "P"
            with col5:
                if st.button("R: サレンダー", disabled=not allow_surrender, use_container_width=True): action = "R"

            if action:
                st.session_state.total_actions += 1
                action_names = {"H": "ヒット", "S": "スタンド", "D": "ダブルダウン", "P": "スプリット", "R": "サレンダー"}
                if action == correct_action:
                    st.session_state.correct_actions += 1
                    st.session_state.history.append((f"【判定】正解です！「{action_names[correct_action]}」です。", "success"))
                else:
                    st.session_state.history.append((f"【判定】ミス！ 選択: {action_names[action]} ➡ 正解: 「{action_names[correct_action]}」でした。", "error"))

                if action == "H":
                    current_hand.append(draw_card())
                    if calculate_total(current_hand) > 21:
                        st.session_state.history.append((f"手札 {idx+1} がバーストしました！", "error"))
                        if idx + 1 < len(st.session_state.player_hands): st.session_state.current_hand_idx += 1
                        else: st.session_state.game_status = "dealer_turn"
                    st.rerun()
                elif action == "S":
                    if idx + 1 < len(st.session_state.player_hands): st.session_state.current_hand_idx += 1
                    else: st.session_state.game_status = "dealer_turn"
                    st.rerun()
                elif action == "D":
                    st.session_state.hand_bets[idx] *= 2
                    current_hand.append(draw_card())
                    if idx + 1 < len(st.session_state.player_hands): st.session_state.current_hand_idx += 1
                    else: st.session_state.game_status = "dealer_turn"
                    st.rerun()
                elif action == "P":
                    card1, card2 = current_hand[0], current_hand[1]
                    current_bet = st.session_state.hand_bets[idx]
                    st.session_state.player_hands.pop(idx)
                    st.session_state.hand_bets.pop(idx)
                    st.session_state.player_hands.insert(idx, [card2, draw_card()])
                    st.session_state.hand_bets.insert(idx, current_bet)
                    st.session_state.player_hands.insert(idx, [card1, draw_card()])
                    st.session_state.hand_bets.insert(idx, current_bet)
                    st.rerun()
                elif action == "R":
                    st.session_state.game_status = "surrendered_end"
                    st.rerun()

        # --- サレンダー時の特殊精算 ---
        if st.session_state.game_status == "surrendered_end":
            loss_amount = st.session_state.hand_bets[0] // 2
            st.session_state.total_profit -= loss_amount
            st.session_state.losses += 1
            st.session_state.history.append((f"サレンダーが成立しました。(-{loss_amount:,}円)", "normal"))
            st.session_state.game_status = "end"
            st.rerun()

        # --- ディーラーのターン ＆ 結果判定 ---
        if st.session_state.game_status == "dealer_turn":
            all_busted = all(calculate_total(h) > 21 for h in st.session_state.player_hands)
            if not all_busted:
                while calculate_total(st.session_state.dealer_hand) < 17:
                    st.session_state.dealer_hand.append(draw_card())

            d_total = calculate_total(st.session_state.dealer_hand)
            round_profit = 0
            for idx, hand in enumerate(st.session_state.player_hands):
                p_total = calculate_total(hand)
                bet = st.session_state.hand_bets[idx]
                if p_total > 21:
                    round_profit -= bet
                    st.session_state.losses += 1
                    st.session_state.history.append((f"手札 {idx+1}: バースト負け (-{bet:,}円)", "normal"))
                elif d_total > 21:
                    round_profit += bet
                    st.session_state.wins += 1
                    st.session_state.history.append((f"手札 {idx+1}: ディーラーバーストで勝利 (+{bet:,}円)", "success"))
                elif p_total > d_total:
                    round_profit += bet
                    st.session_state.wins += 1
                    st.session_state.history.append((f"手札 {idx+1}: 勝利！ (+{bet:,}円)", "success"))
                elif p_total < d_total:
                    round_profit -= bet
                    st.session_state.losses += 1
                    st.session_state.history.append((f"手札 {idx+1}: 負け (-{bet:,}円)", "normal"))
                else:
                    st.session_state.draws += 1
                    st.session_state.history.append((f"手札 {idx+1}: 引き分け (プッシュ)", "normal"))

            st.session_state.total_profit += round_profit
            st.session_state.game_status = "end"
            st.rerun()

        # --- ゲーム終了 ---
        if st.session_state.game_status == "end":
            d_total = calculate_total(st.session_state.dealer_hand)
            d_hand_str = " ".join([f"`[ {c} ]`" for c in st.session_state.dealer_hand])
            st.write("---")
            st.subheader("【ディーラーの最終手札】")
            st.markdown(f"{d_hand_str} (合計: **{d_total}**)")

            if st.button("次のゲームへ", type="primary", use_container_width=True):
                # 次のゲームのために再びカードを初期化してループを回す
                st.session_state.dealer_hand = [draw_card(), draw_card()]
                st.session_state.player_hands = [generate_hard_mode_hand()] if "特訓モード" in mode else [[draw_card(), draw_card()]]
                st.session_state.hand_bets = [bet_amount]
                st.session_state.current_hand_idx = 0
                st.session_state.history = []
                st.session_state.game_status = "player_turn"
                st.rerun()
