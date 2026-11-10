from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold"
IMAGES = ROOT / "docs" / "images"

# Seuil Comex : une baisse vs N-1 est jugée significative à partir de -15 %
ALERT_THRESHOLD_PCT = -15

for folder in (SILVER, GOLD, IMAGES):
    folder.mkdir(parents=True, exist_ok=True)


def clean_text(series):
    """Remplace les espaces insécables, retire les espaces en trop."""
    return series.str.replace("\xa0", " ", regex=False).str.replace(r"\s+", " ", regex=True).str.strip()
