"""Bronze -> Silver : price.csv (prix de gros quotidien = coût d'achat)."""
import pandas as pd

from paths import RAW, SILVER

df = pd.read_csv(RAW / "price.csv", dtype={"Item Code": str})
df.columns = ["date", "item_code", "wholesale_price"]
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")

# Un seul prix par jour et par produit, sinon la jointure avec les ventes duplique des lignes
assert not df.duplicated(["date", "item_code"]).any(), "doublon (date, produit)"

# Un prix de gros sous 0,10 RMB/kg n'est pas crédible (erreur de saisie) :
# on le remplace par le dernier prix connu du produit pour ne pas fausser la marge
df = df.sort_values(["item_code", "date"])
df["price_imputed"] = df["wholesale_price"].lt(0.10)
df["wholesale_price"] = (
    df["wholesale_price"].mask(df["price_imputed"]).groupby(df["item_code"]).ffill()
)

df.to_csv(SILVER / "price.csv", index=False)
print(f"price : {len(df)} lignes, {df['price_imputed'].sum()} prix < 0,10 remplacés, "
      f"{df['wholesale_price'].isna().sum()} restés vides")
