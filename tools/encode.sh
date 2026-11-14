#!/bin/sh
# コマ（frame_0000.png …、30fps）から GIF と MP4 を作る。
#   sh encode.sh <framesDir> <outPrefix>
#   → <outPrefix>.mp4（1600x900 そのまま、H.264 yuv420p）
#     <outPrefix>.gif（1000x562、15fps、64色。約 8MB。32色だと凡例の琥珀の明るい端が青白く化けるので 64 にした。X の上限は 15MB）
#     <outPrefix>-small.gif（800x450、15fps、24色）。どちらも 30fps のコマを1つおきに使うのでループの継ぎ目が均等
# 容量は動く画素の数で決まり、色数はあまり効かない（2026-11-13 実測：1200 幅 64 色 7.9MB、48 色 7.2MB）。
# 目標（X 用 5MB、Zenn 用 3MB）に収めるため幅を落とし、ディザは無し（あると粒の周りのノイズで膨らむ）。変えたら容量を測り直す。
#
# 環境変数で変えられる（未指定なら上の Day 13 の既定どおり）
#   GIF_W=1000 GIF_FPS=15 GIF_COLORS=64   … 本体 GIF の幅・fps・色数
#   PAL_STATS=diff                        … palettegen の stats_mode。画面全体が動く絵は full が向く
#   SMALL=1                               … 0 で -small.gif を作らない
#   MP4=1                                 … 0 で MP4 を作らない（GIF の設定だけ試すとき）
#   PAL_EXTRA=<画像>                      … パレットの集計にこの画像を 2 秒ぶん混ぜる。面積の小さい色（朱など）を
#                                           色数を絞っても残すため（例：tools/day14-palette.png＝Day 14 の基準 8 色の帯）
set -eu
FR="$1"; OUT="$2"
GIF_W="${GIF_W:-1000}"; GIF_FPS="${GIF_FPS:-15}"; GIF_COLORS="${GIF_COLORS:-64}"
PAL_STATS="${PAL_STATS:-diff}"; SMALL="${SMALL:-1}"; MP4="${MP4:-1}"; PAL_EXTRA="${PAL_EXTRA:-}"
IN="$FR/frame_%04d.png"

if [ "$MP4" = 1 ]; then
ffmpeg -hide_banner -loglevel error -y -framerate 30 -i "$IN" \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -preset slow -movflags +faststart "$OUT.mp4"
fi

# パレットは全コマから作る（stats_mode=diff で動く部分＝粒と点を優先）
gif() { # $1=幅 $2=fps $3=色数 $4=出力
  if [ -n "$PAL_EXTRA" ]; then
    ffmpeg -hide_banner -loglevel error -y -framerate 30 -i "$IN" -loop 1 -framerate "$2" -t 2 -i "$PAL_EXTRA" -filter_complex \
      "[0]fps=$2,scale=$1:-2:flags=lanczos,format=rgb24,setsar=1,split[a][b];[1]scale=$1:-2:flags=neighbor,format=rgb24,setsar=1[s];[a][s]concat=n=2:v=1[c];[c]palettegen=max_colors=$3:stats_mode=$PAL_STATS[p];[b][p]paletteuse=dither=none:diff_mode=rectangle" \
      -loop 0 "$4"
    return
  fi
  ffmpeg -hide_banner -loglevel error -y -framerate 30 -i "$IN" -filter_complex \
    "fps=$2,scale=$1:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=$3:stats_mode=$PAL_STATS[p];[b][p]paletteuse=dither=none:diff_mode=rectangle" \
    -loop 0 "$4"
}
gif "$GIF_W" "$GIF_FPS" "$GIF_COLORS" "$OUT.gif"
[ "$SMALL" = 1 ] && gif 800 15 24 "$OUT-small.gif"
ls -l "$OUT".*  "$OUT"-small.gif 2>/dev/null || true
