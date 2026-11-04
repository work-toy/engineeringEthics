# 逐段合成 Edge TTS（晓晓），插入片头/章间/片尾静音，拼成 48k 立体声，写出时间戳。
# 时间结构：1.0 s 片头 + 8 段口播（段间 1.2 s）+ 3.2 s 片尾 = 384.0 s，与 timeline.js 对齐。
import asyncio, hashlib, json, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAR = os.path.join(ROOT, "narration")
AUD = os.path.join(ROOT, "audio")
os.makedirs(AUD, exist_ok=True)

LEAD, GAP, TAIL = 1.0, 1.2, 3.2
cfg = json.load(open(os.path.join(NAR, "segments.json"), encoding="utf-8"))
VOICE, RATE = cfg["voice"], cfg.get("rate", "+0%")


def dur(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], text=True).strip())


def to_wav(src, dst):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", "48000", "-ac", "2",
                    "-c:a", "pcm_s16le", dst], check=True)


def silence(seconds, dst):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", f"anullsrc=r=48000:cl=stereo", "-t", str(seconds),
                    "-c:a", "pcm_s16le", dst], check=True)


async def main():
    import edge_tts

    files, segs = [], []
    tag = VOICE.replace("zh-CN-", "")
    files.append(os.path.join(NAR, "_lead.wav")); silence(LEAD, files[-1])
    for i, s in enumerate(cfg["segments"]):
        h = hashlib.md5(s["text"].encode("utf-8")).hexdigest()[:8]
        mp3 = os.path.join(NAR, f"{s['id']}-{tag}-{h}.mp3")
        if not (os.path.exists(mp3) and os.path.getsize(mp3) > 1000):
            await edge_tts.Communicate(s["text"], VOICE, rate=RATE).save(mp3)
        wav = os.path.join(NAR, f"{s['id']}.wav")
        to_wav(mp3, wav)
        d = dur(wav)
        segs.append({"id": s["id"], "duration": round(d, 3)})
        files.append(wav)
        if i < len(cfg["segments"]) - 1:
            gp = os.path.join(NAR, "_gap.wav")
            silence(GAP, gp); files.append(gp)
        print(f"{s['id']}: {d:.2f}s", flush=True)
    files.append(os.path.join(NAR, "_tail.wav")); silence(TAIL, files[-1])

    listf = os.path.join(NAR, "concat.txt")
    with open(listf, "w", encoding="utf-8") as f:
        for p in files:
            f.write(f"file '{p}'\n")
    out = os.path.join(AUD, "narration.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", listf, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", out], check=True)

    t, timings = LEAD, []
    for s in segs:
        timings.append({"id": s["id"], "start": round(t, 3), "end": round(t + s["duration"], 3)})
        t += s["duration"] + GAP
    total = dur(out)
    json.dump({"voice": VOICE, "rate": RATE, "duration": round(total, 3), "file": "audio/narration.wav",
               "structure": {"lead": LEAD, "gap": GAP, "tail": TAIL}, "segments": timings},
              open(os.path.join(NAR, "timings.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"total {total:.3f}s -> {out}")


asyncio.run(main())
