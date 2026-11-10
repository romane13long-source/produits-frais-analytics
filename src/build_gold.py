"""Silver -> Gold : modèle en étoile pour le dashboard (1 table de faits + 3 dimensions)."""
import pandas as pd

from paths import GOLD, SILVER

# Seuil Comex : une baisse vs N-1 est jugée significative à partir de -15 %
ALERT_THRESHOLD_PCT = -15

product = pd.read_csv(SILVER / "product.csv", dtype=str)
loss = pd.read_csv(SILVER / "loss_rate.csv", dtype={"item_code": str})
price = pd.read_csv(SILVER / "price.csv", dtype={"item_code": str}, parse_dates=["date"])
sales = pd.read_csv(SILVER / "transaction.csv", dtype={"item_code": str}, parse_dates=["date", "datetime"])

# --- dim_category : une ligne par catégorie
dim_category = product[["category_code", "category_name"]].drop_duplicates().reset_index(drop=True)

# --- dim_product : référentiel produit + taux de perte (attribut du produit, pas de la vente)
dim_product = product.drop(columns="category_name").merge(loss, on="item_code", how="left", validate="1:1")
assert dim_product["loss_rate_pct"].notna().all(), "produit sans taux de perte"

# --- dim_date : calendrier complet + périodes Comex (12 derniers mois vs 12 mois précédents)
dates = pd.date_range(sales["date"].min(), sales["date"].max(), freq="D")
dim_date = pd.DataFrame({"date": dates})
dim_date["year"] = dim_date["date"].dt.year
dim_date["month"] = dim_date["date"].dt.to_period("M").astype(str)
dim_date["weekday"] = dim_date["date"].dt.day_name()
end = dim_date["date"].max()
start_n = end - pd.DateOffset(years=1) + pd.Timedelta(days=1)
start_n1 = start_n - pd.DateOffset(years=1)
dim_date["period"] = "hors période"
dim_date.loc[dim_date["date"] >= start_n1, "period"] = "N-1"
dim_date.loc[dim_date["date"] >= start_n, "period"] = "N"

# --- fact_sales : une ligne par article scanné en caisse
fact = sales.merge(price, on=["date", "item_code"], how="left", validate="m:1")
assert len(fact) == len(sales), "la jointure a dupliqué des ventes"
assert fact["wholesale_price"].notna().all(), "vente sans prix de gros"
fact = fact.merge(loss[["item_code", "loss_rate_pct"]], on="item_code", how="left", validate="m:1")

fact["revenue"] = fact["quantity_kg"] * fact["unit_price"]
fact["purchase_cost"] = fact["quantity_kg"] * fact["wholesale_price"]
fact["gross_margin"] = fact["revenue"] - fact["purchase_cost"]
# Pour vendre 1 kg avec un taux de perte p, il faut acheter 1 / (1 - p) kg :
# coût de la perte estimé = coût d'achat x p / (1 - p)
p = fact["loss_rate_pct"] / 100
fact["loss_cost_est"] = fact["purchase_cost"] * p / (1 - p)
fact["margin_after_loss"] = fact["gross_margin"] - fact["loss_cost_est"]
fact = fact.drop(columns=["loss_rate_pct", "price_imputed"])

for name, table in {"fact_sales": fact, "dim_product": dim_product,
                    "dim_category": dim_category, "dim_date": dim_date}.items():
    table.to_csv(GOLD / f"{name}.csv", index=False)
    print(f"{name} : {len(table):,} lignes, {table.shape[1]} colonnes")

# --- Vue consolidée pour le Comex : CA, marge, volume par catégorie, N vs N-1
view = (fact.merge(dim_date[["date", "period"]], on="date")
            .merge(dim_product[["item_code", "category_code"]], on="item_code")
            .merge(dim_category, on="category_code")
            .query("period != 'hors période'")
            .groupby(["category_name", "period"])[["revenue", "gross_margin", "margin_after_loss", "quantity_kg"]]
            .sum().unstack("period"))
kpi = pd.DataFrame(index=view.index)
for col in ["revenue", "gross_margin", "margin_after_loss", "quantity_kg"]:
    kpi[f"{col}_N"] = view[(col, "N")].round(0)
    kpi[f"{col}_N1"] = view[(col, "N-1")].round(0)
    kpi[f"{col}_gap"] = (view[(col, "N")] - view[(col, "N-1")]).round(0)
    kpi[f"{col}_evol_pct"] = ((view[(col, "N")] / view[(col, "N-1")] - 1) * 100).round(1)
    kpi[f"{col}_alert"] = kpi[f"{col}_evol_pct"].le(ALERT_THRESHOLD_PCT)
kpi = kpi.sort_values("revenue_gap")
kpi.to_csv(GOLD / "kpi_category_n_vs_n1.csv")
print(f"\nPériode N : {start_n:%Y-%m-%d} -> {end:%Y-%m-%d}")
print(kpi[["revenue_N", "revenue_gap", "revenue_evol_pct", "gross_margin_evol_pct", "quantity_kg_evol_pct",
           "revenue_alert"]].to_string())
