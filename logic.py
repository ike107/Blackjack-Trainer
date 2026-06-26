# logic.py
import random
from config import CARD_VALUES

def draw_card():
    """山札からランダムに1枚カードを引く"""
    return random.choice(list(CARD_VALUES.keys()))

def calculate_total(cards):
    """手札の合計値を計算する（Aの調整を含む）"""
    total = sum(CARD_VALUES[c] for c in cards)
    ace_count = cards.count('A')
    while total > 21 and ace_count > 0:
        total -= 10
        ace_count -= 1
    return total

def generate_hard_mode_hand():
    """特訓モード用の手札（難問・ペア・ソフトハンド）を生成"""
    while True:
        c1, c2 = draw_card(), draw_card()
        cards = [c1, c2]
        total = calculate_total(cards)
        if c1 == c2 and c1 in ['9', '7', '6', '4']: 
            return cards
        if c1 == c2: 
            continue
        if 'A' in cards:
            if total < 19: 
                return cards
            continue

def get_correct_action(player_cards, dealer_up_card):
    """MBS公式ルール（制限なしダブル、A以外サレンダーあり）に基づく正解アクション"""
    d_val = CARD_VALUES[dealer_up_card]
    values = [CARD_VALUES[c] for c in player_cards]
    total = sum(values)
    ace_count = player_cards.count('A')
    
    while total > 21 and ace_count > 0:
        total -= 10
        ace_count -= 1


    # 1. ペアハンド（スプリット）の判定
    if len(player_cards) == 2 and player_cards[0] == player_cards[1]:
        p_card = player_cards[0]
        if p_card in ['A', '8']: return 'P'
        elif p_card in ['10', 'J', 'Q', 'K']: return 'S'
        elif p_card == '9': return 'S' if d_val in [7, 10, 11] else 'P'
        elif p_card == '7': return 'P' if d_val <= 7 else 'H'
        elif p_card == '6': return 'P' if d_val <= 6 else 'H'
        elif p_card == '5': return 'D' if d_val <= 9 else 'H'
        elif p_card == '4': return 'P' if 5 <= d_val <= 6 else 'H'
        elif p_card in ['2', '3']: return 'P' if d_val <= 7 else 'H'


    # 2.【サレンダー判定】最初の手札2枚、かつディーラーがA以外の時のみ
    if len(player_cards) == 2 and dealer_up_card != 'A':
        if ace_count == 0:
            if total == 16 and dealer_up_card in ['9', '10', 'J', 'Q', 'K']:
                return 'R'
            if total == 15 and dealer_up_card in ['10', 'J', 'Q', 'K']:
                return 'R'

  

    # 3. ソフトハンドの判定
    if ace_count > 0 and total <= 21:
        other_total = total - 11
        if other_total >= 8: return 'S'
        elif other_total == 7: 
            if 3 <= d_val <= 6 and len(player_cards) == 2: return 'D'
            return 'S' if d_val <= 8 else 'H'
        elif other_total == 6:
            return 'D' if (3 <= d_val <= 6 and len(player_cards) == 2) else 'H'
        elif other_total in [4, 5]:
            return 'D' if (4 <= d_val <= 6 and len(player_cards) == 2) else 'H'
        elif other_total in [2, 3]:
            return 'D' if (5 <= d_val <= 6 and len(player_cards) == 2) else 'H'

    # 4. ハードハンドの判定
    if total >= 17: return 'S'
    elif total in [13, 14, 15, 16]: return 'S' if d_val <= 6 else 'H'
    elif total == 12: return 'S' if 4 <= d_val <= 6 else 'H'
    elif total == 11: 
        return 'D' if len(player_cards) == 2 else 'H'
    elif total == 10: 
        if d_val <= 9: return 'D' if len(player_cards) == 2 else 'H'
        return 'H'
    elif total == 9: 
        if 3 <= d_val <= 6: return 'D' if len(player_cards) == 2 else 'H'
        return 'H'
    else: 
        return 'H'
