"""Gold -> docs/Comex_produits_frais.pptx : 5 slides + 1 annexe, graphiques natifs (modifiables dans PowerPoint)."""
import pandas as pd
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from paths import ALERT_THRESHOLD_PCT, GOLD, ROOT

# Même palette que le dashboard et les images du README
INK, DARK, WHITE = RGBColor(0x0B, 0x0B, 0x0B), RGBColor(0x1A, 0x1A, 0x19), RGBColor(0xFF, 0xFF, 0xFF)
BLUE, RED, GREY = RGBColor(0x2A, 0x78, 0xD6), RGBColor(0xD0, 0x3B, 0x3B), RGBColor(0xA3, 0xA2, 0x9C)
MUTED, LIGHT_MUTED, TINT = RGBColor(0x52, 0x51, 0x4E), RGBColor(0xC3, 0xC2, 0xB7), RGBColor(0xF4, 0xF4, 0xF1)
FONT = "Calibri"
MONTHS = ["juil.", "août", "sept.", "oct.", "nov.", "déc.", "janv.", "févr.", "mars", "avr.", "mai", "juin"]

# ---------------------------------------------------------------- chiffres (tous lus dans le Gold)
fact = pd.read_csv(GOLD / "fact_sales.csv", dtype={"item_code": str}, parse_dates=["date"])
dim_product = pd.read_csv(GOLD / "dim_product.csv", dtype={"item_code": str, "category_code": str})
dim_category = pd.read_csv(GOLD / "dim_category.csv", dtype={"category_code": str})
dim_date = pd.read_csv(GOLD / "dim_date.csv", parse_dates=["date"])
kpi = pd.read_csv(GOLD / "kpi_category_n_vs_n1.csv").set_index("category_name")

sales = (fact.merge(dim_date[["date", "month", "period"]], on="date")
             .merge(dim_product[["item_code", "item_label", "category_code"]], on="item_code")
             .merge(dim_category, on="category_code")
             .query("period != 'hors période'"))
total = sales.groupby("period")[["revenue", "gross_margin", "quantity_kg"]].sum()
evol_total = (total.loc["N"] / total.loc["N-1"] - 1) * 100

alerts = kpi[kpi["revenue_alert"]].index.tolist()
assert alerts == ["Solanum"], f"le récit des slides suppose Solanum seule en alerte, trouvé : {alerts}"
sol = kpi.loc["Solanum"]
sol_sales = sales[sales["category_name"] == "Solanum"]
sol_period = sol_sales.groupby("period").agg(ca=("revenue", "sum"), kg=("quantity_kg", "sum"),
                                             promo=("discount", "mean"))
price_kg = sol_period["ca"] / sol_period["kg"]
sol_month = sol_sales.groupby(["period", "month"])["revenue"].sum()
sol_products = (sol_sales.groupby(["item_label", "period"])["revenue"].sum().unstack(fill_value=0)
                .assign(gap=lambda d: d["N"] - d["N-1"]).sort_values("gap"))
top2 = sol_products.head(2)
flower = sales[sales["category_name"] == "Flower/Leaf Vegetables"].groupby("period")[["revenue", "quantity_kg"]].sum()
flower_price_evol = ((flower["revenue"] / flower["quantity_kg"]).pipe(lambda s: s["N"] / s["N-1"] - 1) * 100)


def pct(v):
    return f"{'+' if v > 0 else '−' if v < 0 else ''}{abs(v):.1f} %".replace(".", ",")


def k(v):
    return f"{'+' if v > 0 else '−' if v < 0 else ''}{abs(v) / 1000:.1f} k".replace(".", ",")


# ---------------------------------------------------------------- mise en page
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
MARGIN = Inches(0.6)
CONTENT_W = prs.slide_width - 2 * MARGIN


def textbox(slide, x, y, w, h, runs, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """runs = texte simple, ou liste de paragraphes ; chaque paragraphe = liste de (texte, options)."""
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    paragraphs = [[(runs, {})]] if isinstance(runs, str) else runs
    for i, para in enumerate(paragraphs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(8)
        for txt, opt in para:
            r = p.add_run()
            r.text = txt
            r.font.name = FONT
            r.font.size = Pt(opt.get("size", size))
            r.font.bold = opt.get("bold", bold)
            r.font.color.rgb = opt.get("color", color)
    return box


def new_slide(question, title, dark=False):
    slide = prs.slides.add_slide(BLANK)
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = DARK if dark else WHITE
    if question:
        textbox(slide, MARGIN, Inches(0.45), CONTENT_W, Inches(0.4), question.upper(), size=12, bold=True,
                color=LIGHT_MUTED if dark else MUTED)
    textbox(slide, MARGIN, Inches(0.8), CONTENT_W, Inches(1.2), title, size=30, bold=True,
            color=WHITE if dark else INK)
    return slide


def stat(slide, x, y, w, value, label, color=INK, label_color=MUTED, fill=TINT):
    """Tuile chiffre clé : gros nombre + légende."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, Inches(1.45))
    card.adjustments[0] = 0.08
    card.fill.solid()
    card.fill.fore_color.rgb = fill
    card.line.fill.background()
    card.shadow.inherit = False
    textbox(slide, x + Inches(0.25), y + Inches(0.18), w - Inches(0.5), Inches(0.7), value, size=34, bold=True, color=color)
    textbox(slide, x + Inches(0.25), y + Inches(0.88), w - Inches(0.5), Inches(0.5), label, size=13, color=label_color)


def footer(slide, txt, dark=False):
    textbox(slide, MARGIN, Inches(7.0), CONTENT_W, Inches(0.3), txt, size=10, color=LIGHT_MUTED if dark else MUTED)


def style_chart(chart):
    chart.font.name = FONT
    chart.font.size = Pt(12)
    chart.font.color.rgb = MUTED
    chart.has_title = False


def bar_chart(slide, x, y, w, h, labels, values, colors, number_format):
    data = CategoryChartData()
    data.categories = labels
    data.add_series("valeur", values)
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, x, y, w, h, data).chart
    style_chart(chart)
    chart.has_legend = False
    plot = chart.plots[0]
    plot.gap_width = 60
    plot.has_data_labels = True
    labels_ = plot.data_labels
    labels_.number_format, labels_.number_format_is_linked = number_format, False
    labels_.position = XL_LABEL_POSITION.OUTSIDE_END
    labels_.font.size, labels_.font.color.rgb = Pt(12), INK
    for i, c in enumerate(colors):
        point = plot.series[0].points[i]
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = c
    va = chart.value_axis
    va.visible = False
    va.has_major_gridlines = False
    ca = chart.category_axis
    ca.format.line.color.rgb = LIGHT_MUTED
    ca.tick_labels.font.size, ca.tick_labels.font.color.rgb = Pt(12), INK
    # étiquettes de catégories à gauche du graphique, même pour les barres négatives
    ca._element.get_or_add_tickLblPos().set("val", "low")
    return chart


# ---------------------------------------------------------------- 1. Titre + réponse en une phrase
s = new_slide(None, "Produits frais : le problème est ciblé, une seule catégorie est en alerte", dark=True)
textbox(s, MARGIN, Inches(2.0), CONTENT_W, Inches(0.5),
        "Ventes magasin · 12 derniers mois (07/2022 – 06/2023) comparés à N-1 · Comex", size=16, color=LIGHT_MUTED)
stat(s, MARGIN, Inches(3.2), Inches(3.8), pct(evol_total["revenue"]), "CA total magasin vs N-1",
     color=WHITE, label_color=LIGHT_MUTED, fill=RGBColor(0x2C, 0x2C, 0x2A))
stat(s, MARGIN + Inches(4.1), Inches(3.2), Inches(3.8), pct(sol["revenue_evol_pct"]), "CA Solanum vs N-1 (seuil : −15 %)",
     color=RGBColor(0xE6, 0x67, 0x67), label_color=LIGHT_MUTED, fill=RGBColor(0x2C, 0x2C, 0x2A))
stat(s, MARGIN + Inches(8.2), Inches(3.2), Inches(3.9), "2 produits", "expliquent la baisse de Solanum",
     color=WHITE, label_color=LIGHT_MUTED, fill=RGBColor(0x2C, 0x2C, 0x2A))
textbox(s, MARGIN, Inches(5.2), CONTENT_W, Inches(0.8),
        [[("Recommandation : ", {"bold": True, "color": WHITE}),
          (f"relancer {top2.index[0]} et {top2.index[1]} avant septembre 2023.", {"color": WHITE})]], size=20)
footer(s, "Source : caisses magasin, prix de gros du jour, référentiel produit · données au 30/06/2023", dark=True)
s.notes_slide.notes_text_frame.text = (
    "Le message en une phrase : les ventes de produits frais ne baissent pas globalement, le CA progresse de "
    f"{pct(evol_total['revenue'])}. Une seule catégorie passe sous le seuil d'alerte fixé par le Comex : Solanum. "
    "Et deux produits expliquent cette baisse. Je vous montre pourquoi, puis ce qu'on recommande.")

# ---------------------------------------------------------------- 2. Qui baisse ?
s = new_slide("Les ventes de produits frais reculent-elles ?",
              f"Non : le CA progresse de {pct(evol_total['revenue'])}, seule Solanum passe sous le seuil de −15 %")
order = kpi.sort_values("revenue_evol_pct", ascending=False)
chart = bar_chart(s, MARGIN, Inches(2.4), Inches(7.6), Inches(4.4), order.index.tolist(),
                  order["revenue_evol_pct"].tolist(),
                  [RED if a else BLUE for a in order["revenue_alert"]], '+0.0" %";−0.0" %"')
textbox(s, MARGIN, Inches(2.05), Inches(7.6), Inches(0.3), "Évolution du CA vs N-1, par catégorie (en rouge : alerte)",
        size=13, color=MUTED)
x_side = MARGIN + Inches(8.1)
for i, (col, label) in enumerate([("revenue", "CA total"), ("gross_margin", "Marge brute totale"),
                                  ("quantity_kg", "Volume total (kg)")]):
    stat(s, x_side, Inches(2.4) + i * Inches(1.55), Inches(4.0), pct(evol_total[col]), f"{label} vs N-1")
footer(s, "Seuil d'alerte Comex : baisse de 15 % ou plus vs N-1. Marge brute = CA − kg vendus × prix de gros du jour.")
s.notes_slide.notes_text_frame.text = (
    "Question : est-ce que les produits frais reculent ? Non. CA, marge et volume progressent tous. "
    "Sur les 6 catégories, 5 progressent de 17 à 50 %. Une seule, Solanum, recule de "
    f"{pct(sol['revenue_evol_pct'])}, au-delà du seuil de −15 % fixé par le Comex. C'est là qu'il faut agir.")

# ---------------------------------------------------------------- 3. Pourquoi Solanum baisse ?
s = new_slide("Pourquoi Solanum baisse-t-elle ?",
              "Solanum perd du volume, pas du prix : le décrochage se concentre de septembre à décembre 2022")
stat(s, MARGIN, Inches(2.4), Inches(3.6), pct(sol["quantity_kg_evol_pct"]), "Volume vendu vs N-1", color=RED)
stat(s, MARGIN, Inches(3.85), Inches(3.6), pct((price_kg["N"] / price_kg["N-1"] - 1) * 100),
     f"Prix moyen : {price_kg['N-1']:.2f} → {price_kg['N']:.2f} RMB/kg".replace(".", ","))
stat(s, MARGIN, Inches(5.3), Inches(3.6), pct(sol["gross_margin_evol_pct"]), "Marge brute vs N-1", color=RED)
data = CategoryChartData()
data.categories = MONTHS
data.add_series("N-1 (07/21 – 06/22)", (sol_month["N-1"] / 1000).round(1).tolist())
data.add_series("N (07/22 – 06/23)", (sol_month["N"] / 1000).round(1).tolist())
gf = s.shapes.add_chart(XL_CHART_TYPE.LINE, MARGIN + Inches(4.1), Inches(2.4), Inches(8.0), Inches(4.4), data)
chart = gf.chart
style_chart(chart)
chart.has_legend = True
chart.legend.position = XL_LEGEND_POSITION.TOP
chart.legend.include_in_layout = False
chart.legend.font.size = Pt(12)
for series, color in zip(chart.plots[0].series, [GREY, BLUE]):
    series.smooth = False
    series.marker.style = XL_MARKER_STYLE.NONE
    series.format.line.color.rgb = color
    series.format.line.width = Pt(2.5)
va = chart.value_axis
va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = RGBColor(0xE1, 0xE0, 0xD9)
va.format.line.fill.background()
va.tick_labels.number_format, va.tick_labels.number_format_is_linked = '0" k"', False
chart.category_axis.format.line.color.rgb = LIGHT_MUTED
textbox(s, MARGIN + Inches(4.1), Inches(2.05), Inches(8.0), Inches(0.3), "CA mensuel Solanum (k RMB)", size=13, color=MUTED)
footer(s, "Prix moyen = CA / kg vendus. Le prix au kg ne bouge presque pas : c'est la quantité vendue qui chute.")
s.notes_slide.notes_text_frame.text = (
    "Pourquoi Solanum baisse ? Le prix moyen au kilo est stable, autour de 9 RMB. Ce sont les kilos vendus "
    f"qui chutent, {pct(sol['quantity_kg_evol_pct'])}. Sur la courbe, on voit que tout se joue de septembre à "
    "décembre 2022 : le CA mensuel tombe entre 1,1 et 1,7 k contre 2,5 à 5,7 k l'année d'avant. Ça repart en janvier, "
    "mais il faut attendre juin 2023 pour retrouver le niveau de N-1.")

# ---------------------------------------------------------------- 4. Quels produits ?
s = new_slide("Quels produits font baisser Solanum ?",
              f"Deux produits expliquent toute la baisse : {top2.index[0]} et {top2.index[1]}")
chart = bar_chart(s, MARGIN, Inches(2.4), Inches(7.6), Inches(4.4), sol_products.index[::-1].tolist(),
                  (sol_products["gap"][::-1] / 1000).round(1).tolist(),
                  [RED if g < 0 else BLUE for g in sol_products["gap"][::-1]], '+0.0" k";−0.0" k"')
textbox(s, MARGIN, Inches(2.05), Inches(7.6), Inches(0.3), "Écart de CA vs N-1 par produit Solanum (k RMB)",
        size=13, color=MUTED)
stat(s, x_side, Inches(2.4), Inches(4.0), k(top2["gap"].sum()) + " RMB", f"sur ces 2 produits, pour {k(sol['revenue_gap'])} sur toute la catégorie", color=RED)
textbox(s, x_side, Inches(4.1), Inches(4.0), Inches(2.6),
        [[(f"{top2.index[0]} : ", {"bold": True}),
          (f"{pct((top2['N'].iloc[0] / top2['N-1'].iloc[0] - 1) * 100)} de CA", {})],
         [(f"{top2.index[1]} : ", {"bold": True}),
          (f"{pct((top2['N'].iloc[1] / top2['N-1'].iloc[1] - 1) * 100)} de CA, 1er produit de la catégorie", {})],
         [("Les nouveaux produits (Eggplant (1), Green Eggplant (2)) compensent une petite partie.",
           {"color": MUTED})]], size=15)
footer(s, "Agrégation par code produit : (1) et (2) distinguent deux produits différents portant le même nom.")
s.notes_slide.notes_text_frame.text = (
    f"Quels produits ? Deux produits pèsent {k(top2['gap'].sum())} RMB, soit plus que la baisse totale de la "
    "catégorie : les nouveaux produits compensent un peu. Changxianqie perd près des trois quarts de son CA. "
    "Eggplant (2), le premier produit de la catégorie, perd près d'un quart.")

# ---------------------------------------------------------------- 5. Recommandation
s = new_slide("Que faire ?", f"Relancer {top2.index[0]} et {top2.index[1]} avant septembre 2023", dark=True)
actions = [
    ("1", "Comprendre", "Vérifier avec les achats la disponibilité des 2 produits de septembre à décembre 2022 "
                        "(rupture, déréférencement, fournisseur ?)."),
    ("2", "Tester", f"Remettre des promos sur Solanum : {sol_period['promo']['N'] * 100:.1f} % des ventes en promo "
                    f"en N contre {sol_period['promo']['N-1'] * 100:.1f} % en N-1. Hypothèse, à mesurer sur 2 mois."
                    .replace(".", ",", 2)),
    ("3", "Suivre", "Chaque mois dans le dashboard : alerte automatique dès qu'une catégorie baisse de 15 % ou plus."),
]
for i, (num, head, body) in enumerate(actions):
    x = MARGIN + i * Inches(4.1)
    card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(2.2), Inches(3.85), Inches(3.3))
    card.adjustments[0] = 0.06
    card.fill.solid()
    card.fill.fore_color.rgb = RGBColor(0x2C, 0x2C, 0x2A)
    card.line.fill.background()
    circle = s.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(0.3), Inches(2.5), Inches(0.6), Inches(0.6))
    circle.fill.solid()
    circle.fill.fore_color.rgb = BLUE
    circle.line.fill.background()
    textbox(s, x + Inches(0.3), Inches(2.5), Inches(0.6), Inches(0.6), num, size=20, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    textbox(s, x + Inches(1.05), Inches(2.55), Inches(2.6), Inches(0.5), head, size=20, bold=True, color=WHITE)
    textbox(s, x + Inches(0.3), Inches(3.35), Inches(3.3), Inches(2.0), body, size=15, color=LIGHT_MUTED)
textbox(s, MARGIN, Inches(5.85), CONTENT_W, Inches(0.8),
        [[("Point de vigilance : ", {"bold": True, "color": WHITE}),
          (f"Flower/Leaf n'est pas en alerte, mais son prix moyen au kg baisse de {pct(flower_price_evol)} "
           "(son coût d'achat baisse autant, la marge suit).", {"color": LIGHT_MUTED})]], size=15)
s.notes_slide.notes_text_frame.text = (
    "Ce qu'on recommande, en 3 temps. Un : comprendre pourquoi ces 2 produits ont décroché à l'automne. "
    "Les données ne disent pas si c'est une rupture ou un choix d'assortiment, il faut demander aux achats. "
    "Deux : tester le retour des promos, qui ont quasiment disparu sur Solanum. C'est une hypothèse, pas une "
    "certitude, donc on la mesure. Trois : suivre chaque mois avec le dashboard. "
    "Enfin, on garde un œil sur Flower/Leaf, dont le prix au kilo baisse.")

# ---------------------------------------------------------------- 6. Annexe méthode
s = new_slide("Annexe", "Méthode et limites")
rows = [
    ("Périmètre", "Ventes magasin (caisse). N = 07/2022 – 06/2023, N-1 = 07/2021 – 06/2022 : les données s'arrêtent au 30/06/2023."),
    ("KPI", "CA, marge brute, volume vendu, écart en valeur et évolution en % vs N-1. Alerte si baisse ≥ 15 %."),
    ("Marge", "CA − kg vendus × prix de gros du jour. Elle n'inclut pas les pertes (à valider avec le Comex)."),
    ("Nettoyage", "461 retours déduits du CA, 53 prix de gros quasi nuls remplacés, catégories et noms harmonisés."),
    ("Limite", "La donnée montre quand et où les ventes baissent, pas pourquoi : la cause est à confirmer avec les achats."),
    ("Sources", "Dashboard interactif : docs/dashboard.html · code : github.com/romane13long-source/produits-frais-analytics"),
]
for i, (head, body) in enumerate(rows):
    y = Inches(2.0) + i * Inches(0.8)
    textbox(s, MARGIN, y, Inches(2.2), Inches(0.7), head, size=15, bold=True)
    textbox(s, MARGIN + Inches(2.4), y, CONTENT_W - Inches(2.4), Inches(0.7), body, size=15, color=MUTED)

out = ROOT / "docs" / "Comex_produits_frais.pptx"
prs.save(out)
print(f"{out.relative_to(ROOT)} : {len(prs.slides)} slides (alerte : {', '.join(alerts)}, seuil {ALERT_THRESHOLD_PCT} %)")
