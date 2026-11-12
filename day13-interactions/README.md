# Day 13: Interactions — 風と波（日本近海）

その場の風が起こす波（風浪）と、遠くから届いたうねりのどちらが勝っているかを 1° 格子で示す地図。

## 再現手順
1. `python3 fetch.py`（標準ライブラリのみ。667 点 × 2 API、約 3 分）→ `data.json`
2. リポジトリのルートを http で配信し（例：`python3 -m http.server`）、`/day13-interactions/` を開く（file:// では data.json を読めない）
3. 投稿用の静止画は `?shot=1`（操作 UI を隠し、左に凡例ぶんの余白）を 1600×900 で撮る → `day13.png`

## 表現
- 点の色相＝判定、明るさ＝有義波高（0〜4 m、連続）。「波高のみ」ボタンで単一の配色に切り替え
- 判定式：`wind_wave_height > swell_wave_height` なら風浪優勢、それ以外（同値を含む）はうねり優勢
- 白い矢印＝風の吹いていく向き（API の風向は吹いてくる方角なので +180°）。長さ＝風速（kn、30 kn で頭打ち）
- 「うねりの向き」ボタンで、うねりの進む向き（同じく +180°）を水色の細い矢印で重ねる
- 格子セルの塗りではなく点にした理由：背景スタイルに陸のポリゴンが無く、セルを塗ると沿岸で陸に被る。点の間から海岸線（水域ポリゴンの縁）が見えるようにした
- 背景は OpenFreeMap の `dark`（Positron と同じ配信元・読み込み方）。海図風に暗くするため

## データと出典
- Weather data by Open-Meteo.com（CC BY 4.0）。波：Marine API、風：Forecast API（10 m 風、kn）。いずれも `current` の値
- 波のモデル：既定の Best match。どのモデルが使われたかは応答に無く**不明**。返ってきた座標が約 1/12° 間隔で、ドキュメントにある MeteoFrance MFWAM（0.08°）と整合するが、確認はできていない
- 風のモデル：既定の Best match。モデル名は**不明**
- 点の位置は要求した 1° 格子。値は API が返した最寄りの格子点のもの（実座標は data.json の `wave_at` / `wind_at`）
- 背景地図：© OpenFreeMap © OpenMapTiles © OpenStreetMap contributors
