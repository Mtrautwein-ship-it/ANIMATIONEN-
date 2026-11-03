"""Baut das Video-HTML: setzt die Figur aus figur/lehrer-figur.html in die Szene ein."""
from pathlib import Path
import re
root = Path(__file__).resolve().parent
fig_html = (root.parent / 'figur' / 'lehrer-figur.html').read_text(encoding='utf-8')
svg = re.search(r'<svg id="figur".*?</svg>', fig_html, re.S).group(0)
tpl = (root / 'step1-template.html').read_text(encoding='utf-8')
(root / 'step1-fluessigkeitskategorien.html').write_text(tpl.replace('<!--FIGUR-->', svg), encoding='utf-8')
print('ok')
