import json
import requests
import websockets

from abc import ABC, abstractmethod
from asyncio import Lock
from environment.battle import Battle


class PlayerNetwork(ABC):
    """
    Network interface of a player.
    
    In charge of communicating with the pokemon showdown server.
    """

    def __init__(
        self,
        username: str,
        password: str,
        *,
        authentification_address: str,
        avatar: int,
        log_messages_in_console: bool,
        server_address: str,
        to_challenge: str = None,
        format: str = "gen9randombattle",
    ) -> None:
        """
        Initialises interface.
        """

        if authentification_address is None:
            raise AttributeError(
                "Unspecified authentification address. Please specify an authentification address."
            )

        self._authentification_address = authentification_address
        self._avatar = avatar
        self._log_messages_in_console = log_messages_in_console
        self._logged_in = False
        self._password = password
        self._server_address = server_address
        self._username = username
        self._waiting_start = False
        self._to_challenge = to_challenge
        self._format = format

        self._lock = Lock()

    async def _log_in(self, conf_1: str, conf_2: str) -> None:
        """
        Log in player to specified username.
        conf_1 and conf_2 are confirmation strings received upon server access.
        They are needed to log in.
        """
        print(f"[DEBUG] Attempting login for {self.username}")
        await self.send_message(f"/trn {self.username},0")
        print(f"[DEBUG] Sent /trn command for {self.username}")
        # If there is an avatar to select, let's select it !
        if self._avatar:
            print(f"[DEBUG] Setting avatar {self._avatar} for {self.username}")
            await self.change_avatar(self._avatar)
        print(f"[DEBUG] Login process completed for {self.username}")

    async def accept_challenge(self, user: str) -> None:
        if self.can_accept_challenge:
            self._waiting_start = True
            await self.send_message(f"/accept {user}")

    async def leave_battle(self, battle: Battle):
        await self.send_message("/leave", room=battle.battle_tag)

    async def challenge(self, player=None, format=None):
        if not self.logged_in:
            return

        if player and format:
            print(f"[DEBUG] Sending challenge command: /challenge {player}, {format}")
            await self.send_message(f"/challenge {player}, {format}")
        else:
            print(
                f"No player or format specified in call to 'challenge' from {self}\nplayer: {player}\nformat: {format}"
            )
            raise ValueError(
                f"No player or format specified in call to 'challenge' from {self}\nplayer: {player}\nformat: {format}"
            )

    async def change_avatar(self, avatar_id: str) -> None:
        await self.send_message(f"/avatar {avatar_id}")

    async def listen(self) -> None:
        # try:
        async with websockets.connect(self.websocket_address) as websocket:
            self._websocket = websocket
            while not self.should_die:
                # try:
                message = await websocket.recv()
                if self._log_messages_in_console:
                    print(f"\n{self.username} << {message}")
                await self.manage_message(message)
                # except websockets.exceptions.ConnectionClosedOK:
                #     print(f"[INFO] Connection closed normally for {self.username}")
                #     break
                # except websockets.exceptions.ConnectionClosedError as e:
                #     print(f"[ERROR] Connection closed unexpectedly for {self.username}: {e}")
                #     break
                # except Exception as e:
                #     print(f"[ERROR] Unexpected error in listen loop for {self.username}: {e}")
                #     break
        # except Exception as e:
        #     print(f"[ERROR] Failed to establish WebSocket connection for {self.username}: {e}")
        # finally:
        #     print(f"[INFO] Listen loop ended for {self.username}")

    async def manage_message(self, message: str) -> None:
        """
        Parse and manage responses to incoming messages.
        """
        if not message or not isinstance(message, str):
            print(f"[WARNING] Invalid message received: {message}")
            return

        split_message = message.split("|")
        if not split_message:
            print("[WARNING] Empty message after split")
            return

        print(f"[DEBUG] Received message split_message[0]: {split_message[0]}")
        
        # メッセージの長さを確認
        if len(split_message) > 1:
            print(f"[DEBUG] Received message split_message[1]: {split_message[1]}")
        else:
            print("[DEBUG] Message too short, skipping")
            return
            
        if len(split_message) > 2:
            print(f"[DEBUG] Received message split_message[2]: {split_message[2]}")
        if len(split_message) > 3:
            print(f"[DEBUG] Received message split_message[3]: {split_message[3]}")
        if len(split_message) > 4:
            print(f"[DEBUG] Received message split_message[4]: {split_message[4]}")
            
        # challstr confirms that we are connected to the server
        # we can therefore login
        if split_message[1] == "challstr":
            if len(split_message) < 4:
                print("[ERROR] Invalid challstr message format")
                return
            conf_1, conf_2 = split_message[2], split_message[3]
            print(f"[DEBUG] Received challstr, attempting login for {self.username}")
            await self._log_in(conf_1, conf_2)

        elif split_message[1] == 'updateuser':
            if len(split_message) < 3:
                print("[ERROR] Invalid updateuser message format")
                return
            print(f"[DEBUG] Received updateuser: {split_message[2]}")
            if split_message[2].strip() == self.username:
                self._logged_in = True
                print(f"[INFO] Logged in as {self.username}")

        elif "updatechallenges" in split_message[1]:
            if len(split_message) < 3:
                print("[ERROR] Invalid updatechallenges message format")
                return
            try:
                response = json.loads(split_message[2])
                print(f"[DEBUG] Received challenges: {response}")
                for user, format in response.get("challengesFrom", {}).items():
                    if format == self.format:
                        print(f"[INFO] Accepting challenge from {user}")
                        await self.accept_challenge(user)
            except json.JSONDecodeError:
                print(f"[ERROR] Failed to parse challenges: {split_message[2]}")

        elif split_message[0].startswith('>battle'):
            self._waiting_start = False  # バトルが開始されたらチャレンジ待ち状態を解除
            await self.battle(message)
        elif split_message[1] == "popup":
            if len(split_message) < 3:
                print("[ERROR] Invalid popup message format")
                return
            print(f"[DEBUG] Received popup: {split_message[2]}")
            if "already challenging" in split_message[2]:
                self._waiting_start = False  # チャレンジが失敗したらチャレンジ待ち状態を解除
        elif split_message[1] == "pm":
            if len(split_message) < 4:
                print("[ERROR] Invalid pm message format")
                return
            print(f"[DEBUG] Received PM from {split_message[2]}: {split_message[3]}")
            # チャレンジメッセージの処理
            if len(split_message) > 4 and split_message[4].startswith("/challenge"):
                print(f"[INFO] Received challenge from {split_message[2]}")
                # チャレンジを受け取ったことを確認
                self._waiting_start = False
                # チャレンジを受け入れる
                await self.accept_challenge(split_message[2])
            # チャレンジ通知の処理
            elif len(split_message) > 4 and split_message[4].startswith("/log") and "wants to battle" in split_message[4]:
                print(f"[INFO] Received battle request from {split_message[2]}")
                # チャレンジを受け取ったことを確認
                self._waiting_start = False
                # チャレンジを受け入れる
                await self.accept_challenge(split_message[2])
        elif split_message[1] in ["updatesearch"]:
            pass
        else:
            print(f"UNMANAGED MESSAGE : {message}")

    async def send_message(
        self, message: str, room: str = "", message_2: str = None
    ) -> None:
        if message_2:
            to_send = "|".join([room, message, message_2])
        else:
            to_send = "|".join([room, message])
        if self._log_messages_in_console:
            print(f"\n{self.username} >> {to_send}")
        print(f"[DEBUG] Sending message: {to_send}")
        async with self._lock:
            await self._websocket.send(to_send)

    @property
    @abstractmethod
    def can_accept_challenge(self) -> bool:
        pass

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    @abstractmethod
    def should_die(self) -> bool:
        pass

    @property
    def username(self) -> str:
        return self._username

    @property
    def websocket_address(self) -> str:
        return f"ws://{self._server_address}/showdown/websocket"

    @property
    def format(self) -> str:
        return self._format
