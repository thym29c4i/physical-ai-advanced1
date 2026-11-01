# LUNA CARGO｜月面基地の配送ロボット

Mac＋Dockerで動く、ROS2 Humble / Gazebo Fortressの課題用プロジェクトです。
日本語指示をAIで管制室・資材庫・研究ラボ・充電ドックの4目的地に分類します。
月面重力の近似値として重力を `0 0 -1.62` m/s² に設定しています。
月の砂、真空、温度、粉塵、実際の充電はモデル化していません。

## 起動と操作

Docker Desktopを起動し、このフォルダで実行します。

```bash
docker compose up --build -d
```

ブラウザで http://localhost:6080/vnc.html?autoconnect=true&resize=scale を開きます。
画面下のボタンで目的地を指定できます。緑＝管制室、青＝資材庫、橙＝研究ラボ、白＝充電ドックです。
到着して停止してから次の指示を出します。「帰還」は充電ドックへの移動を指示します。
「不明指示」は拒否の動作例、「停止」は直ちに速度0を指示します。

ターミナルから操作する場合：

```bash
docker compose exec robot bash scripts/command.sh '管制室まで物資を届けて'
docker compose exec robot bash scripts/command.sh '資材庫へ向かってください'
docker compose exec robot bash scripts/command.sh '研究ラボへ配送をお願いします'
docker compose exec robot bash scripts/command.sh '充電ドックに戻って'
docker compose exec robot bash scripts/command.sh '停止'
```

新しい指示は以前の走行を止めてから処理します。不明な指示では走行しません。
オドメトリが2秒以上途切れる、または走行が90秒を超えると中断します。
これはシミュレーション用の制御であり、実機の安全保証ではありません。

## AIの学習とColab

文字1〜3-gramのTF-IDFと、クラス重心のコサイン類似度を用いた教師あり分類です。
学習文76例、評価文20例。しきい値0.30、上位2クラスの差0.08を受理条件としています。
否定・複数目的地などの拒否には補助ルールも使います。類似度は正解確率ではありません。
大規模言語モデルではなく、未登録の施設や自由な日本語全般を理解するものではありません。

```bash
python3 app/train.py
```

`colab/train_intent.ipynb` をColabにアップロードし、セルを上から実行します。
学習コードとデータをノートブックに含めているため、GPU・APIキー・外部パッケージは不要です。
Colabの学習・推論セルはローカルで実行確認済みで、Colabサービス上での実行確認は未実施です。

ノートブックで学習データを編集した場合は、ダウンロードしたZIPの `data/commands.json` を
Mac側の同名ファイルに反映して再起動してください。起動時に再学習するため、モデルだけの置換は上書きされます。

## 実行確認と録画

```bash
python3 -m unittest discover -s tests -v
docker compose exec robot bash -lc 'source /opt/ros/humble/setup.bash && python3 app/demo.py'
```

デモは3施設への移動→充電ドックへ帰還→不明指示の拒否を順に行い、
`results/demo_evaluation.json` に実測結果を保存します。手動指示とは同時に実行しないでください。
走行の位置判定はオドメトリに基づき、外部測定による位置の正確さを保証しません。

```bash
docker compose exec robot bash scripts/record.sh 90
```

別ターミナルでデモを実行すると、操作パネルを含む実時間録画が `results/` に保存されます。
録画時間は60〜180秒で指定できます。倍速編集した場合は倍速を明記してください。

画面が出ない場合は、`results/gui.log`、`results/panel.log`、`results/gazebo.log` を確認します。
動かない場合は `results/controller.log` と `results/bridge.log`、オドメトリを確認します。
CPU描画にはOgre2を使っています。Ogreでは一部の図形が欠落する現象がありました。
停止：

```bash
docker compose down
```

## 課題としての工夫と制限

元記事の差動二輪・速度指令・ROSブリッジを土台に、日本語指示のAI分類、自律移動、帰還、
月面重力、月面基地の景観、日本語操作パネル、ログと評価を追加しました。
配送は指定位置への移動を表し、物資の把持・積み降ろし、障害物回避は未実装です。
施設・岩・太陽電池パネルは衝突を持たない装飾で、走行経路は平面です。

提出時は自分の工夫と結果を確認し、個人情報や秘密情報を含めず、コードをpublicのGitHubへ、
動画をYouTubeへ限定公開または公開で置いてください。説明資料PDFのファイル名には
omnicampusアカウント名または提出要項に沿った識別名を設定します。

## 参考

- https://qiita.com/N622/items/9d89f77d85d9da0af29e
- https://gazebosim.org/docs/fortress/moving_robot/
- https://gazebosim.org/docs/fortress/ros2_integration/
- https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html
