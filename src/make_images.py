"""Génère les images du README (docs/images)."""
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from paths import GOLD, IMAGES, SILVER

BLUE, ORANGE, INK, MUTED, SURFACE = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#fcfcfb"
ALERT = "#d03b3b"  # rouge « alerte », le même que dans le dashboard et les slides
plt.rcParams.update({"font.size": 10, "text.color": INK, "axes.edgecolor": MUTED,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})


def table_box(ax, x, y, title, rows, color, width=3.2):
    """Dessine une table : titre coloré + une ligne par colonne."""
    h = 0.42 * (len(rows) + 1)
    ax.add_patch(FancyBboxPatch((x, y - h), width, h, boxstyle="round,pad=0.02",
                                fc="white", ec=color, lw=1.5))
    ax.add_patch(FancyBboxPatch((x, y - 0.42), width, 0.42, boxstyle="round,pad=0.02", fc=color, ec=color))
    ax.text(x + width / 2, y - 0.21, title, ha="center", va="center", color="white", weight="bold")
    for i, row in enumerate(rows):
        ax.text(x + 0.12, y - 0.42 * (i + 1.5), row, va="center", fontsize=8.5, family="monospace")
    return {"left": (x, y - 0.6), "right": (x + width, y - 0.6), "top": (x + width / 2, y),
            "bottom": (x + width / 2, y - h)}


def link(ax, a, b, label=""):
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.2,
                                                    connectionstyle="arc3,rad=0.0"))
    if label:
        ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.15, label, ha="center", fontsize=8, color=MUTED)


def canvas(w, h, title):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w * 1.2)
    ax.set_ylim(0, h * 1.2)
    ax.axis("off")
    ax.set_title(title, loc="left", weight="bold", fontsize=12)
    return fig, ax


# 1. Diagnostic : anomalies trouvées par fichier
diag = pd.DataFrame([
    ("transaction", "Heures au format variable (ms tronquées)", 18841),
    ("transaction", "Retours (quantité négative)", 461),
    ("transaction", "Ventes > 20 kg (signalées)", 3),
    ("product", "Espace insécable dans la catégorie", 100),
    ("product", "Noms en double (codes différents)", 8),
    ("product", "Espaces en fin de nom", 4),
    ("price", "Prix de gros < 0,10 RMB/kg", 53),
    ("loss_rate", "Taux stockés en texte (« 4.39 »)", 251),
    ("loss_rate", "Taux de perte à 0 %", 22),
], columns=["fichier", "anomalie", "lignes"])
fig, ax = plt.subplots(figsize=(9, 4.2))
labels = diag["fichier"] + " · " + diag["anomalie"]
ax.barh(labels[::-1], diag["lignes"][::-1], color=BLUE, height=0.6)
ax.set_xscale("log")
for i, v in enumerate(diag["lignes"][::-1]):
    ax.text(v * 1.15, i, f"{v:,}".replace(",", " "), va="center", fontsize=9)
ax.set_xlabel("Lignes concernées (échelle log)")
ax.set_title("Étape 1 · Anomalies détectées par fichier", loc="left", weight="bold")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(IMAGES / "01_diagnostic.png", dpi=150)

# 2. IQR vs seuil métier sur les quantités
q = pd.read_csv(SILVER / "transaction.csv", usecols=["quantity_kg"])["quantity_kg"]
q = q[q > 0]
q1, q3 = q.quantile([0.25, 0.75])
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.hist(q.clip(upper=30), bins=120, color=BLUE)
ax.set_yscale("log")
ax.axvline(q3 + 1.5 * (q3 - q1), color=ORANGE, lw=2)
ax.axvline(20, color=INK, lw=2, ls="--")
ax.text(q3 + 1.5 * (q3 - q1) + 0.3, ax.get_ylim()[1] * 0.3, "Limite IQR ≈ 1,4 kg\n→ 10 570 ventes normales exclues", color=INK, fontsize=9)
ax.text(20.3, ax.get_ylim()[1] * 0.3, "Seuil métier 20 kg\n→ 3 ventes en gros signalées", color=INK, fontsize=9)
ax.set_xlabel("Quantité par ligne de vente (kg, plafonnée à 30)")
ax.set_ylabel("Nombre de ventes (log)")
ax.set_title("Pourquoi un seuil métier plutôt que l'IQR", loc="left", weight="bold")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(IMAGES / "02_iqr_vs_seuil_metier.png", dpi=150)

# 3. Modèle relationnel (tables brutes)
fig, ax = canvas(10, 5.5, "Étape 2 · Modèle relationnel (données brutes)")
t = table_box(ax, 0.2, 5.4, "transaction", ["Date            (FK)", "Time", "Item Code       (FK)",
                                            "Quantity Sold (kilo)", "Unit Selling Price", "Sale or Return",
                                            "Discount (Yes/No)"], BLUE)
p = table_box(ax, 4.6, 6.6, "product", ["Item Code  (PK)", "Item Name", "Category Code", "Category Name"], ORANGE)
pr = table_box(ax, 4.6, 3.0, "price", ["Date       (PK)", "Item Code  (PK, FK)", "Wholesale Price"], BLUE)
lr = table_box(ax, 8.7, 6.6, "loss_rate", ["Item Code  (PK, FK)", "Item Name", "Loss Rate (%)"], BLUE)
link(ax, (3.4, 4.8), (4.6, 6.0))
link(ax, (3.4, 3.4), (4.6, 2.4))
ax.text(3.0, 5.75, "N : 1\nItem Code", ha="center", fontsize=8, color=MUTED)
ax.text(3.6, 1.6, "N : 1\nDate + Item Code", ha="center", fontsize=8, color=MUTED)
link(ax, pr["top"], p["bottom"], "")
ax.text(6.3, 4.2, "N : 1", fontsize=8, color=MUTED)
link(ax, (7.8, 6.0), (8.7, 6.0), "1 : 1")
fig.savefig(IMAGES / "03_modele_relationnel.png", dpi=150, bbox_inches="tight")

# 4. Modèle en étoile (Gold)
fig, ax = canvas(10, 6, "Étape 2 · Modèle en étoile (Gold)")
f = table_box(ax, 4.4, 5.6, "fact_sales", ["datetime", "date            (FK)", "item_code       (FK)",
                                           "quantity_kg", "unit_price", "discount / is_return",
                                           "wholesale_price", "revenue", "purchase_cost", "gross_margin",
                                           "loss_cost_est", "margin_after_loss"], ORANGE, width=3.4)
d = table_box(ax, 0.2, 6.6, "dim_date", ["date   (PK)", "year", "month", "weekday", "period (N / N-1)"], BLUE)
pd_ = table_box(ax, 8.5, 6.6, "dim_product", ["item_code  (PK)", "item_name / item_label", "category_code (FK)",
                                              "loss_rate_pct", "loss_rate_to_check"], BLUE, width=3.3)
c = table_box(ax, 8.5, 2.6, "dim_category", ["category_code (PK)", "category_name"], BLUE, width=3.3)
link(ax, f["left"], d["right"], "N : 1")
link(ax, f["right"], pd_["left"], "N : 1")
link(ax, pd_["bottom"], c["top"], "N : 1")
fig.savefig(IMAGES / "04_modele_etoile.png", dpi=150, bbox_inches="tight")

# 5. Contrôle du résultat : écart de CA par catégorie
kpi = pd.read_csv(GOLD / "kpi_category_n_vs_n1.csv").sort_values("revenue_gap")
fig, ax = plt.subplots(figsize=(9, 3.8))
colors = [ALERT if alert else BLUE for alert in kpi["revenue_alert"]]
ax.barh(kpi["category_name"], kpi["revenue_gap"] / 1000, color=colors, height=0.6)
ax.axvline(0, color=MUTED, lw=1)
for i, (gap, evo) in enumerate(zip(kpi["revenue_gap"], kpi["revenue_evol_pct"])):
    ax.text(gap / 1000 + (1.5 if gap > 0 else -1.5), i, f"{gap / 1000:+.1f} k ({evo:+.0f} %)",
            va="center", ha="left" if gap > 0 else "right", fontsize=9)
for i, alert in enumerate(kpi["revenue_alert"]):
    if alert:
        ax.text(1.5, i, "Alerte : baisse ≥ 15 %", va="center", fontsize=9, weight="bold")
ax.set_xlim(-45, 85)
ax.set_xlabel("Écart de CA N vs N-1 (milliers de RMB)")
ax.set_title("Résultat Gold · Écart de CA par catégorie (07/22–06/23 vs 07/21–06/22)", loc="left", weight="bold")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(IMAGES / "05_ecart_ca_categorie.png", dpi=150)
print("Images :", sorted(x.name for x in IMAGES.glob("*.png")))
