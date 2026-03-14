# engine/state_ops.py
import random
from copy import deepcopy
from typing import Iterable
from data.hunter_cards import CARD_DB


def clone_state(state):
    return deepcopy(state)


def shuffle_discard_into_draw(state):
    """
    当抽牌堆为空时，把弃牌堆随机洗入抽牌堆。
    注意：
    - exhaust_pile 不能回洗
    - powers_played 不能回洗
    """
    if not state.discard_pile:
        return False

    new_draw = list(state.discard_pile)
    random.shuffle(new_draw)
    state.draw_pile = new_draw
    state.discard_pile.clear()
    return True


def draw_one(state):
    """
    抽 1 张牌。
    若 draw_pile 为空，则随机洗弃牌堆回抽牌堆。
    """
    if not state.draw_pile:
        ok = shuffle_discard_into_draw(state)
        if not ok:
            return None

    if not state.draw_pile:
        return None

    card_name = state.draw_pile.pop(0)
    state.hand.append(card_name)
    return card_name


def draw_n(state, n: int):
    """
    连续抽 n 张牌，返回实际抽到的牌列表
    """
    drawn = []
    for _ in range(max(0, n)):
        card_name = draw_one(state)
        if card_name is None:
            break
        drawn.append(card_name)
    return drawn


def move_after_play(state, card_name: str):
    """
    统一处理打出后的去向：
    1) 能力牌 -> powers_played
    2) 消耗牌 -> exhaust_pile
    3) 普通牌 -> discard_pile
    """
    card = CARD_DB[card_name]

    if card.is_power:
        state.powers_played.append(card_name)
        return

    if card.exhaust:
        state.exhaust_pile.append(card_name)
        return

    state.discard_pile.append(card_name)


def add_damage(state, amount: int):
    """
    增加直接伤害统计
    """
    amount = max(0, int(amount))
    if amount <= 0:
        return
    state.total_damage += amount


def add_block(state, amount: int):
    """
    增加格挡，并计入格挡统计
    """
    amount = max(0, int(amount))
    if amount <= 0:
        return
    state.block += amount
    state.total_block_gained += amount


def add_poison(state, amount: int):
    """
    增加中毒统计。
    这里不做敌人数精确模拟，先作为“有效输出资源”累计。
    """
    amount = max(0, int(amount))
    if amount <= 0:
        return

    state.total_poison_added += amount

    if "enemy_poison" not in state.metadata:
        state.metadata["enemy_poison"] = 0
    state.metadata["enemy_poison"] += amount


def discard_card(state, card_name: str, resolver_play_card):
    """
    从手牌弃掉一张牌，并处理：
    1) 从手牌移除
    2) 放入弃牌堆
    3) 触发弃牌效果
    4) 若是奇巧牌，则自动从弃牌堆打出
    """
    if card_name not in state.hand:
        return False

    state.hand.remove(card_name)
    card = CARD_DB[card_name]

    # 先进弃牌堆
    state.discard_pile.append(card_name)

    # 统计本回合弃牌数
    state.metadata["discarded_this_turn"] = state.metadata.get("discarded_this_turn", 0) + 1

    # 弃牌触发：抽牌
    if card.draw_on_discard > 0:
        draw_n(state, card.draw_on_discard)

    # 弃牌触发：回能
    if card.energy_on_discard > 0:
        state.energy += card.energy_on_discard

    # 奇巧：弃牌后自动打出
    if card.play_on_discard:
        auto_play_from_discard(state, card_name, resolver_play_card)

    return True


def discard_many(state, card_names: Iterable[str], resolver_play_card):
    """
    顺序弃多张牌
    """
    for name in list(card_names):
        if name in state.hand:
            discard_card(state, name, resolver_play_card)


def discard_left_n(state, n: int, resolver_play_card):
    """
    简化策略：默认从手牌左侧开始弃 n 张
    """
    if n <= 0:
        return
    to_discard = list(state.hand[:n])
    discard_many(state, to_discard, resolver_play_card)


def discard_all_hand(state, resolver_play_card):
    """
    弃掉当前所有手牌
    """
    to_discard = list(state.hand)
    discard_many(state, to_discard, resolver_play_card)


def auto_play_from_discard(state, card_name: str, resolver_play_card):
    """
    奇巧自动打出：
    1) 从 discard_pile 移除
    2) 免费打出
    """
    if card_name in state.discard_pile:
        state.discard_pile.remove(card_name)

    resolver_play_card(
        state=state,
        card_name=card_name,
        free_to_play=True,
        from_discard_trigger=True
    )


def add_card_to_hand(state, card_name: str, count: int = 1):
    for _ in range(max(0, count)):
        state.hand.append(card_name)


def add_card_to_draw_pile(state, card_name: str, count: int = 1):
    for _ in range(max(0, count)):
        state.draw_pile.append(card_name)


def add_card_to_discard(state, card_name: str, count: int = 1):
    for _ in range(max(0, count)):
        state.discard_pile.append(card_name)


def add_card_to_exhaust(state, card_name: str, count: int = 1):
    for _ in range(max(0, count)):
        state.exhaust_pile.append(card_name)


def count_in_all_zones(state, card_name: str):
    """
    调试用：统计某张牌在各区域出现次数
    """
    return {
        "hand": state.hand.count(card_name),
        "draw_pile": state.draw_pile.count(card_name),
        "discard_pile": state.discard_pile.count(card_name),
        "exhaust_pile": state.exhaust_pile.count(card_name),
        "powers_played": state.powers_played.count(card_name),
    }


def remove_one_from_zone(cards, card_name: str):
    """
    从某个列表区域移除 1 张指定牌，若不存在则返回 False
    """
    if card_name in cards:
        cards.remove(card_name)
        return True
    return False