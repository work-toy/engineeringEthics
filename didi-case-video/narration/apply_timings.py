# 由 narration/timings.json 生成 timeline.js，保证画面、配乐、口播共用同一套时间。
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = json.load(open(os.path.join(ROOT, "narration", "timings.json"), encoding="utf-8"))
segs = T["segments"]

BASE = {"ch1": 42, "ch2": 48, "ch3": 46, "ch4": 70, "ch5": 48, "ch6": 37, "ch7": 52, "ch8": 37.232}
TAIL = 3.2

# 章窗口：上一章口播结束 → 本章口播结束（含章间 1.2 s 呼吸）
rows, prev_end = [], 0.0
for i, s in enumerate(segs):
    dur = s["end"] - s["start"]
    rows.append({"id": s["id"], "t0": round(prev_end, 3), "t1": round(s["end"], 3),
                 "base": BASE[s["id"]], "narr": round(dur, 3)})
    prev_end = s["end"]

raw_dur = T["duration"]
frames = round(raw_dur * 30)
DUR = round(frames / 30, 3)
rows[-1]["t1"] = DUR  # 最后一章吃掉片尾留白，画面映射覆盖到片尾


def at(r, b):
    return round(r["t0"] + b * (r["t1"] - r["t0"]) / r["base"], 3)


cues = []
for r in rows:
    cues.append({"t": round(r["t0"], 3), "sfx": "page"})
stamp1 = at(rows[0], 36)
impact3 = at(rows[2], 36)
stamp8 = at(rows[7], 32.6)
cues.append({"t": stamp1, "sfx": "stamp"})
cues.append({"t": impact3, "sfx": "impact"})
cues.append({"t": stamp8, "sfx": "stamp"})
cues.sort(key=lambda c: c["t"])

lines = []
lines.append("// timeline.js — 由 narration/apply_timings.py 自 timings.json 生成，请改脚本不要手改数字。")
lines.append("// 唯一时间源：画面（index.html）与配乐（score.mjs）都从这里 import。")
lines.append("")
lines.append("export const BPM = 96;")
lines.append("export const BEAT = 60 / BPM;")
lines.append("export const BAR = BEAT * 4;")
lines.append("export const b = n => n * BEAT;")
lines.append("export const revealOn = (hit, dur, reveal = 0) => hit - reveal * dur;")
lines.append("")
lines.append(f"export const DUR = {DUR};")
lines.append("")
lines.append("// base = 该章画面原本的时长；实际章节随口播伸缩，画面按 base/dur 比例重映射")
lines.append("export const CHAPTERS = [")
for r in rows:
    lines.append(f"  {{ id: '{r['id']}', t0: {r['t0']}, t1: {r['t1']}, base: {r['base']}, narr: {r['narr']} }},")
lines.append("];")
lines.append("")
lines.append("export const SHOTS = CHAPTERS.map(c => ({ id: c.id, t0: c.t0, t1: c.t1, base: c.base }));")
lines.append("")
lines.append("// 有口播时音效要克制：章首翻页、两次关键落章、一次重击")
lines.append("export const CUES = [")
for c in cues:
    lines.append(f"  {{ t: {c['t']}, sfx: '{c['sfx']}' }},")
lines.append("];")
lines.append("")
lines.append(f"export const HOLDS = [[{round(DUR - 14, 3)}, {DUR}]];")
lines.append(f"export const DROPS = [];  // 这支片用氛围式配乐，不做 drop 弧线")
lines.append("")

open(os.path.join(ROOT, "timeline.js"), "w", encoding="utf-8").write("\n".join(lines))
print(f"DUR={DUR} frames={frames}")
for r in rows:
    print(f"  {r['id']}: {r['t0']} -> {r['t1']}  (base {r['base']}, narr {r['narr']})")
print("cues:", ", ".join(f"{c['t']}:{c['sfx']}" for c in cues))
