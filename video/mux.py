"""Baut die Tonspur passend zu den Satz-Zeiten des gerenderten Videos und fügt sie ein.
Schreibt außerdem Untertitel (SRT) und Sprechertext (MD).

Aufruf: python3 mux.py stumm.mp4 stimme.mp3 ausgabe.mp4
(step1-zeiten.json wird von render.js geschrieben, step1-timing.json von voice_align.py)
"""
import json, subprocess, sys
from pathlib import Path

root = Path(__file__).resolve().parent
video, voice, out = (Path(a).resolve() for a in sys.argv[1:4])
zeiten = json.loads((root / 'step1-zeiten.json').read_text(encoding='utf-8'))
timing = json.loads((root / 'step1-timing.json').read_text(encoding='utf-8'))
dur = zeiten['duration']

# Tonspur: jeden Satz aus der Aufnahme schneiden und an seinen Zeitpunkt legen
filters, labels = [], []
for k, (line, tm) in enumerate(zip(zeiten['lines'], timing['lines'])):
    filters.append(f"[0:a]atrim=start={tm['s']}:end={tm['e']},asetpts=PTS-STARTPTS,adelay={int(line['start'] * 1000)}:all=1[a{k}]")
    labels.append(f'[a{k}]')
graph = ';'.join(filters) + ';' + ''.join(labels) + f'amix=inputs={len(labels)}:normalize=0,apad=whole_dur={dur},loudnorm=I=-16:TP=-1.5:LRA=11[out]'
wav = root / 'step1-tonspur.wav'
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(voice), '-filter_complex', graph, '-map', '[out]',
                '-ar', '48000', '-t', str(dur), str(wav)], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(video), '-i', str(wav), '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', str(out)], check=True)

# Untertitel + Sprechertext
def srt_t(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
def mm(t):
    return f'{int(t // 60)}:{t % 60:04.1f}'
srt, md = [], ['# Sprechertext – Folge 1: Die 5 Flüssigkeitskategorien', '',
               'Stimme: KI-Stimme „Chris“ (vidIQ Voiceover). Zeiten entsprechen dem fertigen Video.', '',
               '| Zeit | Text |', '|---|---|']
for k, l in enumerate(zeiten['lines'], 1):
    srt += [str(k), f"{srt_t(l['start'])} --> {srt_t(l['end'] + 0.15)}", l['text'], '']
    md.append(f"| {mm(l['start'])} – {mm(l['end'])} | {l['text']} |")
(root / 'step1-fluessigkeitskategorien.srt').write_text('\n'.join(srt), encoding='utf-8')
(root / 'step1-sprechertext.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print('fertig:', out, f'({dur:.1f} s)')
