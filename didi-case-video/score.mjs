// score.mjs — 纪录片式稀疏配乐：低频铺底 + 偶尔的钢琴单音 + 纸张/印章/打字音效。
// 构建：node <skill>/scripts/audio.mjs build score.mjs
import { DUR, BPM, CUES, SHOTS, DROPS } from './timeline.js';
export { DUR };

export default function score(S) {
  S.tempo(BPM);
  S.space({ room: 0.9, damp: 0.6 });

  const bed = S.bus('bed', { gain: 0.30, reverb: 0.55, highpass: 55 });
  const keys = S.bus('keys', { gain: 0.34, reverb: 0.50, highpass: 140 });
  const sfx = S.bus('sfx', { gain: 0.50, reverb: 0.28 });

  // 每章一条低频铺底，缓慢换和弦
  const roots = ['D2', 'A1', 'F2', 'C2', 'D2', 'Bb1', 'G1', 'D2'];
  SHOTS.forEach((sh, i) => {
    const dur = sh.t1 - sh.t0;
    const root = roots[i % roots.length];
    bed.add(S.pad(S.chord(root, 'min', 1), dur + 2, { cutoff: 620, attack: 2.8, release: 3.2, voices: 4 }), sh.t0, { gain: 0.9 });
    bed.add(S.pad(S.chord(root, '5'), dur + 2, { cutoff: 320, attack: 3.5, release: 3.5, voices: 2 }), sh.t0, { gain: 0.55 });
  });

  // 稀疏钢琴：每章开头一个和弦，章末一个单音
  const chords = [
    ['D4', 'F4', 'A4'], ['A3', 'C4', 'E4'], ['F3', 'A3', 'C4'], ['C4', 'E4', 'G4'],
    ['D4', 'F4', 'A4'], ['Bb3', 'D4', 'F4'], ['G3', 'Bb3', 'D4'], ['D4'],
  ];
  SHOTS.forEach((sh, i) => {
    const n = chords[i % chords.length];
    keys.add(S.keys(n, 3.4, { decay: 2.6 }), sh.t0 + 0.9, { gain: 0.50 });
    keys.add(S.keys([n[n.length - 1]], 4.2, { decay: 3.0 }), sh.t1 - 4.6, { gain: 0.30 });
  });

  // 重拍前铺一个低音，制造下压感
  DROPS.forEach(t => {
    bed.add(S.sub('D1', 4.8), t - 4.4, { gain: 0.22 });
  });

  for (const c of CUES) {
    if (c.sfx === 'page') sfx.add(S.swipe(0.42), c.t - 0.10, { gain: 0.50 });
    if (c.sfx === 'stamp') {
      sfx.add(S.impact({ size: 0.3 }), c.t, { gain: 0.42 });
      sfx.add(S.tick('D3'), c.t + 0.03, { gain: 0.28 });
    }
    if (c.sfx === 'tick') sfx.add(S.tick('A5'), c.t, { gain: 0.16 });
    if (c.sfx === 'pop') sfx.add(S.pop('D5'), c.t, { gain: 0.38 });
    if (c.sfx === 'whoosh') sfx.add(S.whoosh(0.9), c.t - 0.7, { gain: 0.45 });
    if (c.sfx === 'shimmer') sfx.add(S.shimmer(2.4), c.t, { gain: 0.32 });
    if (c.sfx === 'impact') {
      sfx.add(S.impact(), c.t, { gain: 0.55 });
      sfx.add(S.boom(), c.t, { gain: 0.45 });
      S.duck(c.t);
    }
  }

  // 两个关键数字前的升压
  sfx.add(S.riser(2.2), 126.4, { gain: 0.28 });
  sfx.add(S.riser(2.2), 377.4, { gain: 0.30 });
}
