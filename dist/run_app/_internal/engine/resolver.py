# engine/resolver.py
from data.hunter_cards import CARD_DB
from engine.state_ops import (
    add_block,
    add_damage,
    add_poison,
    add_card_to_hand,
    discard_all_hand,
    discard_left_n,
    draw_n,
    move_after_play,
)


# =========================
# metadata 默认值
# =========================
def ensure_metadata_defaults(state):
    md = state.metadata

    if "enemy_poison" not in md:
        md["enemy_poison"] = 0

    if "discarded_this_turn" not in md:
        md["discarded_this_turn"] = 0

    if "cards_played_this_turn" not in md:
        md["cards_played_this_turn"] = 0

    if "attacks_played_this_turn" not in md:
        md["attacks_played_this_turn"] = 0

    if "skills_played_this_turn" not in md:
        md["skills_played_this_turn"] = 0

    # 腐蚀波：本回合每抽1张牌，上若干层毒
    if "poison_on_draw_this_turn" not in md:
        md["poison_on_draw_this_turn"] = 0

    # 余像：每打1张牌获得格挡
    if "on_play_gain_block" not in md:
        md["on_play_gain_block"] = 0

    # 小刀伤害加成（精准）
    if "shiv_damage_bonus" not in md:
        md["shiv_damage_bonus"] = 0

    # 本回合第一张小刀额外伤害（幻影之刃）
    if "first_shiv_bonus_damage_each_turn" not in md:
        md["first_shiv_bonus_damage_each_turn"] = 0

    if "first_shiv_used_this_turn" not in md:
        md["first_shiv_used_this_turn"] = False

    # 小刀是否视为 AOE
    if "shivs_are_aoe" not in md:
        md["shivs_are_aoe"] = False

    # 爆发：接下来技能额外结算次数
    if "next_skill_extra_plays" not in md:
        md["next_skill_extra_plays"] = 0

    # 子弹时间 / 免费牌类，先预留
    if "free_all_hand_this_turn" not in md:
        md["free_all_hand_this_turn"] = False

    if "free_attack_cost_this_turn" not in md:
        md["free_attack_cost_this_turn"] = False

    if "free_skill_cost_this_turn" not in md:
        md["free_skill_cost_this_turn"] = False


# =========================
# 基础判定
# =========================
def can_play(state, card_name: str, free_to_play: bool = False) -> bool:
    ensure_metadata_defaults(state)
    card = CARD_DB[card_name]
    md = state.metadata

    if free_to_play:
        return True

    # 华丽收场：只有抽牌堆为空时才能打
    if card.extra.get("require_empty_draw_pile", False):
        if len(state.draw_pile) != 0:
            return False

    if md["free_all_hand_this_turn"]:
        return True

    if card.card_type == "attack" and md["free_attack_cost_this_turn"]:
        return True

    if card.card_type == "skill" and md["free_skill_cost_this_turn"]:
        return True

    if card.extra.get("x_cost", False):
        return state.energy >= 0

    return state.energy >= card.cost


def spend_energy(state, card_name: str):
    ensure_metadata_defaults(state)
    card = CARD_DB[card_name]
    md = state.metadata

    if md["free_all_hand_this_turn"]:
        return 0

    if card.card_type == "attack" and md["free_attack_cost_this_turn"]:
        return 0

    if card.card_type == "skill" and md["free_skill_cost_this_turn"]:
        return 0

    if card.extra.get("x_cost", False):
        spent = state.energy
        state.energy = 0
        return spent

    state.energy -= card.cost
    return card.cost


# =========================
# 抽牌触发
# =========================
def draw_cards_with_triggers(state, n: int):
    """
    带抽牌触发的抽牌：
    - 腐蚀波：每抽1张牌，上毒
    """
    ensure_metadata_defaults(state)
    md = state.metadata

    drawn = draw_n(state, n)

    if md["poison_on_draw_this_turn"] > 0:
        poison_each = md["poison_on_draw_this_turn"]
        for _ in drawn:
            add_poison(state, poison_each)

    return drawn


# =========================
# 伤害计算
# =========================
def compute_card_damage(state, card_name: str):
    ensure_metadata_defaults(state)
    card = CARD_DB[card_name]
    md = state.metadata

    dmg = card.damage + state.strength

    # 精准：小刀额外伤害
    if card_name.startswith("小刀"):
        dmg += md["shiv_damage_bonus"]

        if not md["first_shiv_used_this_turn"]:
            dmg += md["first_shiv_bonus_damage_each_turn"]
            md["first_shiv_used_this_turn"] = True

    # 每手牌 -2 这类特效预留
    if card.extra.get("minus_2_per_hand_card", False):
        dmg -= 2 * len(state.hand)

    # 本回合每弃1张牌 +X 伤害
    if card.extra.get("bonus_from_discards_this_turn", False):
        discarded = state.metadata.get("discarded_this_turn", 0)
        dmg += discarded * card.extra.get("discard_bonus_value", 0)

    return max(0, dmg)


# =========================
# 三类牌效果
# =========================
def resolve_attack_effect(state, card_name: str):
    ensure_metadata_defaults(state)
    card = CARD_DB[card_name]
    extra = card.extra or {}

    dmg = compute_card_damage(state, card_name)
    multi_hit = max(1, int(extra.get("multi_hit", 1)))

    # 当前版本不精细区分单体/群体敌人数，统一累计为有效输出
    add_damage(state, dmg * multi_hit)

    # 攻击牌自带抽牌
    if card.draw > 0:
        draw_cards_with_triggers(state, card.draw)

    # 攻击牌自带格挡
    if card.block > 0:
        add_block(state, card.block)

    # 攻击牌自带中毒
    if card.poison > 0:
        add_poison(state, card.poison)

    # 生成小刀
    if extra.get("add_shiv", 0) > 0:
        add_card_to_hand(state, "小刀", extra.get("add_shiv", 0))


def resolve_skill_effect_once(state, card_name: str):
    """
    单次技能结算。
    如果有“爆发”之类，会在外层重复调用这个函数。
    """
    ensure_metadata_defaults(state)
    card = CARD_DB[card_name]
    extra = card.extra or {}

    # 基础数值
    if card.block > 0:
        add_block(state, card.block)

    if card.draw > 0:
        draw_cards_with_triggers(state, card.draw)

    if card.energy_gain > 0:
        state.energy += card.energy_gain

    if card.poison > 0:
        add_poison(state, card.poison)

    if card.shiv > 0:
        add_card_to_hand(state, "小刀", card.shiv)

    if card.discard > 0:
        discard_left_n(state, card.discard, play_card)

    # ===== 指定牌效果 =====

    # 杂技 / 杂技+
    if extra.get("draw_then_discard", False):
        draw_cards_with_triggers(state, extra.get("draw_count", 0))
        discard_left_n(state, extra.get("discard_count", 0), play_card)
        return

    # 早有准备 / 早有准备+
    if extra.get("draw_then_discard_same", False):
        draw_cards_with_triggers(state, extra.get("draw_count", 0))
        discard_left_n(state, extra.get("discard_count", 0), play_card)
        return

    # 后空翻 / 后空翻+
    if extra.get("block_then_draw", False):
        add_block(state, extra.get("block_value", 0))
        draw_cards_with_triggers(state, extra.get("draw_count", 0))
        return

    # 斗篷与匕首
    if extra.get("gain_block_and_add_shiv", False):
        add_block(state, extra.get("block_value", 0))
        add_card_to_hand(state, "小刀", extra.get("shiv_count", 0))
        return

    # 刀刃之舞
    if extra.get("add_many_shivs", False):
        add_card_to_hand(state, "小刀", extra.get("shiv_count", 0))
        return

    # 生存者：获得格挡，弃1
    if extra.get("block_then_discard", False):
        add_block(state, extra.get("block_value", 0))
        discard_left_n(state, extra.get("discard_count", 1), play_card)
        return

    # 计算下注：弃所有手牌，再抽相同数量
    if extra.get("calculated_gamble", False):
        count = len(state.hand)
        discard_all_hand(state, play_card)
        draw_cards_with_triggers(state, count)
        return

    # 钢铁风暴：弃所有手牌，每弃1张加1张小刀
    if extra.get("storm_of_steel", False):
        count = len(state.hand)
        discard_all_hand(state, play_card)
        add_card_to_hand(state, "小刀", count)
        return

    # 暗影步：当前版本只处理“弃所有手牌”
    if extra.get("discard_all_hand", False):
        discard_all_hand(state, play_card)
        return

    # 腐蚀波：本回合每抽1张牌，上毒
    if extra.get("poison_on_draw_this_turn", 0) > 0:
        state.metadata["poison_on_draw_this_turn"] += extra.get("poison_on_draw_this_turn", 0)
        return

    # 爆发：接下来技能额外结算
    if extra.get("next_skill_extra_plays", 0) > 0:
        state.metadata["next_skill_extra_plays"] += extra.get("next_skill_extra_plays", 0)
        return

    # 蜃景：获得等同于敌方中毒层数的格挡
    if extra.get("gain_block_equal_enemy_poison", False):
        add_block(state, state.metadata.get("enemy_poison", 0))
        return

    # 对所有敌人施毒
    if extra.get("apply_poison_all", 0) > 0:
        add_poison(state, extra.get("apply_poison_all", 0))
        return


def resolve_skill_effect(state, card_name: str):
    """
    技能牌总入口。
    支持“爆发”使技能额外再结算若干次。
    """
    ensure_metadata_defaults(state)
    extra_plays = state.metadata.get("next_skill_extra_plays", 0)

    # 先正常结算一次
    resolve_skill_effect_once(state, card_name)

    # 再追加额外结算
    if extra_plays > 0:
        for _ in range(extra_plays):
            resolve_skill_effect_once(state, card_name)
        state.metadata["next_skill_extra_plays"] = 0


def resolve_power_effect(state, card_name: str):
    ensure_metadata_defaults(state)
    extra = CARD_DB[card_name].extra or {}

    # 余像：每打1张牌获得格挡
    if extra.get("on_play_gain_block", 0) > 0:
        state.metadata["on_play_gain_block"] += extra.get("on_play_gain_block", 0)

    # 精准：小刀伤害增加
    if extra.get("shiv_damage_bonus", 0) > 0:
        state.metadata["shiv_damage_bonus"] += extra.get("shiv_damage_bonus", 0)

    # 幻影之刃：第一张小刀额外伤害
    if extra.get("first_shiv_bonus_damage_each_turn", 0) > 0:
        state.metadata["first_shiv_bonus_damage_each_turn"] += extra.get("first_shiv_bonus_damage_each_turn", 0)

    # 小刀变 AOE
    if extra.get("shivs_are_aoe", False):
        state.metadata["shivs_are_aoe"] = True


def resolve_card_effect(state, card_name: str):
    card = CARD_DB[card_name]

    if card.card_type == "attack":
        resolve_attack_effect(state, card_name)
    elif card.card_type == "skill":
        resolve_skill_effect(state, card_name)
    elif card.card_type == "power":
        resolve_power_effect(state, card_name)


# =========================
# 任意牌打出后的通用触发
# =========================
def after_any_card_play(state, card_name: str):
    ensure_metadata_defaults(state)
    card = CARD_DB[card_name]

    state.metadata["cards_played_this_turn"] += 1
    if card.card_type == "attack":
        state.metadata["attacks_played_this_turn"] += 1
    elif card.card_type == "skill":
        state.metadata["skills_played_this_turn"] += 1

    # 余像：每打1张牌获得格挡
    if state.metadata["on_play_gain_block"] > 0:
        add_block(state, state.metadata["on_play_gain_block"])


# =========================
# 统一打牌入口
# =========================
def play_card(state, card_name: str, free_to_play: bool = False, from_discard_trigger: bool = False):
    """
    统一打牌入口：
    - 正常从手牌打出
    - 或奇巧从弃牌触发免费打出
    """
    ensure_metadata_defaults(state)

    if card_name not in CARD_DB:
        return False

    # 正常从手牌打出
    if not from_discard_trigger:
        if card_name not in state.hand:
            return False
        if not can_play(state, card_name, free_to_play=free_to_play):
            return False

        state.hand.remove(card_name)

        if not free_to_play:
            spend_energy(state, card_name)

    # 奇巧从弃牌触发
    else:
        if not can_play(state, card_name, free_to_play=True):
            return False

    # 记录历史
    state.history.append(card_name)

    # 结算牌效果
    resolve_card_effect(state, card_name)

    # 通用触发
    after_any_card_play(state, card_name)

    # 打出后去向
    move_after_play(state, card_name)

    return True