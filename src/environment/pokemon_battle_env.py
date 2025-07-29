import gymnasium as gym
import numpy as np
from gymnasium import spaces
from .battle import Battle
import asyncio
import websockets
import json
import random
import re

class SyncShowdownClient:
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
        self.loop = asyncio.new_event_loop()
        self.joined_battle = False
        self.logged_in = False
        self.challenge_sent = False
        self.accept_sent = False

    def start_battle(self):
        self.loop.run_until_complete(self._start_battle())

    async def _start_battle(self):
        uri = "ws://127.0.0.1:8000/showdown/websocket"
        async with websockets.connect(uri) as websocket:
            self.websocket = websocket
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
        self.observation_space = spaces.Box(low=0, high=1, shape=(8,), dtype=np.float32)
        self.battle = None
        self.state = None
        self.client = None
        self.valid_actions = []
        print("[LOG] PokemonBattleEnv.__init__ end")

    def reset(self, seed=None, options=None):
        print("[LOG] PokemonBattleEnv.reset start")
        super().reset(seed=seed)
        print("[LOG] SyncShowdownClient生成")
        self.client = SyncShowdownClient(
            username="inf581_bot_1",
            password="INF581_BOT_1",
            opponent="inf581_bot_2",
            is_challenger=True,
            battle_format="gen9randombattle"
        )
        print("[LOG] start_battle呼び出し前")
        self.client.start_battle()
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
        # action_idx→コマンド変換
        if action_idx < len(self.valid_actions):
            action_cmd = self.valid_actions[action_idx]
        else:
            action_cmd = self.valid_actions[0]  # fallback
        print(f"[LOG] send_action: {action_cmd}")
        self.client.send_action(action_cmd)
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