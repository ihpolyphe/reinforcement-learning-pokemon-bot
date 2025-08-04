import asyncio
import json
import random
import re

import gymnasium as gym
import numpy as np
import websockets
from gymnasium import spaces

from .battle import Battle


class SyncShowdownClient:
    def choose_action_from_request(self, request_str, select_type="random"):
        """
        battle_DQN.pyのロジックを参考に、request文字列から適切なコマンドを返す
        select_type: "random" or "max_damage"
        """
        try:
            if "|request|" not in request_str:
                return None
            request_json = request_str.split("|request|")[1]
            request = json.loads(request_json)
            # 技選択
            if "active" in request:
                moves = request["active"][0]["moves"]
                valid_moves = [move for move in moves if not move.get("disabled", False)]
                if select_type == "max_damage":
                    if valid_moves:
                        move = max(valid_moves, key=lambda x: x.get("basePower", 0))
                        move_id = move["id"]
                        target = move.get("target", "")
                        if target in ["normal", "adjacentFoe", "adjacentAllyOrSelf", "adjacentAlly", "adjacentFoeOrAlly"]:
                            return f"{self.battle_tag}|/choose move {move_id} 1\n"
                        else:
                            return f"{self.battle_tag}|/choose move {move_id}\n"
                else:
                    # random
                    import random
                    trapped = request["active"][0].get("trapped", False)
                    switch_choices = []
                    if not trapped and "side" in request:
                        side_pokemon = request["side"]["pokemon"]
                        for i, poke in enumerate(side_pokemon):
                            if not poke.get("active", False) and not poke["condition"].endswith("fnt"):
                                switch_choices.append(i + 1)
                    choices = []
                    for move in valid_moves:
                        choices.append(("move", move, False))
                    for switch_index in switch_choices:
                        choices.append(("switch", switch_index, False))
                    if choices:
                        action, value, tera = random.choice(choices)
                        if action == "move":
                            move_id = value["id"]
                            target = value.get("target", "")
                            if target in ["normal", "adjacentFoe", "adjacentAllyOrSelf", "adjacentAlly", "adjacentFoeOrAlly"]:
                                return f"{self.battle_tag}|/choose move {move_id} 1\n"
                            else:
                                return f"{self.battle_tag}|/choose move {move_id}\n"
                        elif action == "switch":
                            return f"{self.battle_tag}|/choose switch {value}\n"
            # 交代要求
            elif "forceSwitch" in request:
                side_pokemon = request["side"]["pokemon"]
                for i, poke in enumerate(side_pokemon):
                    if not poke.get("active", False) and not poke["condition"].endswith("fnt"):
                        return f"{self.battle_tag}|/choose switch {i+1}\n"
                # 交代できるポケモンがいない場合
                return None
        except Exception as e:
            print(f"[choose_action_from_request] error: {e}")
            return None
    @staticmethod
    def start_battles_concurrently(client1, client2):
        """
        2つのSyncShowdownClientのstart_battleを同じイベントループで同時に非同期で進める
        """
        async def run_both():
            await asyncio.gather(
                client1._start_battle(),
                client2._start_battle()
            )
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(run_both())
    """
    Showdownサーバーと同期的にやりとりするラッパークラス
    """
    def __init__(self, username, password, opponent, is_challenger, battle_format):
        self.username = username
        self.password = password
        self.opponent = opponent
        self.is_challenger = is_challenger
        self.battle_format = battle_format
        self.websocket = None
        self.battle_tag = None
        self.last_response = None
        # asyncioのグローバルイベントループを使う（必ずget_event_loopのみ）
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        self.joined_battle = False
        self.logged_in = False
        self.challenge_sent = False
        self.accept_sent = False

    def start_battle(self):
        self.loop.run_until_complete(self._start_battle())

    async def _start_battle(self):
        uri = "ws://127.0.0.1:8000/showdown/websocket"
        # WebSocket接続をバトル中維持するため、インスタンス変数に保持
        self.websocket = await websockets.connect(uri)
        websocket = self.websocket
        # ログイン
        trn_msg = f"|/trn {self.username},{self.password}\n"
        print(f"[SyncShowdownClient] 送信: {trn_msg.strip()}")
        await websocket.send(trn_msg)
        while True:
            resp = await websocket.recv()
            print(f"[SyncShowdownClient] 受信: {resp}")
            self.last_response = resp
            # ログイン完了判定
            if not self.logged_in and f"|updateuser| {self.username}" in resp:
                self.logged_in = True
                print(f"[SyncShowdownClient] ログイン完了: {self.username}")
            # チャレンジ送信（チャレンジャーのみ）
            if self.logged_in and self.is_challenger and not self.challenge_sent:
                challenge_msg = f"|/challenge {self.opponent}, {self.battle_format}\n"
                print(f"[SyncShowdownClient] 送信: {challenge_msg.strip()}")
                await websocket.send(challenge_msg)
                self.challenge_sent = True
            # チャレンジ受諾（チャレンジされた側のみ）
            if self.logged_in and not self.is_challenger and not self.accept_sent:
                if f"|pm| {self.opponent}| {self.username}|/challenge" in resp:
                    accept_msg = f"|/accept {self.opponent}\n"
                    print(f"[SyncShowdownClient] 送信: {accept_msg.strip()}")
                    await websocket.send(accept_msg)
                    self.accept_sent = True
            # battle_tag（ルーム名）の取得
            if self.battle_tag is None:
                m = re.search(r'"(battle-[^"]+)":"\\?\[Gen', resp)
                if m:
                    self.battle_tag = m.group(1)
                    print(f"[SyncShowdownClient] ルーム名取得: {self.battle_tag}")
                m2 = re.search(r'/battle-([a-z0-9\-]+)', resp)
                if m2:
                    self.battle_tag = m2.group(1)
                    print(f"[SyncShowdownClient] ルーム名取得: {self.battle_tag}")
            # ルームにjoin
            if self.battle_tag and not self.joined_battle:
                join_msg = f"|/join {self.battle_tag}\n"
                print(f"[SyncShowdownClient] 送信: {join_msg.strip()}")
                await websocket.send(join_msg)
                self.joined_battle = True
            # バトル開始まで抜けない
            if self.battle_tag and self.joined_battle:
                print(f"[SyncShowdownClient] バトル準備完了: {self.battle_tag}")
                break

    def close(self):
        # バトル終了時にWebSocketをクローズ
        if self.websocket is not None:
            self.loop.run_until_complete(self.websocket.close())
            self.websocket = None

    def send_action(self, action_cmd):
        self.loop.run_until_complete(self._send_action(action_cmd))

    async def _send_action(self, action_cmd):
        if not self.websocket or not self.battle_tag:
            return
        await self.websocket.send(action_cmd)
        # 1ターン分のレスポンスを受信
        while True:
            resp = await self.websocket.recv()
            self.last_response = resp
            # ターン進行またはバトル終了でbreak
            if "|turn|" in resp or "|win|" in resp or "|tie|" in resp:
                break

    def get_last_response(self):
        return self.last_response

class PokemonBattleEnv(gym.Env):
    def __init__(self):
        print("[LOG] PokemonBattleEnv.__init__ start")
        super().__init__()
        # 最大行動数: 技4+交代5=9（6on6想定）
        self.max_moves = 4
        self.max_switches = 5
        self.action_space = spaces.Discrete(self.max_moves + self.max_switches)
        # 特徴量10次元に合わせてshapeを修正
        self.observation_space = spaces.Box(low=0, high=1, shape=(10,), dtype=np.float32)
        self.battle = None
        self.state = None
        self.client = None
        self.valid_actions = []
        print("[LOG] PokemonBattleEnv.__init__ end")

    def reset(self, seed=None, options=None):
        print("[LOG] PokemonBattleEnv.reset start")
        super().reset(seed=seed)
        print("[LOG] SyncShowdownClient生成 (bot1)")
        self.client = SyncShowdownClient(
            username="inf581_bot_1",
            password="INF581_BOT_1",
            opponent="inf581_bot_2",
            is_challenger=True,
            battle_format="gen9randombattle"
        )
        print("[LOG] SyncShowdownClient生成 (bot2)")
        self.client2 = SyncShowdownClient(
            username="inf581_bot_2",
            password="INF581_BOT_2",
            opponent="inf581_bot_1",
            is_challenger=False,
            battle_format="gen9randombattle"
        )
        print("[LOG] start_battle呼び出し前 (両bot並列)")
        SyncShowdownClient.start_battles_concurrently(self.client, self.client2)
        print("[LOG] start_battle呼び出し後")
        self.battle = Battle(battle_tag=self.client.battle_tag or "test-0001", player_name="inf581_bot_1")
        print("[LOG] Battleインスタンス生成後")
        # 初期状態反映（レスポンスをparse）
        if self.client.get_last_response():
            print("[LOG] parse_message呼び出し前")
            self.battle.parse_message(self.client.get_last_response().split("|"))
            print("[LOG] parse_message呼び出し後")
        self.state = self._encode_state(self.battle)
        print("[LOG] _encode_state呼び出し後")
        self.valid_actions = self._make_valid_actions(self.battle)
        print("[LOG] reset end")
        return self.state, {}

    def step(self, action_idx):
        print(f"[LOG] step start action_idx={action_idx}")
        # bot1の行動
        # サーバーからのリクエストを取得
        req1 = self.client.get_last_response()
        action_cmd = None
        if req1 and "|request|" in req1:
            action_cmd = self.client.choose_action_from_request(req1, select_type="max_damage")
        if not action_cmd:
            # fallback: 有効なアクション
            if action_idx < len(self.valid_actions):
                action_cmd = self.valid_actions[action_idx]
            else:
                action_cmd = self.valid_actions[0]
        print(f"[LOG] send_action (bot1): {action_cmd}")
        self.client.send_action(action_cmd)

        # bot2の行動（requestに応じて）
        action_cmd2 = None
        if hasattr(self, 'client2') and self.client2:
            req2 = self.client2.get_last_response()
            if req2 and "|request|" in req2:
                action_cmd2 = self.client2.choose_action_from_request(req2, select_type="random")
            if not action_cmd2:
                action_cmd2 = f"{self.client2.battle_tag or 'test-0001'}|/choose move 1\n"
            print(f"[LOG] send_action (bot2): {action_cmd2}")
            self.client2.send_action(action_cmd2)

        # サーバーからのレスポンスをparseしてBattleに反映
        if self.client.get_last_response():
            print("[LOG] step parse_message呼び出し前")
            self.battle.parse_message(self.client.get_last_response().split("|"))
            print("[LOG] step parse_message呼び出し後")
        self.state = self._encode_state(self.battle)
        print("[LOG] step _encode_state呼び出し後")
        reward = self._calc_reward(self.battle)
        terminated = self._is_done(self.battle)
        truncated = False
        self.valid_actions = self._make_valid_actions(self.battle)
        # バトル終了時にWebSocketをクローズ
        if terminated:
            if hasattr(self.client, 'close'):
                self.client.close()
            if hasattr(self, 'client2') and hasattr(self.client2, 'close'):
                self.client2.close()
        print("[LOG] step end")
        info = {"valid_actions": self.valid_actions}
        return self.state, reward, terminated, truncated, info

    def _make_valid_actions(self, battle):
        # 有効な技・交代先をコマンドリスト化
        actions = []
        # 技
        for i, move in enumerate(getattr(battle, "available_moves", [])[:self.max_moves]):
            actions.append(f"{battle.battle_tag}|/choose move {i+1}\n")
        # 交代
        for i, sw in enumerate(getattr(battle, "available_switches", [])[:self.max_switches]):
            actions.append(f"{battle.battle_tag}|/choose switch {i+1}\n")
        if not actions:
            actions.append(f"{battle.battle_tag}|/choose move 1\n")  # fallback
        return actions

    def _encode_state(self, battle):
        # HP割合・残ポケ数・勝敗フラグ・技情報でエンコード（拡張版）
        try:
            dic = battle.dic_state
            active = dic["active"]
            opponent_active = dic["opponent_active"]
            my_hp = float(active.get("hp", 100)) / float(active.get("maxhp", 100))
            opp_hp = float(opponent_active.get("hp", 100)) / float(opponent_active.get("maxhp", 100))
            my_alive = sum([1 for p in dic["back"] if not p.get("status", "").endswith("fnt")]) + (1 if not active.get("status", "").endswith("fnt") else 0)
            opp_alive = sum([1 for p in dic["opponent_back"] if not p.get("status", "").endswith("fnt")]) + (1 if not opponent_active.get("status", "").endswith("fnt") else 0)
            weather = [1.0 if v else 0.0 for v in dic["weather"].values()][:2]
            won = 1.0 if getattr(battle, "won", False) else 0.0
            # 技情報
            moves = getattr(battle, "available_moves", [])
            num_moves = len(moves) / 4.0  # 最大4で正規化
            max_power = max([m.get("basePower", 0) for m in moves], default=0) / 200.0  # 200で正規化
            total_pp = sum([m.get("pp", 0) for m in moves]) / 100.0  # 100で正規化
            obs = np.array([
                my_hp, opp_hp, my_alive/6, opp_alive/6,
                num_moves, max_power, total_pp,
                weather[0] if len(weather)>0 else 0.0,
                weather[1] if len(weather)>1 else 0.0,
                won
            ], dtype=np.float32)
            return obs
        except Exception as e:
            return np.zeros(10, dtype=np.float32)

    def _calc_reward(self, battle):
        # 勝敗重視＋被ダメ抑制（簡易）
        try:
            dic = battle.dic_state
            active = dic["active"]
            opponent_active = dic["opponent_active"]
            my_hp = float(active.get("hp", 100)) / float(active.get("maxhp", 100))
            opp_hp = float(opponent_active.get("hp", 100)) / float(opponent_active.get("maxhp", 100))
            # 勝利:+1, 敗北:-1, ターンごとに被ダメ減少をペナルティ
            if getattr(battle, "won", False):
                return 1.0
            if getattr(battle, "_finished", False) and not getattr(battle, "won", False):
                return -1.0
            # 被ダメ抑制: HP減少分をマイナス
            return (opp_hp - my_hp)
        except Exception as e:
            return 0.0

    def _is_done(self, battle):
        # バトル終了判定
        return getattr(battle, "_finished", False) 