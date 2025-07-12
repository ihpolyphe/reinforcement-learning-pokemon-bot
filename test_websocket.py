import asyncio
import websockets
import json
import re

async def showdown_bot(username, password, opponent, is_challenger, battle_format):
    uri = "ws://127.0.0.1:8000/showdown/websocket"
    battle_tag = None
    joined_battle = False
    turn_count = 0
    logged_in = False
    challenge_sent = False
    accept_sent = False

    async with websockets.connect(uri) as websocket:
        # ログイン
        trn_msg = f"|/trn {username},{password}\n"
        print(f"[{username}] 送信: {trn_msg.strip()}")
        await websocket.send(trn_msg)

        while True:
            resp = await websocket.recv()
            print(f"[{username}] 受信: {resp}")

            # ログイン完了判定
            if not logged_in and f"|updateuser| {username}" in resp:
                logged_in = True
                print(f"[{username}] ログイン完了")

            # チャレンジ送信（チャレンジャーのみ）
            if logged_in and is_challenger and not challenge_sent:
                challenge_msg = f"|/challenge {opponent}, {battle_format}\n"
                print(f"[{username}] 送信: {challenge_msg.strip()}")
                await websocket.send(challenge_msg)
                challenge_sent = True

            # チャレンジ受諾（チャレンジされた側のみ）
            if logged_in and not is_challenger and not accept_sent:
                # チャレンジ受信を検知
                if f"|pm| {opponent}| {username}|/challenge" in resp:
                    accept_msg = f"|/accept {opponent}\n"
                    print(f"[{username}] 送信: {accept_msg.strip()}")
                    await websocket.send(accept_msg)
                    accept_sent = True

            # battle_tag（ルーム名）の取得
            if battle_tag is None:
                # |updatesearch|{"searching":[],"games":{"battle-gen9randombattle-123456":"[Gen 9] Random Battle"}}
                m = re.search(r'"(battle-[^"]+)":"\\?\[Gen', resp)
                if m:
                    battle_tag = m.group(1)
                    print(f"[{username}] ルーム名取得: {battle_tag}")
                # |pm| ... /nonotify ... <a href="/battle-gen9randombattle-123456">...
                m2 = re.search(r'/battle-([a-z0-9\-]+)', resp)
                if m2:
                    battle_tag = m2.group(1)
                    print(f"[{username}] ルーム名取得: {battle_tag}")

            # ルームにjoin
            if battle_tag and not joined_battle:
                join_msg = f"|/join {battle_tag}\n"
                print(f"[{username}] 送信: {join_msg.strip()}")
                await websocket.send(join_msg)
                joined_battle = True

            # バトル進行
            if battle_tag and resp.startswith(f">{battle_tag}"):
                if "|turn|" in resp:
                    print(f"[{username}] [INFO] ターン進行: {resp}")
                if "|request|" in resp:
                    try:
                        request_json = resp.split("|request|")[1]
                        request = json.loads(request_json)
                        if "active" in request:
                            # 技選択処理
                            moves = request["active"][0]["moves"]
                            # 有効な技のみをフィルタリング
                            valid_moves = [move for move in moves if not move.get("disabled", False)]
                            if valid_moves:
                                move = valid_moves[0]  # 最初の有効な技を選択
                                move_id = move["id"]
                                target = move.get("target", "")
                                if target in ["normal", "adjacentFoe", "adjacentAllyOrSelf", "adjacentAlly", "adjacentFoeOrAlly"]:
                                    move_line = f"{battle_tag}|/choose move {move_id} 1\n"
                                else:
                                    move_line = f"{battle_tag}|/choose move {move_id}\n"
                                turn_count += 1
                                print(f"[{username}] [ターン{turn_count}] 送信コマンド: {move_line.strip()}")
                                await websocket.send(move_line)
                            else:
                                print(f"[{username}] 有効な技がありません")
                        elif "forceSwitch" in request:
                            # 交代要求処理
                            # 交代可能なポケモンのインデックスを自動で選ぶ（最初のtrueを選択）
                            force_switch = request["forceSwitch"][0]
                            side_pokemon = request["side"]["pokemon"]
                            switch_index = None
                            for i, poke in enumerate(side_pokemon):
                                # "active": false かつ "condition" が 0 fnt でなければ出せる
                                if not poke.get("active", False) and not poke["condition"].endswith("fnt"):
                                    switch_index = i + 1  # 1-indexed
                                    break
                            if switch_index is None:
                                print(f"[{username}] 交代可能なポケモンがいません")
                                return
                            move_line = f"{battle_tag}|/choose switch {switch_index}\n"
                            print(f"[{username}] [交代] 送信コマンド: {move_line.strip()}")
                            await websocket.send(move_line)
                        else:
                            print(f"[{username}] 未対応リクエスト: {request}")
                    except Exception as e:
                        print(f"[{username}] requestパースエラー: {e}")

            if "|win|" in resp or "|tie|" in resp:
                print(f"[{username}] バトル終了")
                break

async def main():
    battle_format = "gen9randombattle"
    bot1 = showdown_bot("inf581_bot_1", "INF581_BOT_1", "inf581_bot_2", True, battle_format)
    bot2 = showdown_bot("inf581_bot_2", "INF581_BOT_2", "inf581_bot_1", False, battle_format)
    await asyncio.gather(bot1, bot2)

if __name__ == "__main__":
    asyncio.run(main())