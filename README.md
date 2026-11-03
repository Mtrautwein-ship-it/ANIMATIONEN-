# ANIMATIONEN – Wasser-Meister

Lehrer-Figur für Erklärvideos zu **Trinkwasserhygiene und Installation**.
Gedrungene, comichafte Proportionen (großer Kopf, kurze Beine, ca. 3,5 Kopflängen hoch),
Werkzeugtasche mit Rohrzange und ein Kupferrohr als Zeigestab.

Standard-Look nach Marcel: schwarze Snapback-Cap, kräftige Brille mit Doppelsteg,
dunkler Vollbart, Ohr-Tunnel, schwarzes T-Shirt mit Namensaufdruck und Wappen,
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
| `video/step1-fluessigkeitskategorien.mp4` | Fertiges Video, 1920 × 1080, 30 fps, 2:21 min, mit KI-Stimme „Chris“ und eingebrannten Untertiteln |
| `video/step1-tonspur.wav` | Sprachspur einzeln (für eigenen Schnitt, Musik etc.) |
| `video/step1-fluessigkeitskategorien.html` | Szene im Browser abspielen und vorspulen (Vorschau-Player) |
| `video/step1-sprechertext.md` | Sprechertext mit Zeitangaben |
| `video/step1-fluessigkeitskategorien.srt` | Untertitel-Datei (z. B. für YouTube) |
| `video/step1-template.html` | Drehbuch: Texte, Posen und Zeiten (`CATS`, `POSES`, `CAPTIONS`) |

Neu bauen und rendern (Node + Playwright + ffmpeg):

```bash
cd video
python3 build.py      # Figur in die Szene einsetzen
node render.js        # MP4 rendern (ohne Ton)
```

Neue KI-Stimme anlegen: Sprechertext bei vidIQ (Voiceover) als eine MP3 erzeugen, dann

```bash
python3 voice_align.py stimme.mp3 step1-tonspur.wav   # Sätze an Untertitel anlegen, Zeiten im Template anpassen
python3 build.py && node render.js step1-fluessigkeitskategorien.html stumm.mp4
ffmpeg -i stumm.mp4 -i step1-tonspur.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest step1-fluessigkeitskategorien.mp4
```
