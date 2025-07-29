import gymnasium as gym
from stable_baselines3 import DQN
from src.environment.pokemon_battle_env import PokemonBattleEnv

if __name__ == "__main__":
    # 環境インスタンス化
    env = PokemonBattleEnv()

    # DQNエージェント作成
    model = DQN(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log="./dqn_tensorboard/"
    )

    # 学習
    model.learn(total_timesteps=10000)

    # モデル保存
    model.save("models/dqn_pokemon_battle")

    print("学習・保存完了") 