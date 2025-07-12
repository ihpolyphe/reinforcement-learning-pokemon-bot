# -*- coding: utf-8 -*-
"""
Battle class. Represents, from a player's perspective, the state of a Pokemon battle.

This file is part of the pokemon showdown reinforcement learning bot project,
created by Randy Kotti, Ombeline Lagé and Haris Sahovic as part of their
advanced topics in artifical intelligence course at Ecole Polytechnique.

TODO:
- Extend to double battles
- Expand parsing to take into account all types of messages
- Check player identity definition and update, especially in _get_pokemon_from_reference
- Check parse in detail
- In parse_request, manage ultra boost
- Parse turn id in parse_request
"""

from environment.pokemon import empty_pokemon, Pokemon, Move
from typing import List, Optional


class Battle:
    """
    Represents the state of a Pokemon battle for a given player.
    """

    ACTIONS_TO_IGNORE = [
        "",
        "-ability",
        "-activate",
        "-anim",
        "-center",
        "-crit",
        "-cureteam",
        "-damage",
        "-endability",
        "-enditem",
        "-fail",
        "-fieldactivate",
        "-fieldend",
        "-fieldstart",
        "-heal",
        "-hint",
        "-hitcount",
        "-immune",
        "-item",
        "-message",
        "-miss",
        "-mustrecharge",
        "-prepare",  # TODO : switch to an actual boolean somewhere, this needs to be used properly
        "-resisted",
        "-singlemove",  # TODO : check single move possibilities
        "-singleturn",  # TODO : check single turn possibilities
        "-supereffective",
        "-transform",
        "-zbroken",  # TODO : what is this ?
        "-zpower",  # TODO : item assignment ?
        "cant",
        "deinit",
        "detailschange",
        "drag",
        "gen",
        "init",
        "j",
        "l",
        "player",
        "rule",
        "seed",
        "start",
        "swap",
        "replace",
        "tier",
        "title",
        "upkeep",
    ]
    """List of str: contain types of messages to ignore while parsing"""

    FIELDS = [
        "Aurora Veil",
        "Light Screen",
        "Reflect",
        "Safeguard",
        "Spikes",
        "Stealth Rock",
        "Sticky Web",
        "Tailwind",
        "Toxic Spikes",
    ]
    """List of str: contain possible fields statuses"""

    WEATHERS = [
        "none",
        "DesolateLand",
        "Hail",
        "PrimordialSea",
        "RainDance",
        "Safeguard",
        "Sandstorm",
        "SunnyDay",
    ]
    """List of str: contain possible weather statuses"""

    def __init__(self, battle_tag: str, player_name: str) -> None:
        """Battle __init__

        This methods initialises most battle attributes. It records the player's 
        name and battle tag.

        Args:
            attle_tag1 (str): The battle tag, as extracted from showdown
            
            player_name (str): The battle's player name.
        """

        # Simple pre-formatting
        while battle_tag.endswith("\n"):
            battle_tag = battle_tag[:-1]

        # battle_tagが数字だけの場合はbattle-gen9randombattle-xxxxxx形式に変換
        if battle_tag.isdigit():
            battle_tag = f"battle-gen9randombattle-{battle_tag}"
        elif battle_tag.startswith(">"):
            battle_tag = battle_tag[1:]
        self._battle_tag = battle_tag

        # Teams attributes（ここが抜けていたので追加）
        self._player_team = {}
        self._opponent_team = {}
        self._player_team_size = None
        self._opponent_team_size = None

        # End of battle attributes
        self._finished = False
        self._winner = None
        self._won = None

        # This is stored for future extension
        self._gametype = None

        # Some basic information on the battle
        self._player_name = player_name
        self._player_role = None
        self._turn = 0

        # Field and weather information
        self._weather = "none"
        self.p1_fields = {field: False for field in self.FIELDS}
        self.p2_fields = {field: False for field in self.FIELDS}

        self._wait = False

        # Battle state attributes
        self.available_moves = []
        self.available_switches = []
        self.can_mega_evolve = False
        self.can_z_move = False
        self.trapped = False

        self._player_active_pokemon = None
        self._opponent_active_pokemon = None

    def _get_pokemon_from_reference(self, reference: str) -> Pokemon:
        """
        Get a pokemon from a reference.

        Args:
            reference (str): reference to the pokemon

        Returns:
            Pokemon: the pokemon
        """
        player, pokemon_ident = reference[:2], reference.split(": ")[-1].lower()

        if (player == self._player_role) or (
            self._player_role is None
        ):  # this is a hack ; apparently it happens on battle init. This needs to be looked into.
            if pokemon_ident not in self._player_team:
                self._player_team[pokemon_ident] = Pokemon(ident=reference)
            return self._player_team[pokemon_ident]
        elif player is not None:
            if pokemon_ident not in self._opponent_team:
                self._opponent_team[pokemon_ident] = Pokemon(
                    ident=reference, opponents=True
                )
            return self._opponent_team[pokemon_ident]

    def parse_message(self, message: List[str]) -> None:
        """
        Update the object from a message

        Args:
            message (list of str): split message to be parsed
        """
        try:
            if not message or not isinstance(message, list):
                print(f"[WARNING] Invalid message format: {message}")
                return

            # メッセージが文字列の場合は分割
            if isinstance(message[0], str) and "|" in message[0]:
                message = message[0].split("|")

            # print(f"[DEBUG] Parsing message: {'|'.join(message)}")
            # print(f"[DEBUG] Message length: {len(message)}")

            if len(message) <= 1:
                print(f"[WARNING] Message too short: {message}")
                return

            if len(message) > 1 and message[1] in self.ACTIONS_TO_IGNORE:
                return
            elif len(message) > 1 and message[1] == "switch":
                if len(message) > 2 and message[2][0:2] == self._player_role:
                    for pokemon in self._player_team.values():
                        pokemon.active = False
                else:
                    for pokemon in self._opponent_team.values():
                        pokemon.active = False
                if len(message) > 2:
                    pokemon = self._get_pokemon_from_reference(message[2])
                    pokemon.update_from_switch(message)
            elif len(message) > 1 and message[1] == "gametype":
                if len(message) > 2:
                    self._gametype = message[2]
            elif len(message) > 1 and message[1] == "teamsize":
                if len(message) > 3:
                    if message[2] == self._player_role:
                        self._player_team_size = int(message[3])
                    else:
                        self._opponent_team_size = int(message[3])
            elif len(message) > 1 and message[1] == "player":
                if len(message) > 3 and message[3] == self._player_name.lower():
                    if len(message) > 2 and message[2] == "p2":
                        self.player_is_p2()
                    elif len(message) > 2 and message[2] == "p1":
                        self.player_is_p1()
            elif len(message) > 1 and message[1] == "turn":
                if len(message) > 2:
                    print(f"[DEBUG] Turn {message[2]} for battle {self.battle_tag}")
            elif len(message) > 1 and message[1] == "start":
                print(f"[DEBUG] Battle started: {self.battle_tag}")
            elif len(message) > 1 and message[1] == "move":
                if len(message) > 3:
                    pokemon = self._get_pokemon_from_reference(message[2])
                    pokemon.update_from_move(message[3])
            elif len(message) > 1 and message[1] == "faint":
                if len(message) > 2:
                    pokemon = self._get_pokemon_from_reference(message[2])
                    pokemon.set_status("fnt")
            elif len(message) > 1 and message[1] == "win":
                if len(message) > 2:
                    self.won_by(message[2])
            elif len(message) > 1 and message[1] == "-ability":
                if len(message) > 3:
                    pokemon = self._get_pokemon_from_reference(message[2])
                    print(f"[DEBUG] Ability activated: {message[3]} for {pokemon.ident}")
            elif len(message) > 1 and message[1] == "-unboost":
                if len(message) > 4:
                    pokemon = self._get_pokemon_from_reference(message[2])
                    print(f"[DEBUG] Stat unboost: {message[3]} by {message[4]} for {pokemon.ident}")
            elif len(message) > 1 and message[1] == "-weather":
                if len(message) > 2:
                    print(f"[DEBUG] Weather changed to: {message[2]}")
            elif len(message) > 1 and message[1] == "-fieldstart":
                if len(message) > 2:
                    print(f"[DEBUG] Field effect started: {message[2]}")
                    if len(message) > 3 and message[3].startswith("[from] ability:"):
                        ability = message[3].split(": ")[1]
                        print(f"[DEBUG] Field effect from ability: {ability}")
            elif len(message) > 1 and message[1] == "-fieldend":
                if len(message) > 2:
                    print(f"[DEBUG] Field effect ended: {message[2]}")
            else:
                if len(message) > 1:
                    print(f"[DEBUG] Unhandled message type: {message[1]}")
        except Exception as e:
            print(f"[ERROR] Error in parse_message: {e}")
            print(f"[DEBUG] Message that caused error: {'|'.join(message)}")
            print(f"[DEBUG] Message length: {len(message)}")
            print(f"[DEBUG] Message content: {message}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")

    def parse_request(self, request: dict) -> None:
        """
        Update the object from a request

        Args:
            request (dict): parsed json request object
        """
        try:
            if not request or not isinstance(request, dict):
                print(f"[WARNING] Invalid request format: {request}")
                return

            print(f"[DEBUG] Parsing request: {request}")

            if "wait" in request and request["wait"]:
                self._wait = True
            else:
                self._wait = False

            self.available_moves = []
            self.available_switches = []
            self.can_mega_evolve = False
            self.can_z_move = False
            self.trapped = False

            if "side" in request:
                side_request = request["side"]
                if "pokemon" in side_request:
                    for pokemon in side_request["pokemon"]:
                        if "ident" in pokemon and "details" in pokemon:
                            pokemon_ident = pokemon["ident"]
                            pokemon_details = pokemon["details"]
                            if pokemon_ident not in self._player_team:
                                new_pokemon = Pokemon(ident=pokemon_ident)
                                new_pokemon._update_formatted_details(pokemon_details)
                                self._player_team[pokemon_ident] = new_pokemon
                            else:
                                self._player_team[pokemon_ident]._update_formatted_details(pokemon_details)

                            if pokemon.get("active", False):
                                self._player_active_pokemon = self._player_team[pokemon_ident]
                                self._player_team[pokemon_ident].active = True
                                print(f"[DEBUG] Set active pokemon: {pokemon_ident}")
                            elif not self.trapped and pokemon.get("condition", "") != "0 fnt":
                                self.available_switches.append((len(self.available_switches) + 1, pokemon_ident))
                        else:
                            print(f"[WARNING] Pokemon without ident or details: {pokemon}")

            if "active" in request:
                active_request = request["active"][0]
                if "moves" in active_request:
                    for move in active_request["moves"]:
                        if "id" in move:
                            if self._player_active_pokemon:
                                self._player_active_pokemon.update_from_move(move["id"])
                                print(f"[DEBUG] Added move {move['id']} to {self._player_active_pokemon.ident}")
                            self.available_moves.append((len(self.available_moves) + 1, move))
                        else:
                            print(f"[WARNING] Move without id: {move}")

                if "trapped" in active_request and active_request["trapped"]:
                    self.trapped = True
                if "canMegaEvo" in active_request and active_request["canMegaEvo"]:
                    self.can_mega_evolve = True
                if "canZMove" in active_request:
                    self.can_z_move = active_request["canZMove"]

            self._turn += 1
            print(f"[DEBUG] Turn updated to {self._turn}")
            print(f"[DEBUG] Parsed request for battle {self.battle_tag}")
            print(f"[DEBUG] After parse_request: _player_active_pokemon={self._player_active_pokemon}")
            print(f"[DEBUG] After parse_request: active_pokemon={self.active_pokemon}")
            if self._player_active_pokemon:
                print(f"[DEBUG] Active pokemon moves: {list(self._player_active_pokemon.moves.keys())}")
            if self.active_pokemon:
                print(f"[DEBUG] Active pokemon moves (via property): {list(self.active_pokemon.moves.keys())}")
        except Exception as e:
            print(f"[ERROR] Error in parse_request: {e}")
            print(f"[DEBUG] Request that caused error: {request}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")

    def player_is_p1(self) -> None:
        """
        Sets the battle's player to p1
        """
        self._player_role = "p1"

    def player_is_p2(self) -> None:
        """
        Sets the battle's player to p2
        """
        self._player_role = "p2"


    def won_by(self, winner: str) -> None:
        """
        Update the battle's winner.

        Args:
            winner (str): player identifier
        """
        self._finished = True
        self._winner = winner
        self._won = self._player_name == winner

    @property
    def active_moves(self) -> List[str]:
        """
        List of str: the active pokemon's moves
        """
        active = self.active_pokemon
        if active:
            return list(active.moves.keys())
        else:
            return []

    @property
    def active_pokemon(self) -> Pokemon:
        """
        Pokemon: the active pokemon, or None
        """
        for pokemon in self._player_team.values():
            if pokemon.active:
                return pokemon
        return None

    @property
    def available_moves_object(self) -> List[Move]:
        """
        List of Move: list of available moves objects
        """
        return [Move(move["id"]) for _, move in self.available_moves]

    @property
    def available_switches_object(self) -> List[Pokemon]:
        """
        List of Pokemon: list of available switches as Pokemon objects
        """
        return [
            self._get_pokemon_from_reference(ident)
            for _, ident in self.available_switches
        ]

    @property
    def battle_tag(self) -> str:
        """
        str: battle's battle_tag
        """
        return self._battle_tag

    @property
    def battle_num(self) -> int:
        parts = self._battle_tag.split('-')
        if len(parts) > 2:
            return int(parts[2])
        elif len(parts) == 1:
            # バトル番号だけの場合（例：122938）
            try:
                return int(parts[0])
            except ValueError:
                print(f"[ERROR] Invalid battle number format: {parts[0]}")
                return -1
        else:
            print(f"[ERROR] Invalid battle_tag format: {self._battle_tag}")
            return -1

    @property
    def dic_state(self) -> dict:
        """
        dict: dictionnary describing the object's state
        """
        active = self.active_pokemon
        opponent_active = self.opponent_active_pokemon

        back = [
            pokemon.dic_state
            for pokemon in self._player_team.values()
            if not pokemon.active
        ]
        opponent_back = [
            pokemon.dic_state
            for pokemon in self._opponent_team.values()
            if not pokemon.active
        ]

        if not active:
            active = empty_pokemon
        else:
            active = active.dic_state
        if not opponent_active:
            opponent_active = empty_pokemon
        else:
            opponent_active = opponent_active.dic_state

        while len(back) < 5:
            back.append(empty_pokemon)
        while len(opponent_back) < 5:
            opponent_back.append(empty_pokemon)

        return {
            "active": active,
            "opponent_active": opponent_active,
            "back": back,
            "opponent_back": opponent_back,
            "weather": {weather: self._weather == weather for weather in self.WEATHERS},
            "field": self.p1_fields if self._player_role == "p1" else self.p2_fields,
            "opponent_field": self.p2_fields
            if self._player_role == "p1"
            else self.p1_fields,
        }

    @property
    def is_ready(self) -> bool:
        """
        Whether the battle is ready for the player to choose a move.

        Returns:
            bool: True if the battle is ready, False otherwise
        """
        try:
            if not self._player_role:
                print(f"[DEBUG] Battle {self.battle_tag} not ready: player role not set")
                return False

            if not self._player_active_pokemon:
                print(f"[DEBUG] Battle {self.battle_tag} not ready: no active pokemon")
                return False

            if not self.available_moves and not self.available_switches:
                print(f"[DEBUG] Battle {self.battle_tag} not ready: no available moves or switches")
                return False

            if self._wait:
                print(f"[DEBUG] Battle {self.battle_tag} not ready: waiting for opponent")
                return False

            print(f"[DEBUG] Battle {self.battle_tag} is ready")
            return True

        except Exception as e:
            print(f"[ERROR] Error in is_ready: {e}")
            print(f"[DEBUG] Battle tag: {self.battle_tag}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return False

    @property
    def opponent_active_pokemon(self) -> Pokemon:
        """
        Pokemon: the opponent's active pokemon, or None
        """
        for pokemon in self._opponent_team.values():
            if pokemon.active:
                return pokemon
        return None

    @property
    def opponent_player_back(self) -> List[str]:
        """
        List of str: the player's back pokemons' species names
        """
        return [
            pokemon.species
            for pokemon in self._opponent_team.values()
            if not pokemon.active
        ]

    @property
    def player_back(self) -> List[str]:
        """
        List of str: the player's back pokemons' species names
        """
        return [
            pokemon.species
            for pokemon in self._player_team.values()
            if not pokemon.active
        ]

    @property
    def turn_sent(self) -> int:
        """
        int: turn identifier to send when choosing a move
        """
        return self._turn * 2 + (1 if self._player_role == "p2" else 0)

    @property
    def wait(self) -> bool:
        """
        bool: indicates if the last requested requiered waiting
        """
        return self._wait


    @property
    def won(self) -> bool:
        """
        bool: indicates if the battle was won by the player
        """
        return self._won
