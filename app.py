# app.py
import streamlit as st
from config import BET_AMOUNT
from logic import draw_card, calculate_total, generate_hard_mode_hand, get_correct_action
from views import render_simulation_page, render_counting_page

st.title("Blackjack Trainer")

mode = st.radio(
    "🎲 プレイモードを選択",
    ["通常モード（完全ランダム）", "特訓モード（難問・嫌な手札限定）", "高速自動シミュレーション（期待値検証）", "カウンティング特訓（自動プレイ観戦）"],
    horizontal=True
)

# 特殊モードは views.py の関数へ委託
if mode == "高速自動シミュレーション（期待値検証）":
    render_simulation_page()

elif mode == "カウンティング特訓（自動プレイ観戦）":
    render_counting_page()

# 通常プレイ・特訓モードのメインUI
else:
    # 🌟 ここに各モードごとの簡単な説明を追加します
    if mode == "通常モード（完全ランダム）":
        st.header("通常モード")
        st.write("ベーシックストラテジーに基づく最適なアクションを選択するモード")
        
    elif mode == "特訓モード（難問・嫌な手札限定）":
        st.header("特訓モード")
        st.write("判断に迷いやすい「ペアハンド」や「ソフトハンド」が中心のモード")

    # --- 以下は既存のロジックコードをそのまま継続 ---
    if "total_profit" not in st.session_state: st.session_state.total_profit = 0
    if "wins" not in st.session_state: st.session_state.wins = 0
    if "losses" not in st.session_state: st.session_state.losses = 0
    if "draws" not in st.session_state: st.session_state.draws = 0
    if "total_actions" not in st.session_state: st.session_state.total_actions = 0
    if "correct_actions" not in st.session_state: st.session_state.correct_actions = 0
    if "game_status" not in st.session_state: st.session_state.game_status = "init"
    if st.session_state.game_status == "init":
        st.session_state.dealer_hand = [draw_card(), draw_card()]
        st.session_state.player_hands = [generate_hard_mode_hand()] if "特訓モード" in mode else [[draw_card(), draw_card()]]
        st.session_state.hand_bets = [BET_AMOUNT]
        st.session_state.current_hand_idx = 0
        st.session_state.history = []
        st.session_state.game_status = "player_turn"

    st.sidebar.metric("基本ベット額", f"{BET_AMOUNT:,} 円 / 回")
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
        st.rerun()

    with st.expander("ストラテジー表を確認（カンペ）"):
        columns = ["自分の手", "2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]
        st.caption("MBS公式ルール（制限なしダブル / A以外サレンダーあり）")
        
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
            st.session_state.game_status = "init"
            st.rerun()