"""Legt eine KI-Sprachaufnahme passend unter das Video.

1. Findet in der MP3 die einzelnen Sätze (über Sprechpausen).
2. Setzt jeden Satz auf den Startzeitpunkt seines Untertitels (CAPTIONS im Template).
   Ist ein Satz länger als sein Zeitfenster, wird er leicht beschleunigt (max. 20 %).
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
log = subprocess.run(['ffmpeg', '-i', str(src), '-af', 'silencedetect=noise=-38dB:d=0.25', '-f', 'null', '-'],
                     capture_output=True, text=True).stderr
total = float(re.search(r'Duration: (\d+):(\d+):([\d.]+)', log).group(3)) + 60 * int(re.search(r'Duration: (\d+):(\d+)', log).group(2))
starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
gaps = list(zip(starts, ends))
# Sprachsegmente zwischen den Pausen
segs, cur = [], 0.0
for s, e in gaps:
    if s - cur > 0.05:
        segs.append([cur, s])
    cur = e
if total - cur > 0.05:
    segs.append([cur, total])
# Zu viele Segmente? Die kleinsten Pausen zusammenführen (Pausen innerhalb eines Satzes)
while len(segs) > n:
    i = min(range(len(segs) - 1), key=lambda k: segs[k + 1][0] - segs[k][1])
    segs[i] = [segs[i][0], segs[i + 1][1]]
    del segs[i + 1]
if len(segs) != n:
    sys.exit(f'Segmente ({len(segs)}) passen nicht zu Untertiteln ({n})')

parts, new_caps, report = [], [], []
for i, ((a, b, text), (s, e)) in enumerate(zip(caps, segs)):
    s, e = max(0, s - 0.05), min(total, e + 0.08)
    dur = e - s
    nxt = caps[i + 1][0] if i + 1 < n else 141.0
    slot = nxt - a - 0.1
    tempo = 1.0
    if dur > slot:
        tempo = min(1.2, dur / slot)
    spoken = dur / tempo
    clip = root / f'.voice_{i:02d}.wav'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{s:.3f}', '-to', f'{e:.3f}', '-i', str(src),
                    '-af', f'atempo={tempo:.4f},adelay={int(a * 1000)}:all=1', '-ar', '48000', '-ac', '2', str(clip)], check=True)
    parts.append(clip)
    end = round(min(a + spoken + 0.3, nxt - 0.05), 2)
    new_caps.append([a, end, text])
    report.append(f'{a:6.1f}s  {spoken:5.2f}s  x{tempo:.2f}  {text[:50]}')

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
