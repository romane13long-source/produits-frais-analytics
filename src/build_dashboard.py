"""Gold -> docs/dashboard.html : agrégats N vs N-1 insérés dans le modèle HTML (fichier autonome)."""
import json

import pandas as pd

from paths import ALERT_THRESHOLD_PCT, GOLD, ROOT

KPIS = ["revenue", "gross_margin", "quantity_kg"]

fact = pd.read_csv(GOLD / "fact_sales.csv", dtype={"item_code": str}, parse_dates=["date"])
dim_product = pd.read_csv(GOLD / "dim_product.csv", dtype={"item_code": str, "category_code": str})
dim_category = pd.read_csv(GOLD / "dim_category.csv", dtype={"category_code": str})
dim_date = pd.read_csv(GOLD / "dim_date.csv", parse_dates=["date"])

sales = (fact.merge(dim_date[["date", "month", "period"]], on="date")
             .merge(dim_product[["item_code", "item_label", "category_code"]], on="item_code")
             .merge(dim_category, on="category_code")
             .query("period != 'hors période'"))
# "Toutes" = total magasin, calculé comme une catégorie de plus
sales = pd.concat([sales, sales.assign(category_name="Toutes")])


def by_period(keys):
    """Somme des KPI par clé, une colonne par période (N, N-1)."""
    out = sales.groupby(keys + ["period"])[KPIS].sum().unstack("period").fillna(0)
    out.columns = [f"{kpi}_{'N1' if period == 'N-1' else 'N'}" for kpi, period in out.columns]
    return out.round(1)


categories = by_period(["category_name"])
promo = sales.groupby(["category_name", "period"])["discount"].mean().unstack("period")
categories["promo_share_N"] = (promo["N"] * 100).round(1)
categories["promo_share_N1"] = (promo["N-1"] * 100).round(1)

# Courbe mensuelle : le mois N est aligné sur le même mois N-1 (juillet avec juillet...)
monthly = sales.groupby(["category_name", "period", "month"])[KPIS].sum().round(1).reset_index()

products = by_period(["category_name", "item_label"]).reset_index()

data = {
    "threshold": ALERT_THRESHOLD_PCT,
    "period_N": "07/2022 – 06/2023",
    "period_N1": "07/2021 – 06/2022",
    "categories": categories.reset_index().to_dict("records"),
    "monthly": monthly.to_dict("records"),
    "products": products.to_dict("records"),
}

template = (ROOT / "src" / "dashboard_template.html").read_text(encoding="utf-8")
html = template.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
(ROOT / "docs" / "dashboard.html").write_text(html, encoding="utf-8")
print(f"docs/dashboard.html : {len(categories)} catégories, {len(products)} lignes produit")
