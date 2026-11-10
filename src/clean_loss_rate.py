"""Bronze -> Silver : loss_rate.csv (taux de perte par produit)."""
import pandas as pd

from paths import RAW, SILVER, clean_text

df = pd.read_csv(RAW / "loss_rate.csv", dtype=str, encoding="utf-8-sig")
df.columns = ["item_code", "item_name", "loss_rate_pct"]
df["item_code"] = clean_text(df["item_code"])

# Les 251 valeurs finissent par un espace ("4.39 ") : texte -> nombre
df["loss_rate_pct"] = pd.to_numeric(clean_text(df["loss_rate_pct"]))
assert df["loss_rate_pct"].between(0, 100).all(), "taux de perte hors 0-100 %"

# Le nom est déjà dans product.csv (vérifié identique) : on ne garde que la clé
df = df.drop(columns="item_name")

# 0 % de perte sur un produit frais est peu crédible : on garde la valeur mais on la signale
df["loss_rate_to_check"] = df["loss_rate_pct"].eq(0)

df.to_csv(SILVER / "loss_rate.csv", index=False)
print(f"loss_rate : {len(df)} produits, {df['loss_rate_to_check'].sum()} à 0 %")
