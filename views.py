# views.py
import streamlit as st
import pandas as pd
import time
from config import BET_AMOUNT
from logic import draw_card, calculate_total, get_correct_action

def run_blackjack_simulation(num_games):
    """指定された回数分、ベーシックストラテジーで自動プレイして収支推移を返す"""
    profit_history = [0]
    current_profit = 0
    wins, losses, draws = 0, 0, 0
    total_bet_money = 0
    
    for _ in range(num_games):
        dealer_hand = [draw_card(), draw_card()]
        dealer_up = dealer_hand[0]
        
        d_total_init = calculate_total(dealer_hand)
        is_dealer_bj = (len(dealer_hand) == 2 and d_total_init == 21)
        
        player_hands = [[draw_card(), draw_card()]]
        hand_bets = [BET_AMOUNT]
        is_surrendered = [False]
        is_ace_split_hand = [False]
        split_count = 0
        
        if not is_dealer_bj:
            hand_idx = 0
            while hand_idx < len(player_hands):
                current_hand = player_hands[hand_idx]
                if is_ace_split_hand[hand_idx]:
                    current_hand.append(draw_card())
                    hand_idx += 1
                    continue
                
                while True:
                    action = get_correct_action(current_hand, dealer_up)
                    if action == "P" and split_count >= 3:
                        action = "H" if current_hand[0] in ['A', '8', '9', '7', '6', '4', '3', '2'] else "S"
                    
                    if action == "H":
                        current_hand.append(draw_card())
                        if calculate_total(current_hand) > 21: break
                    elif action == "S": break
                    elif action == "D":
                        hand_bets[hand_idx] *= 2
                        current_hand.append(draw_card())
                        break
                    elif action == "R":
                        is_surrendered[hand_idx] = True
                        break
                    elif action == "P":
                        split_count += 1
                        card1, card2 = current_hand[0], current_hand[1]
                        current_bet = hand_bets[hand_idx]
                        is_ace_split = (card1 == 'A')
                        
                        player_hands.pop(hand_idx)
                        hand_bets.pop(hand_idx)
                        is_ace_split_hand.pop(hand_idx)
                        is_surrendered.pop(hand_idx)
                        
                        player_hands.insert(hand_idx, [card2, draw_card()])
                        hand_bets.insert(hand_idx, current_bet)
                        is_ace_split_hand.insert(hand_idx, is_ace_split)
                        is_surrendered.insert(hand_idx, False)
                        
                        player_hands.insert(hand_idx, [card1, draw_card()])
                        hand_bets.insert(hand_idx, current_bet)
                        is_ace_split_hand.insert(hand_idx, is_ace_split)
                        is_surrendered.insert(hand_idx, False)
                        current_hand = player_hands[hand_idx]
                hand_idx += 1
            
        all_finished = all(calculate_total(h) > 21 or is_surrendered[idx] for idx, h in enumerate(player_hands))
        if not is_dealer_bj and not all_finished:
            while calculate_total(dealer_hand) < 17:
                dealer_hand.append(draw_card())
                
        d_total = calculate_total(dealer_hand)
        
        for idx, hand in enumerate(player_hands):
            p_total = calculate_total(hand)
            bet = hand_bets[idx]
            total_bet_money += bet
            is_player_bj = (len(hand) == 2 and p_total == 21 and len(player_hands) == 1)
            
            if is_surrendered[idx]:
                current_profit -= (bet // 2)
                losses += 1
            elif p_total > 21:
                current_profit -= bet
                losses += 1
            elif is_player_bj and not is_dealer_bj:
                current_profit += int(bet * 1.5)
                wins += 1
            elif is_dealer_bj and not is_player_bj:
                current_profit -= bet
                losses += 1
            elif is_player_bj and is_dealer_bj:
                draws += 1
            elif d_total > 21 or p_total > d_total:
                current_profit += bet
                wins += 1
            elif p_total < d_total:
                current_profit -= bet
                losses += 1
            else:
                draws += 1
        profit_history.append(current_profit)
    return profit_history, wins, losses, draws, total_bet_money

def run_counting_practice_loop(speed_seconds):
    """10ゲーム分の自動プレイを時間差で実行し、画面を動的に更新する"""
    status_area = st.empty()
    dealer_area = st.empty()
    player_area = st.empty()
    action_area = st.empty()
    all_seen_cards = []
    
    def render_hands(cards, highlight_last=False):
        rendered = []
        for i, c in enumerate(cards):
            if highlight_last and i == len(cards) - 1:
                rendered.append(f"<span style='color: #FF4B4B; font-weight: bold; font-size: 1.25rem; border: 2px solid #FF4B4B; padding: 2px 6px; border-radius: 4px; margin: 0 4px;'>[ {c} ]</span>")
            else:
                rendered.append(f"<span style='color: #31333F; font-weight: bold; font-size: 1.25rem; border: 2px solid #D3D3D3; padding: 2px 6px; border-radius: 4px; margin: 0 4px;'>[ {c} ]</span>")
        return " ".join(rendered)

    for game_num in range(1, 11):
        status_area.markdown(f"### 🔄 カウンティング特訓中: {game_num} / 10 ゲーム目")
        dealer_hand = [draw_card(), draw_card()]
        dealer_up = dealer_hand[0]
        all_seen_cards.extend(dealer_hand)
        
        dealer_area.markdown(f"**ディーラーのアップカード:** {render_hands([dealer_up])} <span style='color: #777; font-size: 1.25rem; margin-left: 4px;'>[ ? ]</span>", unsafe_allow_html=True)
        player_area.empty()
        action_area.empty()
        time.sleep(speed_seconds)
        
        d_total_init = calculate_total(dealer_hand)
        is_dealer_bj = (len(dealer_hand) == 2 and d_total_init == 21)
        player_hands = [[draw_card(), draw_card()]]
        all_seen_cards.extend(player_hands[0])
        
        p_total = calculate_total(player_hands[0])
        player_area.markdown(f"**あなたの手札 (手札1):** {render_hands(player_hands[0], highlight_last=True)} (合計: {p_total})", unsafe_allow_html=True)
        time.sleep(speed_seconds)
        
        if not is_dealer_bj:
            hand_idx = 0
            while hand_idx < len(player_hands):
                current_hand = player_hands[hand_idx]
                while True:
                    action = get_correct_action(current_hand, dealer_up)
                    action_names = {"H": "ヒット", "S": "スタンド", "D": "ダブルダウン", "P": "スプリット", "R": "サレンダー"}
                    
                    if len(player_hands) > 1:
                        action_area.info(f"手札 {hand_idx+1} を操作中 ➡ AIの選択: **{action_names.get(action, action)}**")
                    else:
                        action_area.info(f"AIの選択: **{action_names.get(action, action)}**")
                    time.sleep(speed_seconds)
                    
                    if action == "H":
                        new_card = draw_card()
                        current_hand.append(new_card)
                        all_seen_cards.append(new_card)
                        
                        lines = []
                        for i, h in enumerate(player_hands):
                            is_current = (i == hand_idx)
                            lines.append(f"**{'👉 ' if is_current and len(player_hands) > 1 else ''}あなたの手札 (手札{i+1}):** {render_hands(h, highlight_last=is_current)} (合計: {calculate_total(h)})")
                        player_area.markdown("<br>".join(lines), unsafe_allow_html=True)
                        time.sleep(speed_seconds)
                        if calculate_total(current_hand) > 21:
                            action_area.error(f"手札 {hand_idx+1} がバースト！")
                            time.sleep(speed_seconds)
                            break
                    elif action == "S":
                        lines = [f"**あなたの手札 (手札{i+1}):** {render_hands(h, highlight_last=False)} (合計: {calculate_total(h)})" for i, h in enumerate(player_hands)]
                        player_area.markdown("<br>".join(lines), unsafe_allow_html=True)
                        break
                    elif action == "D":
                        new_card = draw_card()
                        current_hand.append(new_card)
                        all_seen_cards.append(new_card)
                        lines = []
                        for i, h in enumerate(player_hands):
                            is_current = (i == hand_idx)
                            lines.append(f"**{'👉 ' if is_current and len(player_hands) > 1 else ''}あなたの手札 (手札{i+1}):** {render_hands(h, highlight_last=is_current)} (合計: {calculate_total(h)})")
                        player_area.markdown("<br>".join(lines), unsafe_allow_html=True)
                        time.sleep(speed_seconds)
                        break
                    elif action == "R":
                        action_area.warning(f"手札 {hand_idx+1} はサレンダー（降伏）しました。")
                        time.sleep(speed_seconds)
                        break
                    elif action == "P":
                        card1, card2 = current_hand[0], current_hand[1]
                        player_hands.pop(hand_idx)
                        nc1, nc2 = draw_card(), draw_card()
                        all_seen_cards.extend([nc1, nc2])
                        player_hands.insert(hand_idx, [card2, nc2])
                        player_hands.insert(hand_idx, [card1, nc1])
                        current_hand = player_hands[hand_idx]
                        
                        lines = []
                        for i, h in enumerate(player_hands):
                            lines.append(f"**{'👉 ' if i == hand_idx else ''}あなたの手札 (手札{i+1}):** {render_hands(h, highlight_last=(i == hand_idx))} (合計: {calculate_total(h)})")
                        player_area.markdown("<br>".join(lines), unsafe_allow_html=True)
                        time.sleep(speed_seconds)
                hand_idx += 1
                
        all_busted = all(calculate_total(h) > 21 for h in player_hands)
        if not is_dealer_bj and not all_busted:
            dealer_area.markdown(f"**ディーラーの手札:** {render_hands(dealer_hand, highlight_last=True)} (合計: {calculate_total(dealer_hand)})", unsafe_allow_html=True)
            time.sleep(speed_seconds)
            while calculate_total(dealer_hand) < 17:
                new_card = draw_card()
                dealer_hand.append(new_card)
                all_seen_cards.append(new_card)
                dealer_area.markdown(f"**ディーラーの手札:** {render_hands(dealer_hand, highlight_last=True)} (合計: {calculate_total(dealer_hand)})", unsafe_allow_html=True)
                time.sleep(speed_seconds)
        
        d_total = calculate_total(dealer_hand)
        dealer_area.markdown(f"**ディーラーの最終手札:** {render_hands(dealer_hand, highlight_last=False)} (合計: {d_total})", unsafe_allow_html=True)
        time.sleep(speed_seconds)
        action_area.success("ゲーム終了。次のゲームへ移ります...")
        time.sleep(speed_seconds * 1.5)
        
    status_area.empty()
    dealer_area.empty()
    player_area.empty()
    action_area.empty()
    return all_seen_cards

def render_simulation_page():
    """高速自動シミュレーション画面の描画"""
    st.header("期待値検証・高速全自動プレイ")
    st.write("ベーシックストラテジーに100%従って、AIが指定回数分ノンストップで自動プレイします。")
    
    
    sim_games = st.selectbox(
        "試行回数を選択してください", [1000, 5000, 10000, 30000, 50000], index=2,
        format_func=lambda x: f"{x:,} 回プレイ"
    )
    
    if st.button("シミュレーションを開始", type="primary", use_container_width=True):
        with st.spinner("シミュレーション中..."):
            history, w, l, d, total_bet = run_blackjack_simulation(sim_games)
            
        final_profit = history[-1]
        payout_rate = ((total_bet + final_profit) / total_bet) * 100
        
        st.subheader("シミュレーション結果")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("最終損益", f"{final_profit:,} 円", delta=f"{final_profit:,} 円" if final_profit >= 0 else f"{final_profit:,} 円")
        with col2: st.metric("実際の回収率 (RTP)", f"{payout_rate:.2f} %")
        with col3: st.metric("理論期待値との差", f"{payout_rate - 99.50:+.2f} %")
            
        st.text(f"勝敗内訳: {w}勝 / {l}敗 / {d}引き分け (総ベット額: {total_bet:,}円、基本ベット額: {BET_AMOUNT:,}円)")
        
        
        
        chart_data = pd.DataFrame({"ゲーム回数": list(range(len(history))), "通算収支（円）": history}).set_index("ゲーム回数")
        st.line_chart(chart_data)

def render_counting_page():
    """カウンティング特訓画面の描画"""
    st.header("カウンティング実戦特訓（バックカウンティング）")
    st.write("AIがストラテジー通りに自動プレイする様子をじっくり観察し、場に出たすべてのカードからランニングカウントを暗算してください。")
    
    speed_mode = st.radio(
        "⏱️ 進行スピードを選択してください", ["低速（ゆっくり確認: 2.0秒）", "中速（実戦テンポ: 1.0秒）", "高速（プロレベル反射: 0.4秒）"], horizontal=True, index=1
    )
    speed_map = {"低速（ゆっくり確認: 2.0秒）": 2.0, "中速（実戦テンポ: 1.0秒）": 1.0, "高速（プロレベル反射: 0.4秒）": 0.4}
    current_speed = speed_map[speed_mode]
    
    if "counting_cards" not in st.session_state: st.session_state.counting_cards = None
    if "counting_active" not in st.session_state: st.session_state.counting_active = False

    if not st.session_state.counting_active and st.session_state.counting_cards is None:
        if st.button("特訓（10ゲーム連続）を開始する", type="primary", use_container_width=True):
            st.session_state.counting_active = True
            st.rerun()

    if st.session_state.counting_active:
        cards_log = run_counting_practice_loop(current_speed)
        st.session_state.counting_cards = cards_log
        st.session_state.counting_active = False
        st.rerun()

    if st.session_state.counting_cards is not None:
        st.success("🏁 10ゲームの観戦が終了しました！頭の中のカウントを解答してください。")
        cards_list = st.session_state.counting_cards
        correct_count = sum(1 if c in ['2','3','4','5','6'] else -1 if c in ['10','J','Q','K','A'] else 0 for c in cards_list)
        low_cards = sum(1 for c in cards_list if c in ['2','3','4','5','6'])
        high_cards = sum(1 for c in cards_list if c in ['10','J','Q','K','A'])
        neutral_cards = len(cards_list) - low_cards - high_cards

        with st.form("counting_answer_form"):
            user_ans = st.number_input("🔢 あなたが数えた【ランニングカウント】の最終数値：", value=0, step=1)
            if st.form_submit_button("🟢 答え合わせをする", type="primary"):
                st.write("---")
                if user_ans == correct_count:
                    st.balloons()
                    st.success(f"🎉 素晴らしい！正解です！ 正解のカウントは **{correct_count}** でした！")
                else:
                    st.error(f"❌ 惜しい！ 計算がズレていたようです。 正解のカウントは **{correct_count}** でした（あなたの回答: {user_ans}）")
                
                st.subheader("📊 出現したカードの統計・内訳")
                st.text(f"総出現枚数: {len(cards_list)} 枚")
                col1, col2, col3 = st.columns(3)
                with col1: st.metric("小カード (2～6) [ ＋1 ]", f"{low_cards} 枚")
                with col2: st.metric("中立カード (7～9) [ 0 ]", f"{neutral_cards} 枚")
                with col3: st.metric("大カード (10～A) [ －1 ]", f"{high_cards} 枚")

        if st.button("🔄 もう一度特訓する", use_container_width=True):
            st.session_state.counting_cards = None
            st.rerun()