# Installation
annacondaでTensorflow1で動く環境。`requirements.txtからpip installすれば動くはず。`

# Startup
pokemon-showdownサーバを起動する。別途リポジトリ必要なのでインストールする必要あり。
```
$ cd ~/pokemon-showdown
$ node pokemon-showdown start --no-security --debug
```
別ターミナルに低下のコマンドでバトル開始。
```
$ python3 test_websocket.py
```

http://localhost:8000からshowdownサーバにアクセスしてバトルしてる感じが見れる。

# ToDo
- 技ランダム、テラスタル、推論モデル同士のバトル
- 学習させる。tf2でも実行できるようにする。
- 人対学習モデル


- もし「どのポケモンに交代するか」や「どの技を使うか」をより細かく学習させたい場合、observationやaction_spaceの設計を拡張する必要があります。
まとめ： 現状の設計でも「技選択・交代先を含めた最適解の学習」は可能ですが、
より高度な最適化や戦略的な交代を学習させたい場合は、状態・行動空間の拡張が有効です。