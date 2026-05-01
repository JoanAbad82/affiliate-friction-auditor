#!/usr/bin/env python3
import csv
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from _site_config import load_site_config_from_cli_or_env, pop_cli_option

SITE_LABEL = "Example Affiliate Site"
OUTPUT_SLUG = "example_affiliate_site"
PHASE08_PREFIX = "affiliate_phase0_8_example_affiliate_site_"
PHASE09_PREFIX = "affiliate_phase0_9_example_affiliate_site_"

REQUIRED_08_FILES = [
    "summary.txt",
    "opportunity_matrix_all.csv",
    "opportunity_matrix_deal_posts.csv",
    "hub_opportunity_summary.csv",
    "priority_unique_destinations.csv",
    "priority_unique_deal_posts.csv",
]

OUTPUT_FILES = [
    "summary.txt",
    "product_service_proposal.md",
    "offer_onepager.txt",
    "implementation_backlog.csv",
    "roi_scenarios.csv",
    "sales_assets.md",
    "outreach_email_es.txt",
    "outreach_linkedin_es.txt",
    "client_discovery_questions.txt",
    "validation_notes.txt",
]


def desktop_dir() -> Path:
    for name in ("Escritorio", "Desktop"):
        p = Path.home() / name
        if p.exists():
            return p
    return Path.home()


def read_csv(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def intish(value, default=0) -> int:
    try:
        return int(float(str(value).strip() or default))
    except Exception:
        return default


def floatish(value, default=0.0) -> float:
    try:
        return float(str(value).replace(",", ".").strip() or default)
    except Exception:
        return default


def safe_text(value: str, fallback: str = "") -> str:
    value = str(value or "").strip()
    return value if value else fallback


def has_required_files(folder: Path) -> bool:
    return folder.is_dir() and all((folder / name).exists() for name in REQUIRED_08_FILES)


def find_required_folder_inside(root: Path) -> Path | None:
    if has_required_files(root):
        return root
    for p in root.rglob("*"):
        if has_required_files(p):
            return p
    return None


def extract_zip_to_temp(zip_path: Path) -> Path | None:
    extract_root = Path.cwd() / f"phase0_9_input_extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    extract_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_root)

    direct = find_required_folder_inside(extract_root)
    if direct:
        return direct

    nested_zips = list(extract_root.rglob("*.zip"))
    for nested in nested_zips:
        nested_root = extract_root / f"nested_{nested.stem}"
        nested_root.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(nested, "r") as z:
            z.extractall(nested_root)
        direct = find_required_folder_inside(nested_root)
        if direct:
            return direct

    return None


def find_latest_phase08_input(input_arg: str | None = None) -> Path:
    if input_arg or len(sys.argv) >= 2:
        arg = Path(input_arg or sys.argv[1]).expanduser()
        if arg.is_dir():
            found = find_required_folder_inside(arg)
            if found:
                return found
        if arg.is_file() and arg.suffix.lower() == ".zip":
            found = extract_zip_to_temp(arg)
            if found:
                return found
        print(f"ERROR: el input indicado no contiene los archivos 0.8 requeridos: {arg}", file=sys.stderr)
        sys.exit(2)

    search_roots = [
        Path.cwd(),
        Path.home() / "affiliate_phase0",
        desktop_dir(),
        Path.home() / "Downloads",
        Path.home() / "Descargas",
    ]

    folder_candidates = []
    zip_candidates = []

    seen_roots = set()

    for root in search_roots:
        if not root.exists():
            continue
        try:
            resolved = root.resolve()
        except Exception:
            continue
        if resolved in seen_roots:
            continue
        seen_roots.add(resolved)

        folder_candidates.extend([p for p in root.glob(PHASE08_PREFIX + "*") if has_required_files(p)])
        zip_candidates.extend([p for p in root.glob(PHASE08_PREFIX + "*.zip") if p.is_file()])

    if folder_candidates:
        return max(folder_candidates, key=lambda p: p.stat().st_mtime)

    if zip_candidates:
        latest_zip = max(zip_candidates, key=lambda p: p.stat().st_mtime)
        found = extract_zip_to_temp(latest_zip)
        if found:
            return found

    print("ERROR: no encuentro carpeta ni ZIP de fase 0.8 con los archivos esperados.", file=sys.stderr)
    print(f"Coloca {PHASE08_PREFIX}* en Desktop, Downloads o $HOME/affiliate_phase0.", file=sys.stderr)
    print("También puedes ejecutar:", file=sys.stderr)
    print("python3 scripts/phase0_9_product_offer.py --input /ruta/al/phase0_8_outputs.zip", file=sys.stderr)
    sys.exit(2)


def split_retailers(value: str) -> list[str]:
    if not value:
        return []
    parts = [x.strip() for x in re.split(r",|\|", value) if x.strip()]
    return parts


def pct(n, d) -> str:
    if not d:
        return "0.0%"
    return f"{(100.0 * n / d):.1f}%"


def euro(value: float) -> str:
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def infer_offer_name(total_hubs: int, deal_posts: int, high_count: int) -> str:
    if total_hubs >= 3 and deal_posts >= 20 and high_count >= 10:
        return "Affiliate Hub CTA Optimization Sprint"
    return "Affiliate Monetization Friction Audit"


def build_implementation_backlog(matrix_rows: list[dict]) -> list[dict]:
    backlog = []
    sorted_rows = sorted(
        matrix_rows,
        key=lambda r: (
            -intish(r.get("PriorityScore")),
            r.get("HubUrl", ""),
            r.get("DestinationUrl", ""),
        ),
    )

    for idx, row in enumerate(sorted_rows, start=1):
        opp = row.get("OpportunityType", "")
        status = row.get("CorrectedMonetizationStatus", "")
        kind = row.get("DestinationKind", "")
        eligible = row.get("EligibleDealPost", "")
        score = intish(row.get("PriorityScore"))

        if eligible != "YES":
            task_type = "Exclude or low-priority landing review"
            effort = "XS"
            impact = "Low"
            action = "No implementar CTA comercial automático; revisar solo si hay estrategia específica para landings."
            acceptance = "La URL queda etiquetada como landing/categoría y no contamina el backlog de posts producto."
        elif opp == "DESTINATION_AFFILIATE_GAP":
            task_type = "Destination monetization fix"
            effort = "M"
            impact = "High"
            action = "Revisar el post destino, localizar retailer/programa afiliado válido y añadir CTA/enlace monetizado si procede."
            acceptance = "El post contiene al menos un CTA comercial verificable o queda documentado como no monetizable."
        elif opp.startswith("HUB_CTA_FRICTION"):
            task_type = "Hub card CTA insertion"
            effort = "S"
            impact = "High" if score >= 80 else "Medium"
            action = "Añadir CTA visible en la card/listado del hub apuntando al destino o al enlace comercial autorizado."
            acceptance = "La card muestra CTA claro, consistente y medible; no rompe diseño móvil ni desktop."
        elif opp == "AFFILIATE_LEAK_FIX":
            task_type = "Affiliate leakage fix"
            effort = "S"
            impact = "High"
            action = "Corregir enlace Amazon sin tag, marketplace erróneo o tracking incompleto."
            acceptance = "El enlace final conserva tag/campaign correcto y no usa marketplace incorrecto."
        elif opp == "MANUAL_NETWORK_REVIEW":
            task_type = "Manual redirect/network review"
            effort = "M"
            impact = "Medium"
            action = "Abrir DevTools/redirecciones y verificar si existe monetización real no visible en HTML."
            acceptance = "La URL queda clasificada como monetizada, gap o descartada con evidencia."
        else:
            task_type = "Manual review"
            effort = "S"
            impact = "Medium"
            action = "Revisar manualmente la oportunidad antes de implementar."
            acceptance = "La oportunidad queda aceptada, descartada o convertida en tarea concreta."

        backlog.append({
            "Rank": idx,
            "HubUrl": row.get("HubUrl", ""),
            "DestinationUrl": row.get("DestinationUrl", ""),
            "DestinationKind": kind,
            "OpportunityType": opp,
            "MonetizationStatus": status,
            "PriorityScore": score,
            "PriorityBand": row.get("PriorityBand", ""),
            "TaskType": task_type,
            "RecommendedAction": action,
            "SuggestedCTA": row.get("SuggestedHubCTA", ""),
            "Retailers": row.get("RetailersDetectedCorrected", ""),
            "EstimatedEffort": effort,
            "ExpectedImpact": impact,
            "AcceptanceCriteria": acceptance,
            "Notes": row.get("Notes", ""),
        })

    return backlog


def build_roi_scenarios() -> list[dict]:
    scenarios = [
        {
            "Scenario": "Conservative",
            "MonthlyHubSessions": 25000,
            "CtaExposureRate": 0.55,
            "IncrementalCommercialCtr": 0.006,
            "MerchantConversionRate": 0.018,
            "AverageOrderValueEUR": 65,
            "CommissionRate": 0.030,
        },
        {
            "Scenario": "Base",
            "MonthlyHubSessions": 75000,
            "CtaExposureRate": 0.65,
            "IncrementalCommercialCtr": 0.012,
            "MerchantConversionRate": 0.025,
            "AverageOrderValueEUR": 85,
            "CommissionRate": 0.040,
        },
        {
            "Scenario": "Optimistic",
            "MonthlyHubSessions": 200000,
            "CtaExposureRate": 0.75,
            "IncrementalCommercialCtr": 0.025,
            "MerchantConversionRate": 0.035,
            "AverageOrderValueEUR": 110,
            "CommissionRate": 0.055,
        },
        {
            "Scenario": "High traffic publisher",
            "MonthlyHubSessions": 500000,
            "CtaExposureRate": 0.70,
            "IncrementalCommercialCtr": 0.018,
            "MerchantConversionRate": 0.028,
            "AverageOrderValueEUR": 95,
            "CommissionRate": 0.045,
        },
    ]

    rows = []

    for s in scenarios:
        sessions = s["MonthlyHubSessions"]
        exposed = sessions * s["CtaExposureRate"]
        incremental_clicks = exposed * s["IncrementalCommercialCtr"]
        orders = incremental_clicks * s["MerchantConversionRate"]
        revenue = orders * s["AverageOrderValueEUR"] * s["CommissionRate"]
        annual = revenue * 12

        rows.append({
            **s,
            "EstimatedExposedSessions": round(exposed, 0),
            "EstimatedIncrementalCommercialClicks": round(incremental_clicks, 1),
            "EstimatedIncrementalOrders": round(orders, 2),
            "EstimatedMonthlyAffiliateRevenueEUR": round(revenue, 2),
            "EstimatedAnnualAffiliateRevenueEUR": round(annual, 2),
            "Note": "Modelo orientativo. Sustituir por datos reales de Analytics, CTR afiliado y comisiones del cliente.",
        })

    return rows


def build_markdown_proposal(
    offer_name: str,
    input_dir: Path,
    total_hubs: int,
    matrix_rows: list[dict],
    deal_rows: list[dict],
    unique_deal_rows: list[dict],
    hub_summary_rows: list[dict],
    type_counts: Counter,
    status_counts: Counter,
    retailer_counts: Counter,
    top_rows: list[dict],
) -> str:
    total_rows = len(matrix_rows)
    total_deals = len(deal_rows)
    unique_deals = len(unique_deal_rows)
    high = sum(1 for r in unique_deal_rows if r.get("PriorityBand") == "HIGH")
    gaps = type_counts.get("DESTINATION_AFFILIATE_GAP", 0)
    friction = sum(v for k, v in type_counts.items() if str(k).startswith("HUB_CTA_FRICTION"))

    primary_retailers = ", ".join([name for name, _ in retailer_counts.most_common(5)]) or "No determinado"

    lines = []

    lines.append(f"# {offer_name}")
    lines.append("")
    lines.append("## 1. Qué se vende")
    lines.append("")
    lines.append("Un sprint de optimización para webs de afiliación que detecta cards/listados con intención comercial donde el usuario tiene que entrar primero al post antes de llegar al enlace monetizado.")
    lines.append("")
    lines.append("La propuesta no es “hacer SEO genérico” ni “poner más banners”. Es reducir fricción en hubs comerciales ya existentes mediante CTAs priorizados, medibles y conectados con la monetización real del post destino.")
    lines.append("")
    lines.append("## 2. Evidencia detectada")
    lines.append("")
    lines.append(f"- Web auditada: **{SITE_LABEL}**.")
    lines.append(f"- Input usado: `{input_dir}`.")
    lines.append(f"- Hubs analizados: **{total_hubs}**.")
    lines.append(f"- Filas hub → destino en matriz: **{total_rows}**.")
    lines.append(f"- Deal posts elegibles: **{total_deals}**.")
    lines.append(f"- Deal posts únicos: **{unique_deals}**.")
    lines.append(f"- Oportunidades de fricción hub/listado: **{friction}**.")
    lines.append(f"- Posibles gaps reales en destino: **{gaps}**.")
    lines.append(f"- Deal posts únicos de prioridad HIGH: **{high}**.")
    lines.append(f"- Retailers detectados principales: **{primary_retailers}**.")
    lines.append("")
    lines.append("## 3. Diagnóstico comercial")
    lines.append("")
    lines.append("La evidencia indica que la web ya monetiza en la mayoría de posts destino. El gap más vendible no es rehacer toda la afiliación, sino capturar clics antes, desde las páginas hub/listado.")
    lines.append("")
    lines.append("Esto permite presentar la oportunidad así:")
    lines.append("")
    lines.append("> “Tus posts ya monetizan, pero tus hubs obligan al usuario a hacer un clic intermedio antes de llegar a la oferta. Podemos añadir CTAs medibles en las cards con mayor intención comercial para reducir fricción y aumentar clics comerciales sin cambiar el contenido editorial.”")
    lines.append("")
    lines.append("## 4. Servicio propuesto")
    lines.append("")
    lines.append("### Sprint base")
    lines.append("")
    lines.append("- Auditoría de hubs/listados comerciales.")
    lines.append("- Matriz hub → destino → monetización → retailer → prioridad.")
    lines.append("- Detección de fricción: posts monetizados que no están explotados desde el hub.")
    lines.append("- Detección de gaps: posts comerciales sin enlace afiliado visible.")
    lines.append("- Recomendación de CTA por card.")
    lines.append("- Backlog de implementación priorizado.")
    lines.append("- Plan de medición: CTR de CTA, clic comercial, conversión afiliada cuando haya datos.")
    lines.append("")
    lines.append("### Entregables")
    lines.append("")
    lines.append("- Informe ejecutivo.")
    lines.append("- Matriz CSV priorizada.")
    lines.append("- Backlog implementable.")
    lines.append("- Recomendaciones de copy para CTAs.")
    lines.append("- Checklist QA de enlaces afiliados.")
    lines.append("- Modelo ROI editable con supuestos.")
    lines.append("")
    lines.append("## 5. Alcance recomendado para vender")
    lines.append("")
    lines.append("**Paquete inicial recomendado:** 3 hubs / hasta 30–50 cards auditadas / backlog priorizado / 1 iteración de revisión.")
    lines.append("")
    lines.append("Rango de precio orientativo:")
    lines.append("")
    lines.append("- Auditoría sin implementación: **250–500 €**.")
    lines.append("- Auditoría + backlog + guía de implementación: **500–900 €**.")
    lines.append("- Auditoría + implementación básica + QA: **900–1.800 €**.")
    lines.append("- Monitorización mensual ligera: **150–400 €/mes**.")
    lines.append("")
    lines.append("Estos importes deben ajustarse según tráfico real, CMS, acceso técnico, número de hubs y si el cliente quiere implementación o solo diagnóstico.")
    lines.append("")
    lines.append("## 6. Top oportunidades")
    lines.append("")

    for i, row in enumerate(top_rows[:10], start=1):
        lines.append(f"### {i}. Score {row.get('PriorityScore')} — {row.get('OpportunityType')}")
        lines.append("")
        lines.append(f"- Hub: `{row.get('HubUrl')}`")
        lines.append(f"- Destino: `{row.get('DestinationUrl')}`")
        lines.append(f"- Estado: `{row.get('CorrectedMonetizationStatus')}`")
        lines.append(f"- CTA sugerido: **{row.get('SuggestedHubCTA') or 'Revisar CTA'}**")
        lines.append(f"- Retailers: {row.get('RetailersDetectedCorrected') or 'No detectado'}")
        lines.append(f"- Acción: {row.get('RecommendedAction')}")
        lines.append("")

    lines.append("## 7. Plan de implementación")
    lines.append("")
    lines.append("1. Añadir eventos de medición a CTAs actuales y nuevos.")
    lines.append("2. Implementar CTAs en cards HIGH primero.")
    lines.append("3. Separar landings/categorías de posts producto para evitar ruido.")
    lines.append("4. Revisar el único gap real detectado antes de tocar masivamente el diseño.")
    lines.append("5. Medir 14–30 días: impresiones de card, clic en CTA, clic afiliado, revenue si el panel afiliado lo permite.")
    lines.append("6. Iterar copy/posición del CTA solo con datos.")
    lines.append("")
    lines.append("## 8. Riesgos y límites")
    lines.append("")
    lines.append("- Sin datos reales de tráfico y revenue afiliado, el ROI solo puede modelarse por escenarios.")
    lines.append("- Los enlaces cortos o cloakeados requieren revisión manual si se quiere validar el destino final.")
    lines.append("- Hay que respetar condiciones de programas afiliados, etiquetado publicitario y política editorial.")
    lines.append("- Añadir CTAs no debe degradar UX, Core Web Vitals ni confianza editorial.")
    lines.append("")
    lines.append("## 9. Mensaje de venta resumido")
    lines.append("")
    lines.append("> Detectamos hubs comerciales donde el usuario tiene que abrir un post antes de llegar a la oferta. Si el post ya monetiza, el hub puede capturar más clics comerciales con CTAs visibles y medibles. Entregamos una matriz priorizada y un backlog listo para implementar.")
    lines.append("")

    return "\n".join(lines)


def build_onepager(
    offer_name: str,
    total_hubs: int,
    deal_count: int,
    high_count: int,
    friction_count: int,
    gap_count: int,
    top_hub: str,
) -> str:
    return f"""OFERTA PRODUCTIZADA — {offer_name}

Problema:
Muchas webs de afiliación tienen hubs/listados con intención comercial, pero obligan al usuario a entrar primero al post antes de ver una oferta o CTA monetizado. Eso añade fricción y puede perder clics comerciales.

Qué hacemos:
Auditamos hubs comerciales, cruzamos cada card con su post destino y verificamos si el destino monetiza. Después generamos una matriz priorizada con CTAs recomendados, gaps de afiliación y backlog implementable.

Evidencia del caso analizado:
- Hubs analizados: {total_hubs}
- Deal posts elegibles: {deal_count}
- Prioridad HIGH: {high_count}
- Oportunidades de fricción hub/listado: {friction_count}
- Gaps reales probables en destino: {gap_count}
- Hub más claro: {top_hub or "No determinado"}

Entregables:
1. Matriz hub → destino → monetización → prioridad.
2. Backlog de implementación.
3. CTAs recomendados por card.
4. Detección de fugas/gaps afiliados.
5. Modelo ROI por escenarios.
6. Checklist de medición y QA.

Oferta inicial:
Sprint de 3 hubs / hasta 30–50 cards / informe + matriz + backlog.

Precio orientativo:
- Solo auditoría: 250–500 €
- Auditoría + backlog: 500–900 €
- Auditoría + implementación básica: 900–1.800 €

Promesa prudente:
No prometemos ingresos sin datos. Detectamos fricción monetizable, priorizamos cambios y dejamos un sistema medible para validar uplift real.
"""


def build_sales_assets(offer_name: str, top_rows: list[dict]) -> str:
    hooks = [
        "Tus posts monetizan, pero tus hubs podrían estar perdiendo clics comerciales.",
        "No necesitas más banners: necesitas menos fricción entre intención comercial y oferta.",
        "Si el usuario ya está en un listado de ofertas, hacerle entrar al post antes del CTA puede costarte clics.",
        "Convertimos hubs de afiliación en matrices accionables: card, destino, retailer, CTA y prioridad.",
        "Primero medimos dónde hay fricción; después proponemos CTAs donde hay evidencia.",
    ]

    objection_handling = [
        ("“Ya tenemos enlaces afiliados”", "Precisamente: el servicio detecta si esos enlaces están enterrados en el post y no visibles desde el hub."),
        ("“No queremos llenar la web de botones”", "La propuesta es priorizada: solo cards con intención alta y destino monetizado o gap claro."),
        ("“No sabemos si aumentará ingresos”", "Por eso se entrega con plan de medición y escenarios ROI, no con promesas absolutas."),
        ("“Nuestro CMS es limitado”", "Puede empezar como guía de copy/posición o implementación manual en los hubs principales."),
        ("“Nos preocupa la confianza editorial”", "Los CTAs deben ser claros, moderados y alineados con la intención del listado, no banners intrusivos."),
    ]

    lines = []
    lines.append(f"# Sales assets — {offer_name}")
    lines.append("")
    lines.append("## Hooks")
    lines.append("")
    for h in hooks:
        lines.append(f"- {h}")
    lines.append("")
    lines.append("## Objeciones y respuestas")
    lines.append("")
    for obj, ans in objection_handling:
        lines.append(f"**{obj}**  ")
        lines.append(f"{ans}")
        lines.append("")
    lines.append("## Ejemplos de oportunidades detectadas")
    lines.append("")
    for row in top_rows[:8]:
        lines.append(f"- Score {row.get('PriorityScore')}: {row.get('DestinationUrl')} → {row.get('SuggestedHubCTA')}")
    lines.append("")
    lines.append("## Claim principal")
    lines.append("")
    lines.append("> Reducimos fricción entre hubs comerciales y enlaces monetizados, usando evidencia real de cada card y cada post destino.")
    lines.append("")
    return "\n".join(lines)


def build_outreach_email(offer_name: str, total_hubs: int, high_count: int, gap_count: int) -> str:
    return f"""Asunto: Oportunidad rápida para mejorar CTAs en hubs de afiliación

Hola,

He estado analizando una forma muy concreta de mejorar webs de afiliación sin rehacer contenido ni meter más banners: detectar hubs/listados donde los posts destino ya monetizan, pero la página hub obliga al usuario a hacer un clic intermedio antes de llegar a la oferta.

En un caso de prueba he cruzado {total_hubs} hubs con sus posts destino y he generado una matriz de oportunidades. La señal más clara no era “falta de afiliación”, sino fricción: muchas cards llevan a posts que ya monetizan, pero el CTA comercial no está visible desde el hub. También apareció algún gap puntual de afiliación en destino.

Estoy empaquetando esto como un {offer_name}: auditoría + matriz priorizada + CTAs sugeridos + backlog de implementación.

Creo que puede ser útil para webs de ofertas, reviews, cupones o comparativas que ya tienen tráfico y programas afiliados activos.

Si te interesa, puedo enseñarte un ejemplo de la matriz y cómo quedaría aplicado a 2–3 hubs.

Un saludo,
"""


def build_linkedin_message() -> str:
    return """Hola, estoy trabajando en una auditoría muy concreta para webs de afiliación: detectar hubs/listados donde los posts destino ya monetizan, pero el CTA comercial queda demasiado escondido.

La idea no es añadir banners, sino reducir fricción con una matriz hub → destino → retailer → CTA → prioridad.

Creo que puede encajar en webs de ofertas/reviews con tráfico existente. ¿Te puedo enviar un ejemplo breve?"""


def build_discovery_questions() -> str:
    questions = [
        "¿Qué hubs/listados generan más tráfico orgánico actualmente?",
        "¿Tenéis eventos medidos para clics en cards, clics en CTA y clics afiliados?",
        "¿Qué programas afiliados usáis: Amazon, AliExpress, Awin, TradeDoubler, Impact, otros?",
        "¿El CMS permite añadir CTAs por card en listados o requiere desarrollo?",
        "¿Tenéis datos de revenue por URL o solo por programa afiliado?",
        "¿Hay restricciones editoriales sobre botones, precio, tiendas o disclosure publicitario?",
        "¿Qué porcentaje de tráfico es móvil?",
        "¿Cuáles son los 3 hubs que más os interesa monetizar primero?",
        "¿Queréis solo auditoría o también implementación?",
        "¿Hay páginas donde no queréis tocar diseño aunque haya oportunidad?",
    ]

    return "\n".join([f"{i}. {q}" for i, q in enumerate(questions, start=1)])


def main():
    load_site_config_from_cli_or_env(globals())
    input_arg = pop_cli_option(sys.argv, "--input")
    input_dir = find_latest_phase08_input(input_arg)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = desktop_dir() / f"{PHASE09_PREFIX}{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    matrix_all = read_csv(input_dir / "opportunity_matrix_all.csv")
    matrix_deals = read_csv(input_dir / "opportunity_matrix_deal_posts.csv")
    hub_summary = read_csv(input_dir / "hub_opportunity_summary.csv")
    priority_unique = read_csv(input_dir / "priority_unique_destinations.csv")
    priority_unique_deals = read_csv(input_dir / "priority_unique_deal_posts.csv")

    total_hubs = len(hub_summary)
    total_rows = len(matrix_all)
    deal_count = len(matrix_deals)
    unique_deal_count = len(priority_unique_deals)

    type_counts = Counter([r.get("OpportunityType", "") for r in matrix_deals])
    status_counts = Counter([r.get("CorrectedMonetizationStatus", "") for r in matrix_deals])
    band_counts = Counter([r.get("PriorityBand", "") for r in priority_unique_deals])

    retailer_counts = Counter()
    for r in priority_unique_deals:
        for retailer in split_retailers(r.get("RetailersDetectedCorrected", "")):
            retailer_counts[retailer] += 1

    high_count = band_counts.get("HIGH", 0)
    friction_count = sum(v for k, v in type_counts.items() if str(k).startswith("HUB_CTA_FRICTION"))
    gap_count = type_counts.get("DESTINATION_AFFILIATE_GAP", 0)

    top_rows = sorted(priority_unique_deals, key=lambda r: -intish(r.get("PriorityScore")))[:20]

    top_hub = ""
    if hub_summary:
        top_hub_row = sorted(hub_summary, key=lambda r: -floatish(r.get("AverageDealPostPriorityScore")))[0]
        top_hub = top_hub_row.get("HubUrl", "")

    offer_name = infer_offer_name(total_hubs, deal_count, high_count)

    backlog = build_implementation_backlog(matrix_deals)
    roi_rows = build_roi_scenarios()

    proposal_md = build_markdown_proposal(
        offer_name=offer_name,
        input_dir=input_dir,
        total_hubs=total_hubs,
        matrix_rows=matrix_all,
        deal_rows=matrix_deals,
        unique_deal_rows=priority_unique_deals,
        hub_summary_rows=hub_summary,
        type_counts=type_counts,
        status_counts=status_counts,
        retailer_counts=retailer_counts,
        top_rows=top_rows,
    )

    onepager = build_onepager(
        offer_name=offer_name,
        total_hubs=total_hubs,
        deal_count=deal_count,
        high_count=high_count,
        friction_count=friction_count,
        gap_count=gap_count,
        top_hub=top_hub,
    )

    sales_assets = build_sales_assets(offer_name, top_rows)
    outreach_email = build_outreach_email(offer_name, total_hubs, high_count, gap_count)
    outreach_linkedin = build_linkedin_message()
    discovery_questions = build_discovery_questions()

    validation_notes = f"""VALIDATION NOTES — FASE 0.9

Input usado:
{input_dir}

Archivos 0.8 consumidos:
- opportunity_matrix_all.csv: {len(matrix_all)} filas
- opportunity_matrix_deal_posts.csv: {len(matrix_deals)} filas
- hub_opportunity_summary.csv: {len(hub_summary)} filas
- priority_unique_destinations.csv: {len(priority_unique)} filas
- priority_unique_deal_posts.csv: {len(priority_unique_deals)} filas

Transformación realizada:
- Se convierte la matriz técnica en oferta comercial.
- Se genera backlog implementable.
- Se generan escenarios ROI orientativos.
- Se generan assets de venta y outreach.
- No se hace nuevo crawling.
- No se prometen ingresos; se propone validación con medición.

Advertencia:
El ROI requiere datos reales de tráfico, CTR, conversión y comisión. Los escenarios incluidos son plantillas de sensibilidad, no previsiones garantizadas.
"""

    summary_lines = []
    summary_lines.append("FASE 0.9 — CONVERSION DE MATRIZ EN PROPUESTA PRODUCTO/SERVICIO")
    summary_lines.append(f"Web base: {SITE_LABEL}")
    summary_lines.append(f"Oferta propuesta: {offer_name}")
    summary_lines.append(f"Input 0.8 usado: {input_dir}")
    summary_lines.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_lines.append("")
    summary_lines.append("RESUMEN COMERCIAL")
    summary_lines.append(f"- Hubs analizados: {total_hubs}")
    summary_lines.append(f"- Filas hub -> destino: {total_rows}")
    summary_lines.append(f"- Deal posts elegibles: {deal_count}")
    summary_lines.append(f"- Deal posts unicos: {unique_deal_count}")
    summary_lines.append(f"- Deal posts HIGH: {high_count}")
    summary_lines.append(f"- Oportunidades de friccion hub/listado: {friction_count}")
    summary_lines.append(f"- Gaps reales probables en destino: {gap_count}")
    summary_lines.append(f"- Hub mas claro por score medio: {top_hub or 'No determinado'}")
    summary_lines.append("")
    summary_lines.append("TIPOS DE OPORTUNIDAD")
    for k, v in sorted(type_counts.items()):
        summary_lines.append(f"- {k}: {v}")
    summary_lines.append("")
    summary_lines.append("ESTADOS DE MONETIZACION")
    for k, v in sorted(status_counts.items()):
        summary_lines.append(f"- {k}: {v}")
    summary_lines.append("")
    summary_lines.append("RETAILERS PRINCIPALES")
    for k, v in retailer_counts.most_common(10):
        summary_lines.append(f"- {k}: {v}")
    summary_lines.append("")
    summary_lines.append("TOP 10 OPORTUNIDADES VENDIBLES")
    for r in top_rows[:10]:
        summary_lines.append(
            f"- score={r.get('PriorityScore')} | {r.get('OpportunityType')} | "
            f"CTA='{r.get('SuggestedHubCTA')}' | {r.get('DestinationUrl')}"
        )
    summary_lines.append("")
    summary_lines.append("ARCHIVOS GENERADOS")
    for name in OUTPUT_FILES:
        summary_lines.append(f"- {name}")
    summary_lines.append("")
    summary_lines.append("DICTAMEN")
    summary_lines.append("La propuesta vendible no debe posicionarse como SEO general ni auditoria generica.")
    summary_lines.append("Debe posicionarse como optimizacion de friccion afiliada en hubs/listados ya existentes.")
    summary_lines.append("El claim prudente: detectar, priorizar e implementar CTAs medibles donde ya hay evidencia de monetizacion o intencion comercial.")

    (out_dir / "summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")
    (out_dir / "product_service_proposal.md").write_text(proposal_md, encoding="utf-8")
    (out_dir / "offer_onepager.txt").write_text(onepager, encoding="utf-8")
    (out_dir / "sales_assets.md").write_text(sales_assets, encoding="utf-8")
    (out_dir / "outreach_email_es.txt").write_text(outreach_email, encoding="utf-8")
    (out_dir / "outreach_linkedin_es.txt").write_text(outreach_linkedin, encoding="utf-8")
    (out_dir / "client_discovery_questions.txt").write_text(discovery_questions, encoding="utf-8")
    (out_dir / "validation_notes.txt").write_text(validation_notes, encoding="utf-8")

    write_csv(
        out_dir / "implementation_backlog.csv",
        backlog,
        [
            "Rank",
            "HubUrl",
            "DestinationUrl",
            "DestinationKind",
            "OpportunityType",
            "MonetizationStatus",
            "PriorityScore",
            "PriorityBand",
            "TaskType",
            "RecommendedAction",
            "SuggestedCTA",
            "Retailers",
            "EstimatedEffort",
            "ExpectedImpact",
            "AcceptanceCriteria",
            "Notes",
        ],
    )

    write_csv(
        out_dir / "roi_scenarios.csv",
        roi_rows,
        [
            "Scenario",
            "MonthlyHubSessions",
            "CtaExposureRate",
            "IncrementalCommercialCtr",
            "MerchantConversionRate",
            "AverageOrderValueEUR",
            "CommissionRate",
            "EstimatedExposedSessions",
            "EstimatedIncrementalCommercialClicks",
            "EstimatedIncrementalOrders",
            "EstimatedMonthlyAffiliateRevenueEUR",
            "EstimatedAnnualAffiliateRevenueEUR",
            "Note",
        ],
    )

    zip_path = out_dir / "phase0_9_outputs.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in OUTPUT_FILES:
            z.write(out_dir / name, arcname=name)

    print()
    print("=" * 70)
    print("RESUMEN FASE 0.9")
    print("=" * 70)
    print((out_dir / "summary.txt").read_text(encoding="utf-8"))
    print()
    print("Archivos generados en:")
    print(out_dir)
    print()
    print("ZIP para subir:")
    print(zip_path)
    print()


if __name__ == "__main__":
    main()
