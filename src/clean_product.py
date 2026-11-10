"""Bronze -> Silver : product.csv (référentiel produits)."""
import pandas as pd

from paths import RAW, SILVER, clean_text

df = pd.read_csv(RAW / "product.csv", dtype=str, encoding="utf-8-sig")
df.columns = ["item_code", "item_name", "category_code", "category_name"]

# Espaces insécables et espaces en fin : sinon "Flower/Leaf Vegetables" existe en deux versions
for col in df.columns:
    df[col] = clean_text(df[col])

# Le code produit est la clé de toutes les jointures : il doit être unique
assert df["item_code"].is_unique, "item_code en double dans product.csv"

# Même nom pour deux codes différents (ex. Broccoli) : on ajoute un libellé unique pour le dashboard
dup = df["item_name"].duplicated(keep=False)
df["item_label"] = df["item_name"].where(~dup, df["item_name"] + " (" + df["item_code"].str[-4:] + ")")

df.to_csv(SILVER / "product.csv", index=False)
print(f"product : {len(df)} produits, {df['category_name'].nunique()} catégories, {dup.sum()} libellés désambiguïsés")
