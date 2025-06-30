import asyncio
from players.policy_network import PolicyNetwork


async def main():
    model_manager = PolicyNetwork()
    # Load model
    model_manager.load("hp")

    print(f"{'-'*10} Testing {'-'*10}")
    # 最小構成でテストを実行
    perf = await model_manager.test(
        number_of_battles=1,  # 1試合のみ
        concurrent_battles=1,  # 同時バトル数1
        log_messages=True,    # ログを有効化
        opponent="random"     # ランダム対戦相手
    )
    print(f"\n{'*'*15} Performance: {perf*100:2.1f}% {'*'*15}\n")

if __name__ == "__main__":
    asyncio.run(main())