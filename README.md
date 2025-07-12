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