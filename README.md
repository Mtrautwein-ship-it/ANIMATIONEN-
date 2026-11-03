# ANIMATIONEN – Wasser-Meister

Lehrer-Figur für Erklärvideos zu **Trinkwasserhygiene und Installation**.
Gedrungene, comichafte Proportionen (großer Kopf, kurze Beine, ca. 3,5 Kopflängen hoch),
Werkzeugtasche mit Rohrzange und ein Kupferrohr als Zeigestab.

Standard-Look: schwarze Snapback-Cap mit Wappen (`figur/wappen.png`), kräftige Brille mit Doppelsteg,
dunkler Vollbart, Ohr-Tunnel, schwarzes T-Shirt mit PMPNZNG-Schriftzug (weiß auf rot),
tätowierte Unterarme, Rot als Akzentfarbe. Alternativ: Arbeitsjacke und Schutzhelm.

## Benutzung

`figur/lehrer-figur.html` im Browser öffnen (am besten Chrome oder Edge).

- **Posen:** Stehen, Erklären, Zeigen (mit Rohr-Zeigestab), Winken, Achtung!, Gehen, Jubeln
- **Sprechen:** Mundbewegung lässt sich mit jeder Pose kombinieren, Blinzeln läuft immer
- **Aussehen anpassen:** Haarfarbe, Hautton, Augenfarbe, Frisur, Bart, Schnurrbart, Brille,
  Cap/Schutzhelm, Ohr-Tunnel, Tattoos, Outfit (T-Shirt/Arbeitsjacke), Statur, Namensschild, Kleidungsfarben
- **Export:**
  - PNG mit transparentem Hintergrund (Standbild der aktuellen Pose, 2240 × 2280 px)
  - SVG (animiert, für Web / Weiterbearbeitung in Inkscape/Illustrator)
  - Video (WebM) – mit Hintergrund „Transparent" inkl. Alphakanal, oder mit Greenscreen
    für Schnittprogramme ohne Alpha-Unterstützung (dann per Chroma-Key freistellen)

## Dateien

| Datei | Inhalt |
|---|---|
| `figur/lehrer-figur.html` | Figuren-Studio mit allen Posen, Anpassungen und Export |
| `figur/wasser-meister.svg` | Figur als animierte SVG (Standard-Look) |
| `figur/vorschau-*.png` | Vorschaubilder |

## Videos

### Step 1 – Die 5 Flüssigkeitskategorien (DIN EN 1717)

| Datei | Inhalt |
|---|---|
| `video/step1-fluessigkeitskategorien.mp4` | Fertiges Video, 1920 × 1080, 30 fps, ca. 2:08 min, KI-Stimme „Chris“, Untertitel eingebrannt |
| `video/step1-fluessigkeitskategorien.html` | Szene im Browser abspielen und vorspulen (Vorschau-Player) |
| `video/step1-template.html` | Drehbuch: Sätze, Folien und Posen (`SCRIPT`), Pausen (`GAP_LINE`, `GAP_SCENE`) |
| `video/step1-stimme-chris.mp3` | Original-Sprachaufnahme (vidIQ Voiceover, Stimme „Chris“) |
| `video/step1-timing.json` | Satzlängen + Lautstärke-Kurve für die Mundbewegung (aus `voice_align.py`) |
| `video/step1-tonspur.wav` | Fertige Tonspur einzeln (für eigenen Schnitt, Musik etc.) |
| `video/step1-sprechertext.md`, `.srt` | Sprechertext mit Zeiten, Untertitel-Datei (z. B. für YouTube) |

Der Ablauf richtet sich nach der Stimme: Sätze folgen direkt aufeinander, Folien wechseln
kurz nach dem letzten Satz. Der Mund bewegt sich nach der Lautstärke der Aufnahme,
Posenwechsel werden weich überblendet.

Neu bauen (Node + Playwright + ffmpeg):

```bash
cd video
python3 voice_align.py step1-stimme-chris.mp3        # nur bei neuer Sprachaufnahme
python3 build.py                                     # Figur + Timing in die Szene einsetzen
node render.js step1-fluessigkeitskategorien.html stumm.mp4
python3 mux.py stumm.mp4 step1-stimme-chris.mp3 step1-fluessigkeitskategorien.mp4
```
