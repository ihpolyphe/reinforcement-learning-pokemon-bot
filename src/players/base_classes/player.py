import asyncio
import json
import numpy as np

from abc import ABC, abstractmethod
from random import choices
from threading import Thread
from typing import List

from environment.battle import Battle
from players.base_classes.player_network import PlayerNetwork


class Player(PlayerNetwork, ABC):
    def __init__(
        self,
        username: str,
        password: str,
        mode: str,
        *,
        authentification_address: str,
        avatar: int,
        format: str,
        log_messages_in_console: bool,
        max_concurrent_battles: int,
        server_address: str,
        target_battles: int,
        to_target: str,
        to_challenge: str = None,
    ) -> None:
        super(Player, self).__init__(
            authentification_address=authentification_address,
            avatar=avatar,
            log_messages_in_console=log_messages_in_console,
            password=password,
            server_address=server_address,
            username=username,
            to_challenge=to_challenge,
            format=format
        )
        self.max_concurrent_battles = max_concurrent_battles
        self.mode = mode
        self.target_battles = target_battles
        self.to_target = to_target

        self.current_battles = 0
        self.total_battles = 0

        self.battles = {}

        self._observations = {}
        self._actions = {}
        self._wins = {}

    async def battle(self, message) -> None:
        """
        Parse and manage battle messages.
        """
        try:
            split_message = message.split("|")
            if len(split_message) <= 1:
                print("[WARNING] Invalid battle message format")
                return

            current_battle = None
            battle_info = split_message[0].split("-")
            if len(battle_info) > 2:
                if battle_info[2] not in self.battles:
                    self.battles[battle_info[2]] = Battle(battle_info[2], self.username)
                    self.current_battles += 1
                    if "2" in self.username.lower():
                        print(f"Battle %3d / %3d started" % (len(self.battles), self.target_battles))
                if battle_info[2] in self.battles:
                    current_battle = self.battles[battle_info[2]]

            # Send move
            if len(split_message) > 1:
                print(f"[DEBUG] Processing message: {'|'.join(split_message)}")  # デバッグログを追加
                if split_message[1] == "request":
                    if len(split_message) > 2 and split_message[2] and current_battle is not None:
                        try:
                            current_battle.parse_request(json.loads(split_message[2]))
                            print(f"[DEBUG] Parsed request for battle {current_battle.battle_tag}")  # デバッグログを追加
                        except json.JSONDecodeError as e:
                            print(f"[ERROR] Failed to parse request: {e}")
                        except Exception as e:
                            print(f"[ERROR] Error in parse_request: {e}")
                    if current_battle is not None and current_battle.is_ready:
                        print(f"[DEBUG] Battle {current_battle.battle_tag} is ready, selecting move")  # デバッグログを追加
                        await self.select_save_move(current_battle)
                elif split_message[1] == "callback" and len(split_message) > 2 and split_message[2] == "trapped" and current_battle is not None:
                    await self.select_save_move(current_battle, trapped=True)
                elif split_message[1] == "error" and len(split_message) > 2 and current_battle is not None:
                    print(f"[DEBUG] Received error message: {'|'.join(split_message)}")  # デバッグログを追加
                    if split_message[2].startswith("[Invalid choice] There's nothing to choose"):
                        pass
                    elif split_message[2].startswith("[Invalid choice] Can't do anything"):
                        pass
                    elif split_message[2].startswith("[Invalid choice] Sorry, too late"):
                        pass
                    elif split_message[2].startswith("[Invalid choice] Can't switch"):
                        current_battle.trapped = True
                        await self.select_save_move(current_battle)
                    elif split_message[2].startswith("[Invalid choice]"):
                        await self.select_save_move(current_battle)
                # Update player id and turn count
                elif (
                    split_message[1] == "player"
                    and len(split_message) > 3
                    and split_message[3] == self.username.lower()
                    and current_battle is not None
                ):
                    if split_message[2] == "p2":
                        current_battle.player_is_p2()
                    elif split_message[2] == "p1":
                        current_battle.player_is_p1()

                    if current_battle.is_ready:
                        await self.select_save_move(current_battle)
                elif split_message[1] == "win" and len(split_message) > 2 and current_battle is not None:
                    current_battle.won_by(split_message[2])
                    self._wins[current_battle.battle_num] = int(self.username.lower() == split_message[2])
                    self.current_battles -= 1
                    self.total_battles += 1
                    print(f"[DEBUG] {self.username} battle ended: total_battles={self.total_battles}, current_battles={self.current_battles}")

                    await self.leave_battle(current_battle)
                elif split_message[1] == "turn" and current_battle is not None:
                    print(f"[DEBUG] Turn {split_message[2]} for battle {current_battle.battle_tag}")  # デバッグログを追加
                    if current_battle.is_ready:
                        await self.select_save_move(current_battle)
                else:
                    if current_battle is not None:
                        try:
                            current_battle.parse_message(split_message)
                        except Exception as e:
                            print(f"[ERROR] Error in parse_message: {e}")
                            print(f"[DEBUG] Message that caused error: {'|'.join(split_message)}")
        except Exception as e:
            print(f"[ERROR] Unexpected error in battle method for {self.username}: {e}")
            print(f"[DEBUG] Message that caused error: {message}")

    async def select_save_move(self, battle: Battle, *, trapped: bool = False) -> None:
        print(f"[DEBUG] Selecting move for battle {battle.battle_tag}")  # デバッグログを追加
        if battle.battle_num not in self._observations.keys():
            self._observations[battle.battle_num] = []
            self._actions[battle.battle_num] = []
        self._observations[battle.battle_num].append(battle.dic_state)
        action = await self.select_move(battle, trapped=trapped)
        self._actions[battle.battle_num].append(action)


    async def random_move(self, battle: Battle, *, trapped: bool = False) -> None:
        state = battle.dic_state
        commands = []
        switch_probs = []
        moves_probs = []

        # スイッチ可能なポケモンの確率を設定
        for pokemon in battle._player_team.values():
            if pokemon.current_hp > 0 and not pokemon.active:
                commands.append(f"/switch {pokemon.ident.split(':')[1]}")
                switch_probs.append(1.0)
            else:
                switch_probs.append(0.0)

        # 技の確率を設定
        active_pokemon = battle.active_pokemon
        if active_pokemon:
            for move_name, move in active_pokemon.moves.items():
                if move.pp > 0:
                    commands.append(f"/choose move {move_name}")
                    moves_probs.append(1.0)  # 通常技の確率を1に設定
                else:
                    moves_probs.append(0.0)

        probs = []
        for p in switch_probs:
            probs.append(p)

        for p in moves_probs:
            probs.append(p)

        probs = np.array(probs)
        
        if sum(probs) > 0:
            probs /= sum(probs)
            choice = choices([i for i, val in enumerate(probs)], probs)[0]
            try:
                if commands[choice]:
                    print(f"[DEBUG] Sending command: {commands[choice]}")  # デバッグログを追加
                    await self.send_message(
                        message=commands[choice],
                        message_2=str(battle.turn_sent),
                        room=battle.battle_tag,
                    )
                    return
            except (ValueError, IndexError) as e:
                print(f"Error in random_move: {e}")
                print(f"probs: {probs}")
                print(f"commands: {commands}")
                print(f"switch_probs: {switch_probs}")
                print(f"moves_probs: {moves_probs}")
        
        # デフォルトの行動として最初の有効な技を使用
        if active_pokemon:
            for move_name, move in active_pokemon.moves.items():
                if move.pp > 0:
                    print(f"[DEBUG] Sending default move: {move_name}")  # デバッグログを追加
                    await self.send_message(
                        message=f"/choose move {move_name}",
                        message_2=str(battle.turn_sent),
                        room=battle.battle_tag,
                    )
                    return

    async def run(self) -> None:
        print(f"[DEBUG] Starting run() for {self.username} in {self.mode} mode")
        if self.mode == "one_challenge":
            while not self.logged_in:
                await asyncio.sleep(0.1)
            await self.challenge(self.to_target, self.format)
        elif self.mode == "challenge":
            while self.total_battles < self.target_battles:
                print(f"[DEBUG] {self.username} run loop: logged_in={self.logged_in}, total_battles={self.total_battles}, target_battles={self.target_battles}, current_battles={self.current_battles}")
                if not self.logged_in:
                    print(f"[DEBUG] {self.username} waiting for login...")
                    await asyncio.sleep(0.1)
                    continue
                if self.can_accept_challenge:
                    print(f"[INFO] Sending challenge to {self.to_target}")
                    self._waiting_start = True
                    await self.challenge(self.to_target, self.format)
                    self._waiting_start = False  # チャレンジ送信後にフラグをリセット
                elif not self.can_accept_challenge:
                    print(f"[DEBUG] {self.username} cannot accept challenge now")
                await asyncio.sleep(1)  # チャレンジの間隔を1秒に設定
        elif self.mode == "battle_online":
            # TODO: implement
            pass
        elif self.mode == "wait":
            print(f"[DEBUG] {self.username} in wait mode, waiting for login...")
            while not self.logged_in:
                await asyncio.sleep(0.1)
            print(f"[DEBUG] {self.username} logged in, waiting for challenges...")
        else:
            raise ValueError(
                f"Unknown mode {self.mode}. Please specify one of the following modes: 'challenge', 'wait', 'battle_online'"
            )

    @abstractmethod
    def select_move(self, battle: Battle, *, trapped: bool = False) -> str:
        pass

    @property
    def actions(self):
        return self._actions

    @property
    def can_accept_challenge(self) -> bool:
        can_accept = (not self._waiting_start) and (
            self.current_battles < self.max_concurrent_battles
            and self.total_battles < self.target_battles
        )
        print(f"[DEBUG] {self.username} can_accept_challenge: {can_accept} (waiting_start: {self._waiting_start}, current_battles: {self.current_battles}, total_battles: {self.total_battles})")
        return can_accept

    @property
    def should_die(self) -> bool:
        should_die = (self.total_battles > self.target_battles) or (
            self.total_battles == self.target_battles and self.current_battles == 0
        )
        print(f"[DEBUG] {self.username} should_die check: {should_die} (total_battles: {self.total_battles}, target_battles: {self.target_battles}, current_battles: {self.current_battles})")
        return should_die


    @property
    def observations(self):
        return self._observations

    @property
    def winning_moves_data(self):
        data = {"observation": [], "action": []}
        for battle_id in self.wins.keys():
            if self.wins[battle_id]:
                for observation, action in zip(self.observations[battle_id], self.actions[battle_id]):
                    data["observation"].append(observation)
                    data["action"].append(action)
        return data
        
    @property
    def wins(self):
        return self._wins

    @property
    def winning_rate(self):
        return sum(self._wins.values())/len(self._wins.values())