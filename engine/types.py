# engine/types.py
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass(frozen=True)
class CardDef:
    id: str
    name: str
    cost: int = 0
    card_type: str = "skill"   # attack / skill / power

    # ===== 基础数值 =====
    damage: int = 0
    block: int = 0
    draw: int = 0
    discard: int = 0
    energy_gain: int = 0

    weak: int = 0
    vulnerable: int = 0
    poison: int = 0

    # ===== 常用标签 =====
    shiv: int = 0
    innate: bool = False
    token: bool = False
    retain: bool = False
    is_power: bool = False

    # ===== 特殊机制 =====
    exhaust: bool = False                 # 打出后进入消耗堆，本场战斗不再出现
    play_on_discard: bool = False         # 奇巧：被弃牌时自动打出
    draw_on_discard: int = 0              # 被弃牌时抽牌
    energy_on_discard: int = 0            # 被弃牌时获得能量
    auto_play_no_energy: bool = True      # 奇巧触发时是否免费打出

    # ===== 回合开始类效果（先预留） =====
    turn_start_draw: int = 0
    turn_start_discard: int = 0
    turn_start_block: int = 0
    turn_start_poison_all: int = 0
    turn_start_add_shiv: int = 0

    # ===== 扩展参数 =====
    # 用于华丽收场、腐蚀波、爆发、多段攻击等特殊逻辑
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GameState:
    # ===== 手牌/牌堆区 =====
    hand: List[str]
    draw_pile: List[str]
    discard_pile: List[str]
    exhaust_pile: List[str] = field(default_factory=list)
    powers_played: List[str] = field(default_factory=list)

    # ===== 资源 =====
    energy: int = 3
    block: int = 0
    strength: int = 0
    dexterity: int = 0

    # ===== 回合/路径 =====
    turn: int = 1
    history: List[str] = field(default_factory=list)

    # ===== 有效循环统计 =====
    # 直接伤害
    total_damage: int = 0
    # 获得格挡
    total_block_gained: int = 0
    # 中毒增量（腐蚀波等要靠这个判定为有效输出）
    total_poison_added: int = 0

    # ===== 扩展运行态 =====
    metadata: Dict[str, Any] = field(default_factory=dict)

    def copy_public_summary(self) -> Dict[str, Any]:
        return {
            "hand": list(self.hand),
            "draw_pile": list(self.draw_pile),
            "discard_pile": list(self.discard_pile),
            "exhaust_pile": list(self.exhaust_pile),
            "powers_played": list(self.powers_played),
            "energy": self.energy,
            "block": self.block,
            "strength": self.strength,
            "dexterity": self.dexterity,
            "turn": self.turn,
            "history": list(self.history),
            "total_damage": self.total_damage,
            "total_block_gained": self.total_block_gained,
            "total_poison_added": self.total_poison_added,
            "metadata": dict(self.metadata),
        }