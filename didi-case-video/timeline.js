// timeline.js — 由 narration/apply_timings.py 自 timings.json 生成，请改脚本不要手改数字。
// 唯一时间源：画面（index.html）与配乐（score.mjs）都从这里 import。

export const BPM = 96;
export const BEAT = 60 / BPM;
export const BAR = BEAT * 4;
export const b = n => n * BEAT;
export const revealOn = (hit, dur, reveal = 0) => hit - reveal * dur;

export const DUR = 387.1;

// base = 该章画面原本的时长；实际章节随口播伸缩，画面按 base/dur 比例重映射
export const CHAPTERS = [
  { id: 'ch1', t0: 0.0, t1: 51.064, base: 42, narr: 50.064 },
  { id: 'ch2', t0: 51.064, t1: 95.416, base: 48, narr: 43.152 },
  { id: 'ch3', t0: 95.416, t1: 142.288, base: 46, narr: 45.672 },
  { id: 'ch4', t0: 142.288, t1: 200.704, base: 70, narr: 57.216 },
  { id: 'ch5', t0: 200.704, t1: 252.136, base: 48, narr: 50.232 },
  { id: 'ch6', t0: 252.136, t1: 294.256, base: 37, narr: 40.92 },
  { id: 'ch7', t0: 294.256, t1: 349.168, base: 52, narr: 53.712 },
  { id: 'ch8', t0: 349.168, t1: 387.1, base: 37.232, narr: 33.528 },
];

export const SHOTS = CHAPTERS.map(c => ({ id: c.id, t0: c.t0, t1: c.t1, base: c.base }));

// 有口播时音效要克制：章首翻页、两次关键落章、一次重击
export const CUES = [
  { t: 0.0, sfx: 'page' },
  { t: 43.769, sfx: 'stamp' },
  { t: 51.064, sfx: 'page' },
  { t: 95.416, sfx: 'page' },
  { t: 132.098, sfx: 'impact' },
  { t: 142.288, sfx: 'page' },
  { t: 200.704, sfx: 'page' },
  { t: 252.136, sfx: 'page' },
  { t: 294.256, sfx: 'page' },
  { t: 349.168, sfx: 'page' },
  { t: 382.381, sfx: 'stamp' },
];

export const HOLDS = [[373.1, 387.1]];
export const DROPS = [];  // 这支片用氛围式配乐，不做 drop 弧线
