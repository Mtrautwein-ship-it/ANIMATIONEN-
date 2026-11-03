"""Legt eine KI-Sprachaufnahme passend unter das Video.

1. Findet in der MP3 die einzelnen Sätze (über Sprechpausen).
2. Setzt jeden Satz auf den Startzeitpunkt seines Untertitels (CAPTIONS im Template).
   Ist ein Satz zu lang, beginnt er etwas früher oder wird leicht beschleunigt (max. 15 %).
3. Passt die Untertitel-Endzeiten an die echte Sprechdauer an (Mundbewegung synchron).
4. Schreibt die fertige Tonspur als WAV.

Aufruf: python3 voice_align.py stimme.mp3 tonspur.wav
"""
import re, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parent
src, out = Path(sys.argv[1]), Path(sys.argv[2])
tpl_path = root / 'step1-template.html'
tpl = tpl_path.read_text(encoding='utf-8')

m = re.search(r'const CAPTIONS = \[\n(.*?)\n\];', tpl, re.S)
cap_lines = m.group(1).split('\n')
caps = [[float(a), float(b), t] for a, b, t in (re.match(r"\s*\[([\d.]+), ([\d.]+), '(.*)'\],?", l).groups() for l in cap_lines)]
n = len(caps)

# Sprechpausen finden
log = subprocess.run(['ffmpeg', '-i', str(src), '-af', 'silencedetect=noise=-40dB:d=0.15', '-f', 'null', '-'],
                     capture_output=True, text=True).stderr
total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(src)],
                             capture_output=True, text=True).stdout)
starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
pauses = [(s, e) for s, e in zip(starts, ends) if s > 0.05 and e < total - 0.05]
lead = ends[0] if starts and starts[0] <= 0.05 else 0.0

# Optimale Zuordnung: n-1 Schnitte aus den Pausen wählen, sodass die Satzlängen
# möglichst gut zur Textlänge passen und bevorzugt an langen Pausen geschnitten wird.
chars = [len(t) for _, _, t in caps]
speech = total - lead - sum(e - s for s, e in pauses)
rate = speech / sum(chars)
P = len(pauses)
bounds_s = [lead] + [e for _, e in pauses]           # Satzanfang nach Pause k-1
bounds_e = [s for s, _ in pauses] + [total]          # Satzende vor Pause k
INF = float('inf')
# dp[i][k]: Kosten, wenn Satz i nach Pause k-1 beginnt (k=0: Anfang)
dp = [[INF] * (P + 1) for _ in range(n + 1)]
back = [[-1] * (P + 1) for _ in range(n + 1)]
dp[0][0] = 0.0
def cost(i, k0, k1):
    dur = bounds_e[k1] - bounds_s[k0]
    exp = chars[i] * rate
    pen = (dur - exp) ** 2 / max(exp, 0.5)
    gap = (pauses[k1][1] - pauses[k1][0]) if k1 < P else 1.0
    return pen - 1.5 * gap
for i in range(n):
    for k0 in range(P + 1):
        if dp[i][k0] == INF:
            continue
        for k1 in range(k0, P + 1):
            if i == n - 1 and k1 != P:
                continue
            if i < n - 1 and k1 == P:
                continue
            c = dp[i][k0] + cost(i, k0, k1)
            if c < dp[i + 1][k1 + 1 if k1 < P else P]:
                dp[i + 1][k1 + 1 if k1 < P else P] = c
                back[i + 1][k1 + 1 if k1 < P else P] = k0
segs, k = [], P
for i in range(n, 0, -1):
    k0 = back[i][k]
    k1 = k - 1 if i < n else P
    segs.append([bounds_s[k0], bounds_e[k1]])
    k = k0
segs.reverse()

parts, new_caps, report = [], [], []
prev_end = 0.0
for i, ((a, b, text), (s, e)) in enumerate(zip(caps, segs)):
    s, e = max(0, s - 0.05), min(total, e + 0.08)
    dur = e - s
    limit = (caps[i + 1][0] if i + 1 < n else 141.0) - 0.15   # spätestens hier fertig
    start, tempo = max(a, prev_end + 0.25), 1.0
    if start + dur > limit:                       # früher anfangen, wenn davor Platz ist
        start = max(prev_end + 0.25, limit - dur)
    if start + dur > limit:                       # sonst leicht beschleunigen
        tempo = min(1.15, dur / max(limit - start, 0.1))
    spoken = dur / tempo
    prev_end = start + spoken
    clip = root / f'.voice_{i:02d}.wav'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{s:.3f}', '-to', f'{e:.3f}', '-i', str(src),
                    '-af', f'atempo={tempo:.4f},adelay={int(start * 1000)}:all=1', '-ar', '48000', '-ac', '2', str(clip)], check=True)
    parts.append(clip)
    new_caps.append([round(start, 2), round(start + spoken + 0.25, 2), text])
    report.append(f'{start:6.1f}s  {spoken:5.2f}s  x{tempo:.2f}  {text[:50]}')

# Untertitel dürfen sich nicht überlappen
for i in range(len(new_caps) - 1):
    new_caps[i][1] = min(new_caps[i][1], round(new_caps[i + 1][0] - 0.05, 2))

# Mischen
inputs = sum([['-i', str(p)] for p in parts], [])
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex',
                f'amix=inputs={len(parts)}:normalize=0,apad=whole_dur=141,loudnorm=I=-16:TP=-1.5:LRA=11',
                '-ar', '48000', str(out)], check=True)
for p in parts:
    p.unlink()

# Untertitel-Endzeiten an die Sprache anpassen
new_lines = [f"  [{a}, {e}, '{t}']," for a, e, t in new_caps]
tpl = tpl[:m.start(1)] + '\n'.join(new_lines) + tpl[m.end(1):]
tpl_path.write_text(tpl, encoding='utf-8')
print('\n'.join(report))
