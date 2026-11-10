from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold"
IMAGES = ROOT / "docs" / "images"

for folder in (SILVER, GOLD, IMAGES):
    folder.mkdir(parents=True, exist_ok=True)


def clean_text(series):
    """Remplace les espaces insécables, retire les espaces en trop."""
    return series.str.replace("\xa0", " ", regex=False).str.replace(r"\s+", " ", regex=True).str.strip()
