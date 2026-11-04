#!/bin/sh
# 混音：配乐 + 口播 → audio/final.wav（成片音轨）
#
# 用法：sh narration/mix.sh
# 前置：
#   audio/music.wav      node <skill>/scripts/audio.mjs build score.mjs --out audio/music.wav
#   audio/narration.wav  python narration/gen.py && python narration/apply_timings.py
#
# 说明：口播归一化到 −16 LUFS 作主线；配乐经 asplit 复制一路作侧链，
#       说话时自动避让约 16 dB；最后限幅并统一到 −15 LUFS / −1.5 dBTP。
set -e
cd "$(dirname "$0")/.."
ffmpeg -y -loglevel error -i audio/music.wav -i audio/narration.wav -filter_complex "\
[1:a]volume=1.0,asplit=2[vo][sc];\
[0:a]volume=0.45[bg];\
[bg][sc]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400:makeup=1[duck];\
[duck][vo]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.9,loudnorm=I=-15:TP=-1.5:LRA=11[out]" \
  -map "[out]" -ar 48000 -ac 2 audio/final.wav
echo "✓ audio/final.wav"
