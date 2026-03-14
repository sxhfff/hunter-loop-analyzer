# data/hunter_cards.py
from engine.types import CardDef


def C(
    name,
    cost,
    card_type,
    damage=0,
    block=0,
    draw=0,
    discard=0,
    energy_gain=0,
    weak=0,
    vulnerable=0,
    poison=0,
    shiv=0,
    innate=False,
    token=False,
    retain=False,
    is_power=False,
    exhaust=False,
    play_on_discard=False,
    draw_on_discard=0,
    energy_on_discard=0,
    auto_play_no_energy=True,
    turn_start_draw=0,
    turn_start_discard=0,
    turn_start_block=0,
    turn_start_poison_all=0,
    turn_start_add_shiv=0,
    extra=None,
):
    return CardDef(
        id=name,
        name=name,
        cost=cost,
        card_type=card_type,
        damage=damage,
        block=block,
        draw=draw,
        discard=discard,
        energy_gain=energy_gain,
        weak=weak,
        vulnerable=vulnerable,
        poison=poison,
        shiv=shiv,
        innate=innate,
        token=token,
        retain=retain,
        is_power=is_power,
        exhaust=exhaust,
        play_on_discard=play_on_discard,
        draw_on_discard=draw_on_discard,
        energy_on_discard=energy_on_discard,
        auto_play_no_energy=auto_play_no_energy,
        turn_start_draw=turn_start_draw,
        turn_start_discard=turn_start_discard,
        turn_start_block=turn_start_block,
        turn_start_poison_all=turn_start_poison_all,
        turn_start_add_shiv=turn_start_add_shiv,
        extra=extra or {},
    )


# =========================
# 模板牌（非循环关键牌统一模板）
# =========================
TEMPLATE_CARDS = {
    # 攻击模板
    "0费攻击": C("0费攻击", 0, "attack", damage=5),
    "1费攻击": C("1费攻击", 1, "attack", damage=8),
    "2费攻击": C("2费攻击", 2, "attack", damage=12),

    # 防御模板
    "0费防御": C("0费防御", 0, "skill", block=4, extra={"simple_block": True}),
    "1费防御": C("1费防御", 1, "skill", block=7, extra={"simple_block": True}),
    "2费防御": C("2费防御", 2, "skill", block=11, extra={"simple_block": True}),

    # 能力模板
    "1费能力": C("1费能力", 1, "power", is_power=True),
    "2费能力": C("2费能力", 2, "power", is_power=True),
    "3费能力": C("3费能力", 3, "power", is_power=True),
}


# =========================
# Token
# =========================
TOKEN_CARDS = {
    "小刀": C(
        "小刀",
        0,
        "attack",
        damage=4,
        token=True,
        exhaust=True
    ),
    "小刀+": C(
        "小刀+",
        0,
        "attack",
        damage=6,
        token=True,
        exhaust=True
    ),
}


# =========================
# 循环关键牌 / 机制牌
# =========================
CORE_CARDS = {
    # ===== 抽牌 / 弃牌核心 =====
    "杂技": C(
        "杂技",
        1,
        "skill",
        extra={"draw_then_discard": True, "draw_count": 3, "discard_count": 1}
    ),
    "杂技+": C(
        "杂技+",
        1,
        "skill",
        extra={"draw_then_discard": True, "draw_count": 4, "discard_count": 1}
    ),

    "早有准备": C(
        "早有准备",
        0,
        "skill",
        extra={"draw_then_discard_same": True, "draw_count": 2, "discard_count": 2}
    ),
    "早有准备+": C(
        "早有准备+",
        0,
        "skill",
        extra={"draw_then_discard_same": True, "draw_count": 3, "discard_count": 2}
    ),

    "后空翻": C(
        "后空翻",
        1,
        "skill",
        extra={"block_then_draw": True, "block_value": 5, "draw_count": 2}
    ),
    "后空翻+": C(
        "后空翻+",
        1,
        "skill",
        extra={"block_then_draw": True, "block_value": 8, "draw_count": 2}
    ),

    "生存者": C(
        "生存者",
        1,
        "skill",
        extra={"block_then_discard": True, "block_value": 8, "discard_count": 1}
    ),
    "生存者+": C(
        "生存者+",
        1,
        "skill",
        extra={"block_then_discard": True, "block_value": 11, "discard_count": 1}
    ),

    "独门绝技": C(
        "独门绝技",
        1,
        "skill",
        draw=6
    ),
    "独门绝技+": C(
        "独门绝技+",
        0,
        "skill",
        draw=6
    ),

    # ===== 奇巧牌 =====
    "本能反应": C(
        "本能反应",
        3,
        "skill",
        play_on_discard=True,
        draw_on_discard=2
    ),
    "本能反应+": C(
        "本能反应+",
        3,
        "skill",
        play_on_discard=True,
        draw_on_discard=3
    ),

    "战术大师": C(
        "战术大师",
        3,
        "skill",
        play_on_discard=True,
        energy_on_discard=1
    ),
    "战术大师+": C(
        "战术大师+",
        3,
        "skill",
        play_on_discard=True,
        energy_on_discard=2
    ),

    "迷雾": C(
        "迷雾",
        3,
        "skill",
        play_on_discard=True,
        extra={"apply_poison_all": 4}
    ),
    "迷雾+": C(
        "迷雾+",
        3,
        "skill",
        play_on_discard=True,
        extra={"apply_poison_all": 6}
    ),

    "毒雾": C(
        "毒雾",
        1,
        "power",
        is_power=True,
        extra={"apply_poison_all": 2}
    ),
    "毒雾+": C(
        "毒雾+",
        1,
        "power",
        is_power=True,
        extra={"apply_poison_all": 3}
    ),

    "触不可及": C(
        "触不可及",
        2,
        "skill",
        play_on_discard=True,
        block=9
    ),
    "触不可及+": C(
        "触不可及+",
        2,
        "skill",
        play_on_discard=True,
        block=12
    ),

    "翻越撑击": C(
        "翻越撑击",
        1,
        "attack",
        damage=7,
        play_on_discard=True,
        extra={"aoe": True}
    ),
    "翻越撑击+": C(
        "翻越撑击+",
        1,
        "attack",
        damage=9,
        play_on_discard=True,
        extra={"aoe": True}
    ),

    "连续反弹": C(
        "连续反弹",
        2,
        "attack",
        damage=3,
        play_on_discard=True,
        extra={"multi_hit": 4}
    ),
    "连续反弹+": C(
        "连续反弹+",
        2,
        "attack",
        damage=3,
        play_on_discard=True,
        extra={"multi_hit": 5}
    ),

    # ===== 小刀体系 =====
    "刀刃之舞": C(
        "刀刃之舞",
        1,
        "skill",
        extra={"add_many_shivs": True, "shiv_count": 3}
    ),
    "刀刃之舞+": C(
        "刀刃之舞+",
        1,
        "skill",
        extra={"add_many_shivs": True, "shiv_count": 4}
    ),

    "斗篷与匕首": C(
        "斗篷与匕首",
        1,
        "skill",
        extra={"gain_block_and_add_shiv": True, "block_value": 6, "shiv_count": 1}
    ),
    "斗篷与匕首+": C(
        "斗篷与匕首+",
        1,
        "skill",
        extra={"gain_block_and_add_shiv": True, "block_value": 6, "shiv_count": 2}
    ),

    "先制打击": C(
        "先制打击",
        0,
        "attack",
        damage=8,
        extra={"add_shiv": 1}
    ),
    "先制打击+": C(
        "先制打击+",
        0,
        "attack",
        damage=11,
        extra={"add_shiv": 1}
    ),

    "精准": C(
        "精准",
        1,
        "power",
        is_power=True,
        extra={"shiv_damage_bonus": 4}
    ),
    "精准+": C(
        "精准+",
        1,
        "power",
        is_power=True,
        extra={"shiv_damage_bonus": 6}
    ),

    "幻影之刃": C(
        "幻影之刃",
        1,
        "power",
        is_power=True,
        extra={"first_shiv_bonus_damage_each_turn": 4}
    ),
    "幻影之刃+": C(
        "幻影之刃+",
        1,
        "power",
        is_power=True,
        extra={"first_shiv_bonus_damage_each_turn": 6}
    ),

    "无尽刀刃": C(
        "无尽刀刃",
        1,
        "power",
        is_power=True,
        turn_start_add_shiv=1
    ),
    "无尽刀刃+": C(
        "无尽刀刃+",
        1,
        "power",
        is_power=True,
        turn_start_add_shiv=2
    ),

    # ===== 消耗牌 =====
    "背刺": C(
        "背刺",
        0,
        "attack",
        damage=11,
        innate=True,
        exhaust=True
    ),
    "背刺+": C(
        "背刺+",
        0,
        "attack",
        damage=15,
        innate=True,
        exhaust=True
    ),

    "肾上腺素": C(
        "肾上腺素",
        0,
        "skill",
        draw=2,
        energy_gain=1,
        exhaust=True
    ),
    "肾上腺素+": C(
        "肾上腺素+",
        0,
        "skill",
        draw=2,
        energy_gain=2,
        exhaust=True
    ),

    "计算下注": C(
        "计算下注",
        0,
        "skill",
        exhaust=True,
        extra={"calculated_gamble": True}
    ),
    "计算下注+": C(
        "计算下注+",
        0,
        "skill",
        retain=True,
        exhaust=True,
        extra={"calculated_gamble": True}
    ),

    "钢铁风暴": C(
        "钢铁风暴",
        1,
        "skill",
        exhaust=True,
        extra={"storm_of_steel": True}
    ),
    "钢铁风暴+": C(
        "钢铁风暴+",
        1,
        "skill",
        exhaust=True,
        extra={"storm_of_steel": True}
    ),

    "暗影步": C(
        "暗影步",
        1,
        "skill",
        exhaust=True,
        extra={"discard_all_hand": True}
    ),
    "暗影步+": C(
        "暗影步+",
        0,
        "skill",
        exhaust=True,
        extra={"discard_all_hand": True}
    ),

    "夜魇": C(
        "夜魇",
        3,
        "skill",
        exhaust=True
    ),
    "夜魇+": C(
        "夜魇+",
        2,
        "skill",
        exhaust=True
    ),

    "爆发": C(
        "爆发",
        1,
        "skill",
        exhaust=True,
        extra={"next_skill_extra_plays": 1}
    ),
    "爆发+": C(
        "爆发+",
        1,
        "skill",
        exhaust=True,
        extra={"next_skill_extra_plays": 2}
    ),

    "蜃景": C(
        "蜃景",
        1,
        "skill",
        exhaust=True,
        extra={"gain_block_equal_enemy_poison": True}
    ),
    "蜃景+": C(
        "蜃景+",
        0,
        "skill",
        exhaust=True,
        extra={"gain_block_equal_enemy_poison": True}
    ),

    # ===== 腐蚀波 =====
    # 技能牌，不消耗；本回合每抽1张牌就施毒
    "腐蚀波": C(
        "腐蚀波",
        1,
        "skill",
        extra={"poison_on_draw_this_turn": 2}
    ),
    "腐蚀波+": C(
        "腐蚀波+",
        1,
        "skill",
        extra={"poison_on_draw_this_turn": 3}
    ),

    # ===== 华丽收场 =====
    # 只有 draw_pile 为空时可打出
    "华丽收场": C(
        "华丽收场",
        0,
        "attack",
        damage=50,
        extra={"require_empty_draw_pile": True}
    ),
    "华丽收场+": C(
        "华丽收场+",
        0,
        "attack",
        damage=70,
        extra={"require_empty_draw_pile": True}
    ),

    # ===== 纯格挡有效循环支撑 =====
    "余像": C(
        "余像",
        1,
        "power",
        is_power=True,
        extra={"on_play_gain_block": 1}
    ),
    "余像+": C(
        "余像+",
        1,
        "power",
        is_power=True,
        extra={"on_play_gain_block": 2}
    ),
}


# =========================
# 可选补充基础牌（便于测试）
# =========================
BASIC_TEST_CARDS = {
    "打击": C("打击", 1, "attack", damage=6),
    "打击+": C("打击+", 1, "attack", damage=9),

    "防御": C("防御", 1, "skill", block=5, extra={"simple_block": True}),
    "防御+": C("防御+", 1, "skill", block=8, extra={"simple_block": True}),
}


# =========================
# 总卡池
# =========================
CARD_DB = {}
CARD_DB.update(TEMPLATE_CARDS)
CARD_DB.update(TOKEN_CARDS)
CARD_DB.update(BASIC_TEST_CARDS)
CARD_DB.update(CORE_CARDS)