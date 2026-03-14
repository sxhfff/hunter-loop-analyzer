# ui/app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from collections import Counter

from engine.types import GameState
from engine.search import find_loop
from data.hunter_cards import CARD_DB


# =========================
# 基础工具
# =========================
def multiset_subtract(full_deck, hand):
    """
    按张数做 full_deck - hand
    例如：
    full_deck = ["打击", "打击", "防御", "杂技"]
    hand      = ["打击", "杂技"]
    => draw_pile = ["打击", "防御"]
    """
    full_counter = Counter(full_deck)
    hand_counter = Counter(hand)

    for card_name, cnt in hand_counter.items():
        if full_counter[card_name] < cnt:
            return None, f"手牌中的【{card_name}】数量超过了完整牌组中的数量。"

    remain_counter = full_counter - hand_counter

    draw_pile = []
    for card_name, cnt in remain_counter.items():
        draw_pile.extend([card_name] * cnt)

    return draw_pile, None


def format_card_count(cards):
    if not cards:
        return "（空）"

    counter = Counter(cards)
    lines = []
    for name in sorted(counter.keys()):
        cnt = counter[name]
        if cnt == 1:
            lines.append(f"- {name}")
        else:
            lines.append(f"- {name} ×{cnt}")
    return "\n".join(lines)


def build_initial_state(full_deck, hand, energy):
    draw_pile, err = multiset_subtract(full_deck, hand)
    if err:
        raise ValueError(err)

    return GameState(
        hand=list(hand),
        draw_pile=list(draw_pile),
        discard_pile=[],
        exhaust_pile=[],
        powers_played=[],
        energy=energy,
        block=0,
        strength=0,
        dexterity=0,
        turn=1,
        history=[],
        total_damage=0,
        total_block_gained=0,
        total_poison_added=0,
        metadata={}
    )


def remove_one(cards, card_name):
    if card_name in cards:
        cards.remove(card_name)


def init_session_state():
    if "hand_cards" not in st.session_state:
        st.session_state.hand_cards = []

    if "full_deck_cards" not in st.session_state:
        st.session_state.full_deck_cards = []

    if "selected_card" not in st.session_state:
        all_cards = sorted(CARD_DB.keys())
        st.session_state.selected_card = all_cards[0] if all_cards else ""


# =========================
# 初始化
# =========================
init_session_state()

st.set_page_config(page_title="杀戮尖塔2 猎人循环分析器", layout="wide")

st.title("杀戮尖塔2 猎人循环分析器")
st.caption("使用按钮添加手牌与完整牌组，程序内部自动计算抽牌堆。")

with st.expander("输入规则", expanded=True):
    st.markdown(
        """
1. **手牌**：当前手上的牌  
2. **完整牌组**：整副牌，**包含手牌**
3. 程序内部自动计算抽牌堆：
   `抽牌堆 = 完整牌组 - 手牌`
4. UI **不显示**抽牌堆和消耗堆
5. 有效循环判定为：
   - 造成直接伤害，或
   - 获得格挡，或
   - 增加中毒
6. `华丽收场` 只有在 **抽牌堆为空** 时才能打出
7. `腐蚀波` 是技能牌、不会消耗，并且算有效输出来源
        """
    )

# =========================
# 选牌和添加
# =========================
st.subheader("添加卡牌")

all_card_names = sorted(CARD_DB.keys())

col_select, col_add_hand, col_add_deck, col_clear_hand, col_clear_deck = st.columns([3, 1, 1, 1, 1])

with col_select:
    selected_card = st.selectbox(
        "选择一张牌",
        options=all_card_names,
        key="selected_card"
    )

with col_add_hand:
    if st.button("加入手牌"):
        st.session_state.hand_cards.append(selected_card)
        st.rerun()

with col_add_deck:
    if st.button("加入完整牌组"):
        st.session_state.full_deck_cards.append(selected_card)
        st.rerun()

with col_clear_hand:
    if st.button("清空手牌"):
        st.session_state.hand_cards = []
        st.rerun()

with col_clear_deck:
    if st.button("清空牌组"):
        st.session_state.full_deck_cards = []
        st.rerun()

# =========================
# 当前手牌 / 牌组显示
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("当前手牌")
    st.code(format_card_count(st.session_state.hand_cards), language="text")

    if st.session_state.hand_cards:
        remove_hand_card = st.selectbox(
            "从手牌删除 1 张",
            options=sorted(set(st.session_state.hand_cards)),
            key="remove_hand_card"
        )
        if st.button("确认删除手牌"):
            remove_one(st.session_state.hand_cards, remove_hand_card)
            st.rerun()

with col2:
    st.subheader("当前完整牌组")
    st.code(format_card_count(st.session_state.full_deck_cards), language="text")

    if st.session_state.full_deck_cards:
        remove_deck_card = st.selectbox(
            "从完整牌组删除 1 张",
            options=sorted(set(st.session_state.full_deck_cards)),
            key="remove_deck_card"
        )
        if st.button("确认删除牌组"):
            remove_one(st.session_state.full_deck_cards, remove_deck_card)
            st.rerun()

# =========================
# 文本预览
# =========================
with st.expander("文本预览"):
    c1, c2 = st.columns(2)
    with c1:
        st.text_area(
            "手牌文本预览",
            value="\n".join(st.session_state.hand_cards),
            height=220,
            disabled=True
        )
    with c2:
        st.text_area(
            "完整牌组文本预览",
            value="\n".join(st.session_state.full_deck_cards),
            height=220,
            disabled=True
        )

# =========================
# 参数区
# =========================
st.subheader("分析参数")

col_p1, col_p2 = st.columns(2)

with col_p1:
    energy = st.number_input("当前能量", min_value=0, max_value=20, value=3, step=1)

with col_p2:
    max_depth = st.number_input("搜索深度上限", min_value=1, max_value=200, value=20, step=1)

run_btn = st.button("开始分析", type="primary")

# =========================
# 分析
# =========================
if run_btn:
    hand_cards = list(st.session_state.hand_cards)
    full_deck_cards = list(st.session_state.full_deck_cards)

    if not hand_cards:
        st.error("手牌不能为空。")
        st.stop()

    if not full_deck_cards:
        st.error("完整牌组不能为空。")
        st.stop()

    draw_pile, err = multiset_subtract(full_deck_cards, hand_cards)
    if err:
        st.error(err)
        st.stop()

    try:
        init_state = build_initial_state(full_deck_cards, hand_cards, int(energy))
    except ValueError as e:
        st.error(str(e))
        st.stop()

    st.subheader("输入检查")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**当前手牌**")
        st.code(format_card_count(hand_cards), language="text")

    with c2:
        st.markdown("**完整牌组**")
        st.code(format_card_count(full_deck_cards), language="text")

    st.info(f"内部已自动计算初始抽牌堆，共 {len(draw_pile)} 张。")

    with st.spinner("正在搜索有效循环路径..."):
        result = find_loop(init_state, max_depth=int(max_depth))

    st.subheader("分析结果")

    if result.get("found", False):
        st.success("找到有效循环。")

        path = result.get("path", [])
        if path:
            st.markdown("**循环路径**")
            st.code(" -> ".join(path), language="text")
        else:
            st.code("找到有效循环，但路径为空。", language="text")

        reason = result.get("reason", "")
        if reason:
            st.info(reason)

    else:
        st.warning("未找到有效循环。")

        best_path = result.get("best_path", [])
        if best_path:
            st.markdown("**最接近有效推进的路径**")
            st.code(" -> ".join(best_path), language="text")
        else:
            st.code("未找到可用推进路径。", language="text")

        reason = result.get("reason", "")
        if reason:
            st.info(reason)

# =========================
# 卡池预览
# =========================
with st.expander("当前可选卡牌列表"):
    st.code("\n".join(all_card_names), language="text")