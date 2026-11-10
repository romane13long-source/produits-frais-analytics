"""Bronze -> Silver : transaction.csv (ventes en caisse, une ligne par article scanné)."""
import pandas as pd

from paths import RAW, SILVER

df = pd.read_csv(RAW / "transaction.csv", dtype={"Item Code": str})
df.columns = ["date", "time", "item_code", "quantity_kg", "unit_price", "sale_type", "discount"]

# Les heures ont un nombre variable de millisecondes ("09:55:08.28") : on parse en vrai horodatage
df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], format="mixed")
df["date"] = df["datetime"].dt.normalize()
df = df.drop(columns="time")

df["is_return"] = df["sale_type"].eq("return")
df["discount"] = df["discount"].eq("Yes")
df = df.drop(columns="sale_type")

# Les retours ont déjà une quantité négative : on les garde, ils viennent en déduction du CA
assert (df.loc[df["is_return"], "quantity_kg"] < 0).all()
assert (df.loc[~df["is_return"], "quantity_kg"] > 0).all()
assert (df["unit_price"] > 0).all()

# Un panier de magasin pèse quelques kg. Le seuil IQR (Q3 + 1,5 x IQR) tomberait à ~1,4 kg
# et marquerait des milliers de ventes normales : on fixe un seuil métier à 20 kg (vente en gros)
q1, q3 = df["quantity_kg"].quantile([0.25, 0.75])
iqr_flags = (df["quantity_kg"] > q3 + 1.5 * (q3 - q1)).sum()
df["bulk_sale"] = df["quantity_kg"].gt(20)

before = len(df)
df = df.drop_duplicates()

df.to_csv(SILVER / "transaction.csv", index=False)
print(f"transaction : {len(df)} lignes ({before - len(df)} doublons), {df['is_return'].sum()} retours, "
      f"{df['bulk_sale'].sum()} ventes > 20 kg (l'IQR en aurait signalé {iqr_flags})")
