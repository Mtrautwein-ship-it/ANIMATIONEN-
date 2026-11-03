"""Baut das Video-HTML: setzt die Figur aus figur/lehrer-figur.html und das Timing in die Szene ein.

Aufruf: python3 build.py [präfix]   (Standard: step1; z. B. folge2)
"""
from pathlib import Path
import re, sys
from folgen import FOLGEN
root = Path(__file__).resolve().parent
prefix = sys.argv[1] if len(sys.argv) > 1 else 'step1'
fig_html = (root.parent / 'figur' / 'lehrer-figur.html').read_text(encoding='utf-8')
svg = re.search(r'<svg id="figur".*?</svg>', fig_html, re.S).group(0)
tpl = (root / f'{prefix}-template.html').read_text(encoding='utf-8')
timing = root / f'{prefix}-timing.json'
html = tpl.replace('<!--FIGUR-->', svg)
if timing.exists():
    html = html.replace('/*TIMING*/null', timing.read_text(encoding='utf-8'))
out = root / f"{FOLGEN[prefix]['name']}.html"
out.write_text(html, encoding='utf-8')
print('ok:', out.name, '(mit Stimme)' if timing.exists() else '(ohne Stimme – geschätzte Zeiten)')
