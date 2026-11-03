"""Bereitet eine KI-Sprachaufnahme (eine MP3 mit dem ganzen Sprechertext) für das Video vor.

1. Findet in der MP3 die einzelnen Sätze (über Sprechpausen, optimal zugeordnet zur Textlänge).
2. Berechnet für jeden Satz die Lautstärke-Kurve (steuert die Mundbewegung der Figur).
3. Schreibt step1-timing.json – build.py baut das ins Video ein; die Zeiten ergeben sich daraus.

Aufruf: python3 voice_align.py stimme.mp3
"""
import json, re, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parent
src = Path(sys.argv[1]).resolve()
tpl = (root / 'step1-template.html').read_text(encoding='utf-8')
block = re.search(r'const SCRIPT = \[\n(.*?)\n\];', tpl, re.S).group(1)
caps = [m.group(1) for m in re.finditer(r"\['[^']+', '[^']+', '(.*)'\],", block)]
n = len(caps)
FPS = 30

# Sprechpausen finden
log = subprocess.run(['ffmpeg', '-i', str(src), '-af', 'silencedetect=noise=-40dB:d=0.15', '-f', 'null', '-'],
                     capture_output=True, text=True).stderr
total = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(src)],
                             capture_output=True, text=True).stdout)
starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
pauses = [(s, e) for s, e in zip(starts, ends) if s > 0.05 and e < total - 0.05]
lead = ends[0] if starts and starts[0] <= 0.05 else 0.0

# Eindeutige lange Pausen (>= 1,4 s) zwischen allen Sätzen? Dann direkt dort schneiden.
long_p = [(a_, b_) for a_, b_ in pauses if b_ - a_ >= 1.4]
segs = None
if len(long_p) == n - 1:
    bs = [lead] + [b_ for _, b_ in long_p]
    be = [a_ for a_, _ in long_p] + [total]
    segs = [[x, y] for x, y in zip(bs, be)]

if segs is None:
    # Optimale Zuordnung: n-1 Schnitte aus den Pausen wählen, sodass die Satzlängen
    # möglichst gut zur Textlänge passen und bevorzugt an langen Pausen geschnitten wird.
    chars = [len(t) for t in caps]
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

# Lautstärke-Kurve je Satz (für den Mund)
pcm = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(src), '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                     capture_output=True, check=True).stdout
import array
samples = array.array('h', pcm)
SR, hop = 16000, 16000 // FPS
def rms(a, b):
    seg = samples[a:b]
    return (sum(x * x for x in seg) / max(len(seg), 1)) ** 0.5
lines, allv = [], []
for (s, e) in segs:
    s, e = max(0, s - 0.05), min(total, e + 0.08)
    vals = [rms(int((s + k / FPS) * SR) - hop // 2, int((s + k / FPS) * SR) + hop) for k in range(int((e - s) * FPS) + 1)]
    lines.append({'s': round(s, 3), 'e': round(e, 3), 'dur': round(e - s, 3), 'raw': vals})
    allv += vals
ref = sorted(allv)[int(len(allv) * 0.95)] or 1
for l in lines:
    v = [min(1.0, (x / ref) ** 0.7) for x in l.pop('raw')]
    sm = [(v[max(0, k - 1)] + 2 * v[k] + v[min(len(v) - 1, k + 1)]) / 4 for k in range(len(v))]
    l['env'] = [round(x, 2) for x in sm]

out = {'source': src.name, 'fps': FPS, 'lines': lines}
(root / 'step1-timing.json').write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
for t, l in zip(caps, lines):
    print(f"{l['dur']:5.2f}s  {t[:60]}")
