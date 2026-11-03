"""Gemeinsame Namen je Folge. Präfix = Anfang der Dateinamen (z. B. step1, folge2)."""
FOLGEN = {
    'step1': {'name': 'step1-fluessigkeitskategorien', 'titel': 'Folge 1: Die 5 Flüssigkeitskategorien'},
    'folge2': {'name': 'folge2-sicherungseinrichtungen', 'titel': 'Folge 2: Sicherungseinrichtungen'},
}

def prefix_of(path):
    from pathlib import Path
    return Path(path).name.split('-')[0]
