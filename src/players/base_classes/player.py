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
            
            # バトルタグを取得
            battle_tag = split_message[0]
            if battle_tag.startswith(">"):
                battle_tag = battle_tag[1:]
            
            # 現在のバトルを取得
            current_battle = self.battles.get(battle_tag)
            
            # バトル関連メッセージのログ出力（playerメッセージのみ）
            if len(split_message) > 1 and split_message[1] == "player":
                print(f"[DEBUG] Player message for {self.username}: {split_message}")
                if len(split_message) > 3 and split_message[3] == self.username.lower():
                    print(f"[DEBUG] This player message is for us: {self.username}")
                    # このボットのplayer roleを設定
                    if current_battle:
                        if len(split_message) > 2 and split_message[2] == "p1":
                            current_battle.player_is_p1()
                            print(f"[DEBUG WARN] Setting player role: p1 for {self.username}")
                        elif len(split_message) > 2 and split_message[2] == "p2":
                            current_battle.player_is_p2()
                            print(f"[DEBUG WARN] Setting player role: p2 for {self.username}")
                else:
                    print(f"[DEBUG] This player message is NOT for us: {split_message[3] if len(split_message) > 3 else 'N/A'} vs {self.username.lower()}")
            
            # バトル進行メッセージのログ出力
            if len(split_message) > 1 and split_message[1] in ["turn", "move", "switch", "win", "tie"]:
                print(f"[DEBUG] Battle progress for {self.username}: {split_message[1]} - {split_message}")
            
            # すべてのplayerメッセージをログ出力（デバッグ用）
            if len(split_message) > 1 and split_message[1] == "player":
                print(f"[DEBUG] ALL PLAYER MESSAGE for {self.username}: {split_message}")
            
            # p2の場合は手動でplayer roleを設定
            if (len(split_message) > 1 and split_message[1] == "player" and 
                len(split_message) > 2 and split_message[2] == "p1" and
                len(split_message) > 3 and split_message[3] != self.username.lower()):
                print(f"[DEBUG] Detected p1 message for other player, setting p2 role for {self.username}")
                if current_battle and not current_battle.player_role:
                    current_battle.player_is_p2()
                    print(f"[DEBUG] Manually set player role: p2 for {self.username}")
            
            # バトル開始後の遅延設定（p2の場合）
            if (len(split_message) > 1 and split_message[1] == "turn" and
                len(split_message) > 2 and split_message[2] == "1"):
                if current_battle and not current_battle.player_role:
                    print(f"[DEBUG] Turn 1 detected, setting p2 role for {self.username}")
                    current_battle.player_is_p2()
            
            # バトル開始時の自動設定（p2の場合）
            if (len(split_message) > 1 and split_message[1] == "start"):
                if current_battle and not current_battle.player_role:
                    print(f"[DEBUG] Battle start detected, setting p2 role for {self.username}")
                    current_battle.player_is_p2()
            
            # バトル参加時の自動設定（p2の場合）
            if (len(split_message) > 1 and split_message[1] == "j" and
                len(split_message) > 2 and "☆" in split_message[2]):
                if current_battle and not current_battle.player_role:
                    print(f"[DEBUG] Battle join detected, setting p2 role for {self.username}")
                    current_battle.player_is_p2()
            
            # バトル作成時の自動設定（p2の場合）
            if (len(split_message) > 1 and split_message[1] == "init" and
                len(split_message) > 2 and split_message[2] == "battle"):
                if current_battle and not current_battle.player_role:
                    print(f"[DEBUG] Battle init detected, setting p2 role for {self.username}")
                    current_battle.player_is_p2()
            
            # バトル参加時の自動設定（p2の場合）- より詳細な条件
            if (len(split_message) > 1 and split_message[1] == "j"):
                if current_battle and not current_battle.player_role:
                    print(f"[DEBUG] Join message detected, setting p2 role for {self.username}")
                    current_battle.player_is_p2()
            
            # p1の場合は手動でplayer roleを設定
            if (len(split_message) > 1 and split_message[1] == "player" and 
                len(split_message) > 2 and split_message[2] == "p2" and
                len(split_message) > 3 and split_message[3] != self.username.lower()):
                print(f"[DEBUG] Detected p2 message for other player, setting p1 role for {self.username}")
                if current_battle and not current_battle.player_role:
                    current_battle.player_is_p1()
                    print(f"[DEBUG] Manually set player role: p1 for {self.username}")
            
            # p2の場合は手動でplayer roleを設定（より詳細な条件）
            if (len(split_message) > 1 and split_message[1] == "player" and 
                len(split_message) > 2 and split_message[2] == "p1" and
                len(split_message) > 3 and split_message[3] != self.username.lower()):
                print(f"[DEBUG] Detected p1 message for other player, setting p2 role for {self.username}")
                if current_battle and not current_battle.player_role:
                    current_battle.player_is_p2()
                    print(f"[DEBUG] Manually set player role: p2 for {self.username}")
            
            # p1の場合は手動でplayer roleを設定（より詳細な条件）
            if (len(split_message) > 1 and split_message[1] == "player" and 
                len(split_message) > 2 and split_message[2] == "p2" and
                len(split_message) > 3 and split_message[3] != self.username.lower()):
                if current_battle and not current_battle.player_role:
                    current_battle.player_is_p1()
                    print(f"[DEBUG] Manually set player role: p1 for {self.username}")
            
            # バトル開始時の自動設定（p1の場合）
            if (len(split_message) > 1 and split_message[1] == "start"):
                if current_battle and not current_battle.player_role:
                    print(f"[DEBUG] Battle start detected, setting p1 role for {self.username}")
                    current_battle.player_is_p1()
            
            # バトル参加時の自動設定（p1の場合）
            if (len(split_message) > 1 and split_message[1] == "j"):
                if current_battle and not current_battle.player_role:
                    print(f"[DEBUG] Join message detected, setting p1 role for {self.username}")
                    current_battle.player_is_p1()
            
            # バトル参加時の自動設定（p2の場合）
            if (len(split_message) > 1 and split_message[1] == "j"):
                if current_battle and not current_battle.player_role:
                    print(f"[DEBUG] Join message detected, setting p2 role for {self.username}")
                    current_battle.player_is_p2()
            

            

            

            battle_info = split_message[0].split("-")
            if len(battle_info) > 2:
                if battle_info[2] not in self.battles:
                    print(f"[DEBUG] Creating new battle {battle_info[2]} for {self.username}")
                    self.battles[battle_info[2]] = Battle(battle_info[2], self.username)
                    self.current_battles += 1
                    if "2" in self.username.lower():
                        print(f"Battle %3d / %3d started" % (len(self.battles), self.target_battles))
                if battle_info[2] in self.battles:
                    current_battle = self.battles[battle_info[2]]
                    print(f"[DEBUG] Using existing battle {battle_info[2]} for {self.username}")
            else:
                # battle_infoの要素数が足りない場合は何もしない
                print(f"[DEBUG] Invalid battle_info format: {battle_info}")
                return

            # Send move
            if len(split_message) > 1:
                # print(f"[DEBUG] Processing message: {'|'.join(split_message)}")  # デバッグログを追加
                if len(split_message) > 2 and split_message[1] == "request":
                    if split_message[2] and current_battle is not None:
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
                elif len(split_message) > 2 and split_message[1] == "callback" and split_message[2] == "trapped" and current_battle is not None:
                    await self.select_save_move(current_battle, trapped=True)
                elif len(split_message) > 2 and split_message[1] == "error" and current_battle is not None:
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
                    len(split_message) > 3 and
                    split_message[1] == "player"
                    and len(split_message) > 3
                    and split_message[3] == self.username.lower()
                    and current_battle is not None
                ):
                    print(f"[DEBUG WARN] Setting player role: {split_message[2]} for {self.username}")
                    if len(split_message) > 2 and split_message[2] == "p2":
                        current_battle.player_is_p2()
                    elif len(split_message) > 2 and split_message[2] == "p1":
                        current_battle.player_is_p1()

                    if current_battle.is_ready:
                        await self.select_save_move(current_battle)
                elif (
                    len(split_message) > 3 and
                    split_message[1] == "player"
                    and len(split_message) > 3
                    and split_message[3] == self.username.lower()
                    and current_battle is None
                ):
                    print(f"[DEBUG ERROR] Player role message received but no current_battle for {self.username}")
                    print(f"[DEBUG] Available battles: {list(self.battles.keys())}")
                elif len(split_message) > 1 and split_message[1] == "player":
                    print(f"[DEBUG] Received player message: {split_message}")
                    if len(split_message) > 3 and split_message[3] == self.username.lower():
                        print(f"[DEBUG] This is for us: {self.username}")
                        if current_battle is not None:
                            if len(split_message) > 2 and split_message[2] == "p2":
                                current_battle.player_is_p2()
                                print(f"[DEBUG] Set p2 for {self.username}")
                            elif len(split_message) > 2 and split_message[2] == "p1":
                                current_battle.player_is_p1()
                                print(f"[DEBUG] Set p1 for {self.username}")
                        else:
                            print(f"[DEBUG] No current_battle for {self.username}")
                    else:
                        print(f"[DEBUG] Player message not for us: {split_message[3] if len(split_message) > 3 else 'N/A'} vs {self.username.lower()}")
                

                

                


                elif len(split_message) > 2 and split_message[1] == "win" and current_battle is not None:
                    if len(split_message) > 2:
                        current_battle.won_by(split_message[2])
                        self._wins[current_battle.battle_num] = int(self.username.lower() == split_message[2])
                        self.current_battles -= 1
                        self.total_battles += 1
                        print(f"[DEBUG] {self.username} battle ended: total_battles={self.total_battles}, current_battles={self.current_battles}")

                        await self.leave_battle(current_battle)
                elif len(split_message) > 2 and split_message[1] == "turn" and current_battle is not None:
                    print(f"[DEBUG] Turn {split_message[2]} for battle {current_battle.battle_tag}")  # デバッグログを追加
                    if current_battle.is_ready:
                        await self.select_save_move(current_battle)
                else:
                    if current_battle is not None:
                        # parse_messageに渡す前に最低限の長さチェック
                        if len(split_message) > 1:
                            try:
                                current_battle.parse_message(split_message)
                            except Exception as e:
                                print(f"[ERROR] Error in parse_message: {e}")
                                print(f"[DEBUG] Message that caused error: {'|'.join(split_message)}")
        except Exception as e:
            import traceback
            print(f"[ERROR] Unexpected error in battle method for {self.username}: {e}")
            print(f"[DEBUG] Message that caused error: {message}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")

    async def select_save_move(self, battle: Battle, *, trapped: bool = False) -> None:
        print(f"[DEBUG] Selecting move for battle {battle.battle_tag}")  # デバッグログを追加
        if battle.battle_num not in self._observations.keys():
            self._observations[battle.battle_num] = []
            self._actions[battle.battle_num] = []
        self._observations[battle.battle_num].append(battle.dic_state)
        print(f"[DEBUG] Calling select_move for {self.username}")
        print(f"[DEBUG] select_move method: {self.select_move.__qualname__}")
        action = await self.select_move(battle, trapped=trapped)
        room_tag = battle.battle_tag
        if not room_tag.startswith('>'):
            room_tag = '>' + room_tag
        print(f"[DEBUG] select_move returned for {self.username}: {action}")  # 選択した行動をログ出力
        if action is None:
            print(f"[DEBUG WARN] Action is None for {self.username}, this should not happen")
        self._actions[battle.battle_num].append(action)

    async def random_move(self, battle: Battle, *, trapped: bool = False) -> str:
        print(f"[DEBUG] random_move called for {self.username}")
        print(f"[DEBUG] available_moves: {getattr(battle, 'available_moves', None)}")
        print(f"[DEBUG] available_switches: {getattr(battle, 'available_switches', None)}")
        print(f"[DEBUG] active_pokemon: {getattr(battle, 'active_pokemon', None)}")
        if getattr(battle, 'active_pokemon', None):
            print(f"[DEBUG] active_pokemon.moves: {battle.active_pokemon.moves}")
        state = battle.dic_state
        commands = []
        switch_probs = []
        moves_probs = []

        for pokemon in battle._player_team.values():
            if pokemon.current_hp is not None and pokemon.current_hp > 0 and not pokemon.active:
                commands.append(f"/switch {pokemon.ident.split(':')[1]}")
                switch_probs.append(1.0)
            else:
                switch_probs.append(0.0)

        active_pokemon = battle.active_pokemon
        if active_pokemon:
            for move_name, move in active_pokemon.moves.items():
                if move.pp > 0:
                    commands.append(f"/choose move {move_name}")
                    moves_probs.append(1.0)
                else:
                    moves_probs.append(0.0)

        probs = []
        for p in switch_probs:
            probs.append(p)
        for p in moves_probs:
            probs.append(p)

        if len(commands) < len(probs):
            commands += [""] * (len(probs) - len(commands))
        elif len(commands) > len(probs):
            commands = commands[:len(probs)]

        probs = np.array(probs)
        if sum(probs) > 0:
            probs /= sum(probs)
            choice = choices([i for i, val in enumerate(probs)], probs)[0]
            try:
                if 0 <= choice < len(commands) and commands[choice]:
                    print(f"[DEBUG] Sending command: {commands[choice]}")
                    await self.send_room_message(
                        message=commands[choice],
                        room=battle.battle_tag,
                    )
                    print(f"[DEBUG] Command sent successfully for {self.username}")
                    return commands[choice]
            except (ValueError, IndexError) as e:
                import traceback
                print(f"[ERROR] {type(e).__name__} in random_move: {e}")
                print(f"[DEBUG] choice: {choice}, len(commands): {len(commands)}, len(probs): {len(probs)}")
                print(f"[DEBUG] commands: {commands}")
                print(f"[DEBUG] probs: {probs}")
                print(f"[DEBUG] switch_probs: {switch_probs}")
                print(f"[DEBUG] moves_probs: {moves_probs}")
                print(f"[DEBUG] Traceback: {traceback.format_exc()}")

        if active_pokemon:
            for move_name, move in active_pokemon.moves.items():
                if move.pp > 0:
                    print(f"[DEBUG] Sending default move: {move_name}")
                    await self.send_room_message(
                        message=f"/choose move {move_name}",
                        room=battle.battle_tag,
                    )
                    print(f"[DEBUG] Default move sent for {self.username}")
                    return f"/choose move {move_name}"

        print(f"[DEBUG] No valid moves found, sending pass for {self.username}")
        await self.send_room_message(
            message="pass",
            room=battle.battle_tag,
        )
        print(f"[DEBUG] Pass command sent for {self.username}")
        print(f"[DEBUG] random_move returning: pass")
        return "pass"

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

    async def select_move(self, battle: Battle, *, trapped: bool = False) -> str:
        print(f"[DEBUG] Default select_move called for {self.username}, using random_move")
        result = await self.random_move(battle, trapped=trapped)
        print(f"[DEBUG] Default select_move returning: {result}")
        return result

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
        # print(f"[DEBUG] {self.username} should_die check: {should_die} (total_battles: {self.total_battles}, target_battles: {self.target_battles}, current_battles: {self.current_battles})")
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