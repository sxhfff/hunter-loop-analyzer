# engine/search.py
from engine.state_ops import clone_state
from engine.resolver import play_card


def state_signature(state):
    """
    随机洗牌环境下的状态签名：
    - hand / draw_pile / discard_pile / exhaust_pile / powers_played
      都按“多重集合”处理，不看顺序
    - energy / block / strength / dexterity 计入
    - metadata 只纳入影响当前回合资源循环的关键部分
    """
    md = state.metadata

    return (
        tuple(sorted(state.hand)),
        tuple(sorted(state.draw_pile)),
        tuple(sorted(state.discard_pile)),
        tuple(sorted(state.exhaust_pile)),
        tuple(sorted(state.powers_played)),
        state.energy,
        state.block,
        state.strength,
        state.dexterity,
        md.get("enemy_poison", 0),
        md.get("discarded_this_turn", 0),
        md.get("poison_on_draw_this_turn", 0),
        md.get("on_play_gain_block", 0),
        md.get("shiv_damage_bonus", 0),
        md.get("first_shiv_bonus_damage_each_turn", 0),
        md.get("first_shiv_used_this_turn", False),
        md.get("shivs_are_aoe", False),
        md.get("next_skill_extra_plays", 0),
        md.get("free_all_hand_this_turn", False),
        md.get("free_attack_cost_this_turn", False),
        md.get("free_skill_cost_this_turn", False),
    )


def legal_plays(state):
    """
    当前可尝试打出的牌列表。
    这里只列出手牌，真正是否合法交给 play_card() 判断。
    """
    return list(state.hand)


def is_effective_progress(before_state, after_state):
    """
    判定这一段是否属于“有效输出推进”：
    - 直接伤害增加
    - 或格挡增加
    - 或中毒增加
    """
    damage_gain = after_state.total_damage - before_state.total_damage
    block_gain = after_state.total_block_gained - before_state.total_block_gained
    poison_gain = after_state.total_poison_added - before_state.total_poison_added

    return (damage_gain > 0) or (block_gain > 0) or (poison_gain > 0)


def cycle_has_effective_output(root_state, cur_state):
    """
    判定从 root_state 到 cur_state 这段路径是否产生了有效输出
    """
    damage_gain = cur_state.total_damage - root_state.total_damage
    block_gain = cur_state.total_block_gained - root_state.total_block_gained
    poison_gain = cur_state.total_poison_added - root_state.total_poison_added

    return (
        (damage_gain > 0) or
        (block_gain > 0) or
        (poison_gain > 0)
    )


def score_state_progress(before_state, after_state):
    """
    给搜索做一个简单评分：
    更偏好能造成输出、同时资源不崩的路径
    """
    damage_gain = after_state.total_damage - before_state.total_damage
    block_gain = after_state.total_block_gained - before_state.total_block_gained
    poison_gain = after_state.total_poison_added - before_state.total_poison_added

    score = 0
    score += damage_gain * 10
    score += block_gain * 3
    score += poison_gain * 6
    score += after_state.energy - before_state.energy
    score += len(after_state.hand) - len(before_state.hand) * 0.1
    return score


def sorted_candidate_plays(state):
    """
    候选牌排序：
    优先尝试更可能形成循环的牌
    """
    cards = legal_plays(state)

    def key_fn(card_name):
        card = getattr(__import__("data.hunter_cards", fromlist=["CARD_DB"]), "CARD_DB")[card_name]

        # 优先级设计：
        # 奇巧 / 抽牌 / 回能 / 小刀生成 / 腐蚀波 / 华丽收场 这类优先
        priority = 0

        if card.play_on_discard:
            priority += 100
        if card.draw > 0:
            priority += 30
        if card.energy_gain > 0:
            priority += 25
        if card.shiv > 0:
            priority += 20
        if card.block > 0:
            priority += 10
        if card.damage > 0:
            priority += 15
        if card.extra.get("draw_then_discard", False):
            priority += 40
        if card.extra.get("draw_then_discard_same", False):
            priority += 40
        if card.extra.get("calculated_gamble", False):
            priority += 45
        if card.extra.get("storm_of_steel", False):
            priority += 35
        if card.extra.get("poison_on_draw_this_turn", 0) > 0:
            priority += 50
        if card.extra.get("require_empty_draw_pile", False):
            priority += 12

        # 低费优先
        priority -= card.cost

        return -priority, card_name

    return sorted(cards, key=key_fn)


def dfs_find_loop(
    root_state,
    cur_state,
    root_sig,
    path,
    max_depth,
    visited_best_depth,
    best_progress
):
    """
    深搜找循环。

    root_state: 起点状态
    cur_state: 当前状态
    root_sig: 起点签名
    path: 当前路径
    max_depth: 深度限制
    visited_best_depth: 记录某状态最早在哪层到达，避免无意义重复
    best_progress: 用于找不到循环时返回“最接近”的路径
    """
    cur_sig = state_signature(cur_state)
    depth = len(path)

    # 只要回到了根签名，并且路径非空，就尝试判定是否为有效循环
    if depth > 0 and cur_sig == root_sig:
        if cycle_has_effective_output(root_state, cur_state):
            return {
                "found": True,
                "path": list(path),
                "final_state": cur_state,
            }

    if depth >= max_depth:
        return None

    prev_best_depth = visited_best_depth.get(cur_sig)
    if prev_best_depth is not None and prev_best_depth <= depth:
        return None
    visited_best_depth[cur_sig] = depth

    candidates = sorted_candidate_plays(cur_state)

    any_progress_here = False

    for card_name in candidates:
        next_state = clone_state(cur_state)
        ok = play_card(next_state, card_name)
        if not ok:
            continue

        path.append(card_name)

        if is_effective_progress(cur_state, next_state):
            any_progress_here = True
            score = score_state_progress(root_state, next_state)
            if score > best_progress["score"]:
                best_progress["score"] = score
                best_progress["path"] = list(path)
                best_progress["state"] = next_state

        ans = dfs_find_loop(
            root_state=root_state,
            cur_state=next_state,
            root_sig=root_sig,
            path=path,
            max_depth=max_depth,
            visited_best_depth=visited_best_depth,
            best_progress=best_progress,
        )
        if ans is not None:
            return ans

        path.pop()

    # 如果这一层没有任何有效推进，也不代表立刻失败；
    # 只是说明当前分支没有继续价值
    if not any_progress_here and depth > 0:
        return None

    return None


def find_loop(state, max_depth=20):
    """
    对外接口：

    返回格式：
    {
        "found": True/False,
        "path": [...],                # 若找到循环，返回循环路径
        "best_path": [...],           # 若没找到，返回最接近有效推进的路径
        "reason": str,
    }
    """
    root_state = clone_state(state)
    root_sig = state_signature(root_state)

    visited_best_depth = {}
    best_progress = {
        "score": float("-inf"),
        "path": [],
        "state": None,
    }

    ans = dfs_find_loop(
        root_state=root_state,
        cur_state=clone_state(root_state),
        root_sig=root_sig,
        path=[],
        max_depth=max_depth,
        visited_best_depth=visited_best_depth,
        best_progress=best_progress,
    )

    if ans is not None:
        return {
            "found": True,
            "path": ans["path"],
            "best_path": ans["path"],
            "reason": "找到有效循环：状态可重复，且造成了伤害/格挡/中毒增量。",
        }

    if best_progress["path"]:
        return {
            "found": False,
            "path": None,
            "best_path": best_progress["path"],
            "reason": "未找到有效循环，已返回当前搜索到的最接近有效推进路径。",
        }

    return {
        "found": False,
        "path": None,
        "best_path": [],
        "reason": "未找到有效循环，也未找到明显有效推进路径。",
    }