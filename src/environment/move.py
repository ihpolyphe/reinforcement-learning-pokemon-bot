# -*- coding: utf-8 -*-
"""
Move class. Represents a move, usually associated with a pokemon.

This file is part of the pokemon showdown reinforcement learning bot project,
created by Randy Kotti, Ombeline Lagé and Haris Sahovic as part of their
advanced topics in artifical intelligence course at Ecole Polytechnique.

TODO:
- PP Management
- Flags management
- Hidden power type
- ZMove effects
"""
from .utils import CATEGORIES, MOVES, TARGETS, TYPES, SECONDARIES


empty_move = {
    "accuracy": 0,
    "auto_boosts": {
        "atk": (0, 0),
        "brn": (0, 0),
        "def": (0, 0),
        "frz": (0, 0),
        "par": (0, 0),
        "psn": (0, 0),
        "slp": (0, 0),
        "spa": (0, 0),
        "spd": (0, 0),
        "spe": (0, 0),
        "tox": (0, 0),
    },
    "base_power": 0,
    "boosts": {
        "atk": (0, 0),
        "brn": (0, 0),
        "def": (0, 0),
        "frz": (0, 0),
        "par": (0, 0),
        "psn": (0, 0),
        "slp": (0, 0),
        "spa": (0, 0),
        "spd": (0, 0),
        "spe": (0, 0),
        "tox": (0, 0),
    },
    "category": {category: False for category in CATEGORIES},
    "exists": 0,
    "max_pp": 0,
    "priority": 0,
    "secondaries": {
        "par": 0,
        "brn": 0,
        "frz": 0,
        "psn": 0,
        "slp": 0,
        "flinch": 0,
        "confusion": 0,
    },
    "target": {target: False for target in TARGETS},
    "type": {type_: False for type_ in TYPES},
    "z_boost": {
        "atk": 0,
        "spa": 0,
        "def": 0,
        "spd": 0,
        "spe": 0,
        "fnt": 0,
        "accuracy": 0,
        "evasion": 0,
    },
    "z_power": 0,
    "z_effect": False,
}
"""This dictionnary is used inplace of unknown moves"""

class Move:
    """
    Represents a move.
    """
    def __init__(self, move: str) -> None:
        """
        Initialize a Move object.

        Args:
            move (str): The move's name
        """
        self.name = move
        self.pp = 0
        self.max_pp = 0
        self.disabled = False
        self.target = None
        self.type = None
        self.z_boost = {}
        self.z_power = 0
        self.z_effect = False
        self.secondaries = {
            "par": 0,
            "brn": 0,
            "frz": 0,
            "psn": 0,
            "slp": 0,
            "flinch": 0,
            "confusion": 0,
        }
        # boostsとauto_boostsを追加
        self.boosts = {
            "atk": (0, 0),
            "brn": (0, 0),
            "def": (0, 0),
            "frz": (0, 0),
            "par": (0, 0),
            "psn": (0, 0),
            "slp": (0, 0),
            "spa": (0, 0),
            "spd": (0, 0),
            "spe": (0, 0),
            "tox": (0, 0),
        }
        self.auto_boosts = {
            "atk": (0, 0),
            "brn": (0, 0),
            "def": (0, 0),
            "frz": (0, 0),
            "par": (0, 0),
            "psn": (0, 0),
            "slp": (0, 0),
            "spa": (0, 0),
            "spd": (0, 0),
            "spe": (0, 0),
            "tox": (0, 0),
        }

        # 技名を正規化
        move = move.lower()
        if move.startswith('hiddenpower'):
            move = 'hiddenpower'
        if move.startswith('z'):
            move = move[1:]

        # 新しい世代の技を追加
        if move not in MOVES:
            print(f"[DEBUG] Adding new move: {move}")
            MOVES[move] = {
                "name": move,
                "type": "normal",  # デフォルトタイプ
                "target": "normal",
                "basePower": 80,   # デフォルト威力
                "accuracy": 100,   # デフォルト命中率
                "pp": 15,          # デフォルトPP
                "category": "Physical",  # デフォルトカテゴリ
                "priority": 0,     # デフォルト優先度
            }

        move_data = MOVES[move]
        self.name = move_data["name"]
        self.type = move_data["type"].lower()
        self.target = move_data["target"]
        self.base_power = move_data.get("basePower", 80)
        self.accuracy = move_data.get("accuracy", 100)
        self.pp = move_data.get("pp", 15)
        self.max_pp = self.pp
        self.category = move_data.get("category", "Physical")
        self.priority = move_data.get("priority", 0)

        if "secondary" in move_data:
            if move_data["secondary"]:
                self.add_secondary(move_data["secondary"])
        elif "secondaries" in move_data:
            for secondary in move_data["secondaries"]:
                self.add_secondary(secondary)

        self.z_boost = {
            "atk": 0,
            "spa": 0,
            "def": 0,
            "spd": 0,
            "spe": 0,
            "fnt": 0,
            "accuracy": 0,
            "evasion": 0,
        }
        if "zMoveBoost" in move_data:
            for key, val in move_data["zMoveBoost"].items():
                if key not in self.z_boost:
                    print(f"[DEBUG] Unknown z-boost stat: {key}")
                else:
                    self.z_boost[key] = val
        if "zMovePower" in move_data:
            self.z_power = move_data["zMovePower"]
        else:
            self.z_power = 0
        if "zMoveEffect" in move_data:
            self.z_effect = True
        else:
            self.z_effect = False

    def __repr__(self) -> str:
        """
        String representation of the Move, in the form "Move object: name"
        """
        return f"Move object: {self.name}"

    def add_secondary(self, effect:dict) -> None:
        """
        Add a secondary effect.

        Arg:
            effect (dict): dictionnary describing the effect, from the move database
        """
        if "boosts" in effect:
            for stat, val in effect["boosts"].items():
                if stat not in self.boosts:
                    print("stat in boost", stat)
                self.boosts[stat] = (val, effect["chance"])
        elif "status" in effect:
            if effect["status"] not in SECONDARIES:
                print("UNKNOWN SECONDARY", effect["status"])
            else:
                self.secondaries[effect["status"]] = effect["chance"]
        elif "volatileStatus" in effect:
            if effect["volatileStatus"] not in SECONDARIES:
                print("UNKNOWN SECONDARY", effect["volatileStatus"])
            else:
                self.secondaries[effect["volatileStatus"]] = effect["chance"]
        elif "self" in effect:
            if "boosts" in effect["self"]:
                for stat, val in effect["self"]["boosts"].items():
                    if stat not in self.auto_boosts:
                        print("stat in auto boost", stat)
                    self.auto_boosts[stat] = (val, effect["chance"])
            else:
                print("effect self", effect)
        else:
            effect.pop("chance")
            if effect:
                print("effect", effect)

    @property
    def dic_state(self) -> dict:
        """
        dict: dictionnary describing the object's state
        """
        return {
            "accuracy": self.accuracy,
            "auto_boosts": self.auto_boosts,
            "base_power": self.base_power,
            "boosts": self.boosts,
            "category": {
                category: category == self.category for category in CATEGORIES
            },
            "exists": 1,
            "max_pp": self.max_pp,
            "priority": self.priority,
            "target": {target: target == self.target for target in TARGETS},
            "type": {type_: type_ == self.type for type_ in TYPES},
            "secondaries": self.secondaries,
            "z_boost": self.z_boost,
            "z_power": self.z_power,
            "z_effect": self.z_effect,
        }


class ZMoveException(Exception):
    """
    Exception raised when a Move class is instantiated from a ZMove
    """
    pass
