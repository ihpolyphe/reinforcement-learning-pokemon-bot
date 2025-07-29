from .move import empty_move, Move, ZMoveException
from .utils import MOVES, POKEDEX, TYPES, SEXES


# 空のポケモン状態を表すクラス
class EmptyPokemon:
    def __init__(self):
        self.active = False
        self.attracted = False
        self.base_stats = {"hp": 0, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0}
        self.current_hp = 0
        self.encored = False
        self.exists = False
        self.focused = False
        self.infested = False
        self.leech_seeding = False
        self.level = 100
        self.max_hp = 0
        self.mega = False
        self.moves = [empty_move for _ in range(4)]
        self.perish_count = 4
        self.primal = False
        self.sex = {s: False for s in SEXES}
        self.stats = {"atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0}
        self.status = {
            "tox": False,
            "psn": False,
            "slp": False,
            "par": False,
            "brn": False,
            "frz": False,
            "fnt": False,
        }
        self.substitute = False
        self.taunted = False
        self.type = {t: False for t in TYPES}
        self.yawned = False

    @property
    def dic_state(self):
        return self.__dict__

empty_pokemon = EmptyPokemon()


class Pokemon:
    def __init__(self, *, ident: str = None, opponents=False) -> None:
        """
        Pokemon __init__

        Args:
            ident (str, defaults to None): identifier of the pokemon
            opponents (bool, defaults to False): whether the pokemon is an opponent's
        """
        self.active = False
        self.ability = None
        self.attracted = False
        self.base_stats = None
        self.boosts = {
            "atk": 0,
            "spa": 0,
            "def": 0,
            "spd": 0,
            "spe": 0,
            "fnt": 0,
            "accuracy": 0,
            "evasion": 0,
        }
        self.confused = False
        self.current_hp = None
        self.encored = False
        self.focused = False
        self.infested = False
        self.item = None
        self.level = None
        self.leech_seeding = False
        self.max_hp = None
        self.mega = False
        self.moves = {}
        self.opponents = opponents
        self.perish_count = 4
        self.primal = False
        self.sex = None
        self.stats = {"atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0}
        self.status = {
            "tox": False,
            "psn": False,
            "slp": False,
            "par": False,
            "brn": False,
            "frz": False,
            "fnt": False,
        }
        self.substitute = False
        self.taunted = False
        # TODO
        self.species = ''.join([c for c in ident.split(": ")[-1].lower() if c.isalpha()])
        self.types = POKEDEX[self.species]["types"]
        self.type_changed = None
        self.yawned = False

        self.ident = ident
        self.reset_stat_boosts()
        self.set_form(self.species)

    def __repr__(self) -> str:
        return f"Pokemon object: {self.species} ({self.current_hp}/{self.max_hp})"

    def _update_formatted_details(self, details: str) -> None:
        details = details.split(", ")
        if details[-1] == 'shiny':
            details = details[:-1]
        if len(details) == 3:
            _, self.level, self.sex = details
            level_str = self.level[1:]
            if level_str.isdigit():
                self.level = int(level_str)
            else:
                self.level = 100
        elif len(details) == 2:
            _, self.level = details
            level_str = self.level[1:]
            if level_str.isdigit():
                self.level = int(level_str)
            else:
                self.level = 100
            self.sex = "N"
        else:
            _ = details[0]
            self.sex = "N"
            self.level = 100
        if self.sex not in SEXES:
            print("Sex", self.sex, details)

    def boost(self, stat: str, value: int) -> None:
        self.boosts[stat] += value

    def reset_stat_boosts(
        self, clear_neg: bool = False, clear_pos: bool = False
    ) -> None:
        if clear_neg:
            self.boosts = {key: max(0, val) for key, val in self.boosts.items()}
        elif clear_pos:
            self.boosts = {key: min(0, val) for key, val in self.boosts.items()}
        else:
            self.boosts = {
                "atk": 0,
                "spa": 0,
                "def": 0,
                "spd": 0,
                "spe": 0,
                "fnt": 0,
                "accuracy": 0,
                "evasion": 0,
            }

    def set_form(
        self,
        form: str = None,
        *,
        mega: bool = False,
        primal: bool = False,
        complement: str = "",
    ) -> None:
        if mega:
            self.mega = True
            form = self.species + "mega" + complement
        elif primal:
            self.primal = True
            form = self.species + "primal"
        else:
            form = form.lower()
        self.ability = POKEDEX[form]["abilities"]
        self.base_stats = POKEDEX[form]["baseStats"]
        self.types = [t.lower() for t in POKEDEX[form]["types"]]

    def set_status(self, status: str, cure: bool = False) -> None:
        if cure:
            self.status[status] = False
        else:
            self.status[status] = True

    def update_formatted_condition(self, condition: str) -> None:
        if condition == "0 fnt":
            self.status["fnt"] = True
            self.current_hp = 0
        else:
            # 特殊な状態（[from]など）を処理
            if "[" in condition:
                condition = condition.split("[")[0].strip()
            
            if condition[-1] not in "1234567890":
                self.status[condition[-3:]] = True
                condition = condition[:-4]
            
            try:
                self.current_hp, self.max_hp = [int(el) for el in condition.split("/")]
            except ValueError as e:
                print(f"[WARNING] Failed to parse condition: {condition}, error: {e}")
                # デフォルト値を設定
                self.current_hp = 100
                self.max_hp = 100

    def update_from_move(self, move: str) -> None:
        # TODO : refactor with Move somehow ?
        # Deal with zoroark and stuff
        move = ''.join([c for c in move.lower() if c not in " '-"])
        if move.startswith('hiddenpower'):
            move = 'hiddenpower'
        if move in ["struggle", "transform"]:
            return
        if move.startswith('z') and move[1:] in MOVES:
            move = move[1:]
        if move not in MOVES:
            return print('unknown :', move)
        if 'isZ' in MOVES[move]:
            return
        if move not in self.moves:
            if len(self.moves) == 4:
                return print(self.moves.keys(), move, self.species)
            try:
                self.moves[move] = Move(move)
            except ZMoveException:
                pass

    def update_from_request(self, request: dict) -> None:
        self._update_formatted_details(request["details"])
        self.update_formatted_condition(request["condition"])

        self.ability = request["baseAbility"]
        self.active = request["active"]
        self.focused = False
        self.item = request["item"]
        self.moves = {} # TODO : check that this is kinda clever
        for move in request["moves"]:
            self.update_from_move(move)
        self.stats = request["stats"]

    def update_from_switch(self, message: str) -> None:
        self.update_formatted_condition(message[-1])
        self._update_formatted_details(message[-2])

        self.reset_stat_boosts()

        self.active = True
        self.attracted = False
        self.confused = False
        self.encored = False
        self.infested = False
        self.perish_count = 4
        self.substitute = False
        self.taunted = False
        self.type_changed = None

    @property
    def dic_state(self) -> dict:
        if self.type_changed:
            type_ = {t: t == self.type_changed for t in TYPES}
        else:
            type_ = {t: t in self.types for t in TYPES}

        moves = [move.dic_state for move in self.moves.values()]
        while len(moves) < 4:
            moves.append(empty_move)
        return {
            "active": self.active,
            "attracted": self.attracted,
            "base_stats": self.base_stats,
            "current_hp": self.current_hp,
            "encored": self.encored,
            "exists": True,
            "focused": self.focused,
            "infested": self.infested,
            "level": self.level,
            "leech_seeding": self.leech_seeding,
            "max_hp": self.max_hp,
            "mega": self.mega,
            "moves": moves,
            "perish_count": self.perish_count,
            "primal": self.primal,
            "sex": {s: self.sex == s for s in SEXES},
            "stats": self.stats,
            "status": self.status,
            "substitute": self.substitute,
            "taunted": self.taunted,
            "type": type_,
            "yawned": self.yawned,
        }
