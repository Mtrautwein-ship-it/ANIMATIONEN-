"""Stimme für eine neue Folge – mit möglichst wenig vidIQ-Credits.

Sätze, die es schon in einer früheren Folge gibt (z. B. „Hallo und herzlich willkommen!“),
werden aus deren Aufnahme übernommen. Nur die neuen Sätze müssen erzeugt werden.

Schritt 1 – Text für vidIQ ausgeben (Zahlen und Kürzel ausgeschrieben, Absätze = Sätze):
    python3 stimme_folge.py folge2 text

Schritt 2 – die erzeugte MP3 mit den neuen Sätzen einbauen:
    python3 stimme_folge.py folge2 bauen neu.mp3
    -> schreibt <präfix>-stimme-chris.mp3 (alle Sätze, getrennt durch 1,6 s Pause)
       und <präfix>-timing.json; danach build.py, render.js, mux.py wie gewohnt.
"""
import json, re, subprocess, sys
from pathlib import Path
from voice_align import script_lines, segment, root

QUELLEN = ['step1']          # frühere Folgen, aus denen Sätze übernommen werden
ZAHLEN = ['null', 'eins', 'zwei', 'drei', 'vier', 'fünf']


def sprechtext(t):
    """Schreibweise, die die KI-Stimme sauber ausspricht."""
    t = re.sub(r'\b(Folge|Kategorie) (\d)\b', lambda m: f'{m.group(1)} {ZAHLEN[int(m.group(2))]}', t)
    t = re.sub(r'\b5\b', 'fünf', t)
    for k, v in {'AA': 'A-A', 'AB': 'A-B', 'BA': 'B-A', 'CA': 'C-A', 'EA': 'E-A'}.items():
        t = re.sub(rf'\b{k}\b', v, t)
    return t.replace(' – ', ', ')


def vorhandene():
    """Text -> (Aufnahme, start, ende) aus früheren Folgen."""
    out = {}
    for q in QUELLEN:
        timing = json.loads((root / f'{q}-timing.json').read_text(encoding='utf-8'))
        for text, l in zip(script_lines(q), timing['lines']):
            out.setdefault(text, (root / timing['source'], l['s'], l['e']))
    return out


prefix, cmd = sys.argv[1], sys.argv[2]
texte = script_lines(prefix)
alt = vorhandene()
neu = [t for t in texte if t not in alt]

if cmd == 'text':
    print('\n\n'.join(sprechtext(t) for t in neu))
    n = sum(len(sprechtext(t)) for t in neu) + 2 * (len(neu) - 1)
    print(f'\n--- {len(neu)} neue Sätze, {len(texte) - len(neu)} übernommen, {n} Zeichen '
          f'(≈ {14 * -(-n // 1000)} vidIQ-Credits)', file=sys.stderr)

elif cmd == 'bauen':
    mp3 = Path(sys.argv[3]).resolve()
    segs, total = segment(mp3, neu)
    teile = {t: (mp3, max(0, s - 0.05), min(total, e + 0.08)) for t, (s, e) in zip(neu, segs)}
    teile.update({t: alt[t] for t in texte if t in alt})
    quellen = sorted({str(teile[t][0]) for t in texte})
    idx = {q: i for i, q in enumerate(quellen)}
    f, lab = [], []
    for k, t in enumerate(texte):
        q, s, e = teile[t]
        f.append(f"[{idx[str(q)]}:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,aresample=44100,aformat=channel_layouts=mono[p{k}]")
        lab.append(f'[p{k}]')
        if k < len(texte) - 1:
            f.append(f'anullsrc=r=44100:cl=mono,atrim=duration=1.6[z{k}]')
            lab.append(f'[z{k}]')
    ziel = root / f'{prefix}-stimme-chris.mp3'
    inputs = sum([['-i', q] for q in quellen], [])
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex',
                    ';'.join(f) + ';' + ''.join(lab) + f'concat=n={len(lab)}:v=0:a=1[out]',
                    '-map', '[out]', '-b:a', '160k', str(ziel)], check=True)
    subprocess.run([sys.executable, str(root / 'voice_align.py'), str(ziel)], check=True)
    print('fertig:', ziel.name)
