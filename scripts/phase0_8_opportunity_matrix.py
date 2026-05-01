#!/usr/bin/env python3
import csv
import re
import sys
import zipfile
import urllib.parse
from collections import defaultdict
from datetime import datetime
from pathlib import Path

SITE_LABEL = "Nolodejesescapar"
ROOT_HOST = "nolodejesescapar.com"
PHASE07_PREFIX = "affiliate_phase0_7_nolodejesescapar_"
PHASE08_PREFIX = "affiliate_phase0_8_nolodejesescapar_"

REQUIRED_FILES = [
    "summary.txt",
    "hub_summary.csv",
    "hub_destinations.csv",
    "destination_validation.csv",
    "destination_links.csv",
    "destination_network_requests.csv",
]

REFINED_INTERNAL_CLOAK_RE = re.compile(
    r"/(go|ir|out|outgoing|comprar|compra|tienda|redirect|recommends|recomienda|link|links|cupon|coupon)(/|$|\?|-)",
    re.I,
)

SOCIAL_OR_UTILITY_HOST_RE = re.compile(
    r"(^|\.)(facebook|instagram|twitter|x|youtube|youtu|tiktok|pinterest|whatsapp|telegram|linkedin|google|gstatic|googleapis|gravatar)\.",
    re.I,
)

HIGH_INTENT_RE = re.compile(
    r"oferta|ofertas|chollo|chollos|rebaja|descuento|precio|comprar|cup[oó]n|amazon|aliexpress|pccomponentes|mediamarkt|miravia|€|smartphone|drone|teclado|monitor|ssd|auriculares|xiaomi|samsung|realme|oppo|poco|dji",
    re.I,
)

BRAND_OR_RETAILER_LANDING_SLUGS = {
    "amazon",
    "aliexpress",
    "xiaomi",
    "samsung",
    "realme",
    "oppo",
    "mediamarkt",
    "pccomponentes",
}


def desktop_dir() -> Path:
    for name in ("Escritorio", "Desktop"):
        p = Path.home() / name
        if p.exists():
            return p
    return Path.home()


def boolish(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "si", "sí"}


def intish(value, default=0) -> int:
    try:
        return int(float(str(value).strip() or default))
    except Exception:
        return default


def canonical_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(str(url).strip())
        parsed = parsed._replace(fragment="")
        return urllib.parse.urlunparse(parsed).rstrip("/")
    except Exception:
        return str(url).strip().rstrip("/")


def host_of(url: str) -> str:
    try:
        return (urllib.parse.urlparse(str(url).strip()).hostname or "").lower()
    except Exception:
        return ""


def path_of(url: str) -> str:
    try:
        return urllib.parse.urlparse(str(url).strip()).path.rstrip("/").lower() or "/"
    except Exception:
        return ""


def slug_of(url: str) -> str:
    path = path_of(url).strip("/")
    if "/" in path:
        return path.split("/")[-1]
    return path


def is_internal(url: str) -> bool:
    host = host_of(url)
    return host == ROOT_HOST or host.endswith("." + ROOT_HOST)


def is_external(url: str) -> bool:
    host = host_of(url)
    return bool(host) and not is_internal(url)


def is_social_or_utility(url: str) -> bool:
    return bool(SOCIAL_OR_UTILITY_HOST_RE.search(host_of(url)))


def refined_internal_cloak(url: str) -> bool:
    if not is_internal(url):
        return False
    return bool(REFINED_INTERNAL_CLOAK_RE.search(path_of(url)))


def read_csv(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def has_required_files(folder: Path) -> bool:
    return folder.is_dir() and all((folder / name).exists() for name in REQUIRED_FILES)


def find_latest_phase07_input() -> Path:
    search_roots = [
        Path.cwd(),
        Path.home() / "affiliate_phase0",
        desktop_dir(),
        Path.home() / "Downloads",
        Path.home() / "Descargas",
    ]

    roots = []
    seen = set()

    for root in search_roots:
        if not root.exists():
            continue
        try:
            resolved = root.resolve()
        except Exception:
            continue
        if resolved not in seen:
            roots.append(root)
            seen.add(resolved)

    folder_candidates = []
    zip_candidates = []

    for root in roots:
        folder_candidates.extend([p for p in root.glob(PHASE07_PREFIX + "*") if has_required_files(p)])
        zip_candidates.extend([p for p in root.glob(PHASE07_PREFIX + "*.zip") if p.is_file()])

    if folder_candidates:
        return max(folder_candidates, key=lambda p: p.stat().st_mtime)

    if zip_candidates:
        latest_zip = max(zip_candidates, key=lambda p: p.stat().st_mtime)
        extract_root = Path.cwd() / f"phase0_8_input_extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        extract_root.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(latest_zip, "r") as z:
            z.extractall(extract_root)

        extracted_candidates = [p for p in extract_root.rglob(PHASE07_PREFIX + "*") if has_required_files(p)]

        if extracted_candidates:
            return extracted_candidates[0]

        if has_required_files(extract_root):
            return extract_root

    print("ERROR: no encuentro carpeta ni ZIP de fase 0.7 con los CSV esperados.", file=sys.stderr)
    print("Coloca la carpeta o ZIP affiliate_phase0_7_nolodejesescapar_* en Desktop, Downloads o $HOME/affiliate_phase0.", file=sys.stderr)
    sys.exit(2)


def destination_kind(row: dict, validation: dict) -> str:
    url = row.get("DestinationUrl", "")
    slug = slug_of(url)
    cta = (row.get("CtaText") or "").strip().lower()
    parent = (row.get("ParentTextSample") or "").strip().lower()
    title = (validation.get("Title") or validation.get("H1") or "").strip().lower()

    if slug in BRAND_OR_RETAILER_LANDING_SLUGS:
        return "BRAND_OR_RETAILER_LANDING"

    if "cupon" in slug or "cupón" in title or "cupones" in title:
        return "COUPON_OR_RECURRING_LANDING"

    if slug.startswith("ofertas-") or slug.startswith("oferta-"):
        return "HUB_OR_LISTING"

    text = f"{cta} {parent} {title}"

    has_price_or_deal = bool(re.search(r"€|\b\d+[,.]?\d*\s*€|chollo|oferta|ofertaza|rebaja|descuento", text, re.I))
    has_productish_slug = bool(re.search(r"-", slug)) and len(slug) >= 8

    if has_price_or_deal or has_productish_slug:
        return "DEAL_POST"

    return "UNKNOWN_INTERNAL_PAGE"


def corrected_link_class(row: dict) -> dict:
    url = row.get("NormalizedUrl", "") or row.get("RequestUrl", "")
    retailer = (row.get("RetailerOrRedirect") or "").strip()
    link_kind = (row.get("LinkKind") or "").strip()
    amazon_class = (row.get("AmazonClass") or "").strip()

    external = boolish(row.get("External")) if "External" in row else is_external(url)
    affiliate_query = boolish(row.get("AffiliateQuerySignal")) or boolish(row.get("PotentialAffiliateSignals"))
    tracking_query = boolish(row.get("TrackingQuerySignal"))
    social_utility = is_social_or_utility(url)

    external_commercial = bool(
        external
        and not social_utility
        and (
            retailer
            or link_kind == "affiliate_or_redirect"
            or affiliate_query
        )
    )

    internal_cloak = refined_internal_cloak(url)
    commercial = external_commercial or internal_cloak

    reasons = []

    if external_commercial:
        if retailer:
            reasons.append("retailer")
        if link_kind == "affiliate_or_redirect":
            reasons.append("affiliate_or_redirect")
        if affiliate_query:
            reasons.append("affiliate_query")

    if internal_cloak:
        reasons.append("internal_cloak_refined")

    if tracking_query and not affiliate_query:
        reasons.append("tracking_only_not_affiliate")

    return {
        "url": url,
        "retailer": retailer,
        "link_kind": link_kind,
        "amazon_class": amazon_class,
        "external": external,
        "external_commercial": external_commercial,
        "internal_cloak_refined": internal_cloak,
        "commercial": commercial,
        "reasons": sorted(set(reasons)),
    }


def suggested_cta(retailers: list[str], monetization_status: str, kind: str) -> str:
    clean = [r for r in retailers if r]

    if kind == "BRAND_OR_RETAILER_LANDING":
        return "No priorizar como post destino"

    if "Amazon" in clean:
        return "Ver oferta en Amazon"

    if "AliExpress" in clean:
        return "Ver oferta en AliExpress"

    if clean:
        return f"Ver oferta en {clean[0]}"

    if monetization_status == "MONETIZED_CLOAKED_PROBABLE":
        return "Ver oferta"

    if monetization_status == "GAP_PROBABLE":
        return "Añadir CTA afiliado si existe oferta real"

    return "Revisar CTA"


def classify_opportunity(hub_row: dict, validation: dict, link_rows: list[dict]) -> dict:
    dest = canonical_url(hub_row.get("DestinationUrl", ""))
    title = validation.get("Title", "") or validation.get("H1", "") or dest
    intent = intish(validation.get("IntentScore"), 0)
    original_verdict = validation.get("Verdict", "") or "MISSING_VALIDATION"
    cta_text = hub_row.get("CtaText", "") or ""
    parent_sample = hub_row.get("ParentTextSample", "") or ""
    kind = destination_kind(hub_row, validation)

    link_classes = [corrected_link_class(r) for r in link_rows]

    external_commercial = [c for c in link_classes if c["external_commercial"]]
    refined_cloaks = [c for c in link_classes if c["internal_cloak_refined"]]

    retailers = sorted({c["retailer"] for c in external_commercial if c["retailer"]})
    reasons = sorted({reason for c in link_classes for reason in c["reasons"] if reason != "tracking_only_not_affiliate"})

    amazon_with_tag = sum(1 for c in link_classes if c["amazon_class"] == "DirectAmazonWithTag")
    amazon_without_tag = sum(1 for c in link_classes if c["amazon_class"] == "DirectAmazonWithoutTag")
    amazon_short = sum(1 for c in link_classes if c["amazon_class"] == "ShortAmazonUnverifiable")
    wrong_market = sum(1 for c in link_classes if c["amazon_class"] == "WrongMarketplace")

    network_only = original_verdict == "DEST_COMMERCIAL_NETWORK_ONLY"

    notes = []

    if kind in {"BRAND_OR_RETAILER_LANDING", "HUB_OR_LISTING", "UNKNOWN_INTERNAL_PAGE"}:
        if external_commercial:
            monetization_status = "LANDING_MONETIZED_EXTERNAL"
            opportunity_type = "LANDING_CTA_REVIEW"
            base_score = 55
            action = "Es una landing/categoria, no un post producto. Revisar solo si el hub quiere destacar tiendas o marcas."
        else:
            monetization_status = "NON_POST_PAGE_NO_CLEAR_MONETIZATION"
            opportunity_type = "EXCLUDE_NON_POST_LANDING"
            base_score = 25
            action = "Excluir de prioridad de posts destino; probablemente es landing, categoria o navegación interna."
        notes.append(f"DestinationKind={kind}; no tratar como gap de post producto.")

    elif amazon_without_tag > 0 or wrong_market > 0:
        monetization_status = "TAG_OR_MARKETPLACE_LEAK_RISK"
        opportunity_type = "AFFILIATE_LEAK_FIX"
        base_score = 95
        action = "Revisar enlaces Amazon sin tag o marketplace incorrecto antes de optimizar CTAs."

    elif external_commercial:
        monetization_status = "MONETIZED_EXTERNAL"
        opportunity_type = "HUB_CTA_FRICTION"
        base_score = 72
        action = "El destino ya monetiza: añadir o elevar CTA comercial visible en la card del hub."

    elif refined_cloaks:
        monetization_status = "MONETIZED_CLOAKED_PROBABLE"
        opportunity_type = "HUB_CTA_FRICTION_WITH_CLOAKING_REVIEW"
        base_score = 66
        action = "El destino parece monetizar mediante redirect interno: verificar destino final y usar CTA claro en el hub."

    elif network_only:
        monetization_status = "NETWORK_ONLY_UNVERIFIED"
        opportunity_type = "MANUAL_NETWORK_REVIEW"
        base_score = 58
        action = "Hay señales de red, pero no enlace comercial claro: revisar manualmente el post y la consola/red."

    elif intent >= 10 or HIGH_INTENT_RE.search(" ".join([dest, title, cta_text, parent_sample])):
        monetization_status = "GAP_PROBABLE"
        opportunity_type = "DESTINATION_AFFILIATE_GAP"
        base_score = 84
        action = "El destino parece comercial pero no monetiza: buscar programa/retailer y añadir enlace afiliado si procede."

    else:
        monetization_status = "LOW_CONFIDENCE"
        opportunity_type = "LOW_CONFIDENCE_REVIEW"
        base_score = 28
        action = "No priorizar salvo que haya evidencia de tráfico o intención comercial adicional."

    score = base_score

    if kind == "DEAL_POST":
        score += min(intent, 30) // 3

        if boolish(hub_row.get("IsCtaText")):
            score += 2

        if HIGH_INTENT_RE.search(cta_text + " " + parent_sample):
            score += 4

        if len(retailers) >= 2:
            score += 3

        if amazon_with_tag > 0:
            score += 2

        if amazon_short > 0:
            score += 1

    if original_verdict == "DEST_ERROR":
        score -= 25

    if kind != "DEAL_POST" and opportunity_type == "EXCLUDE_NON_POST_LANDING":
        score = min(score, 35)

    score = max(0, min(100, score))

    if score >= 80:
        band = "HIGH"
    elif score >= 55:
        band = "MEDIUM"
    else:
        band = "LOW"

    if original_verdict.startswith("DEST_CLOAKED") and not refined_cloaks:
        notes.append("Original cloaking corregido: probable falso positivo por /oferta, /amazon, /aliexpress o navegación interna.")

    if amazon_short:
        notes.append("Amazon corto no verificable sin resolver redirección; revisar manualmente si es prioritario.")

    if not validation:
        notes.append("Destino sin validación; revisar output 0.7.")

    return {
        "HubUrl": hub_row.get("HubUrl", ""),
        "DestinationUrl": dest,
        "DestinationKind": kind,
        "EligibleDealPost": "YES" if kind == "DEAL_POST" else "NO",
        "SourceOrder": hub_row.get("SourceOrder", ""),
        "DestinationOrderInHub": hub_row.get("DestinationOrderInHub", ""),
        "CtaText": cta_text,
        "IsCtaText": hub_row.get("IsCtaText", ""),
        "Title": title,
        "Status": validation.get("Status", "MISSING"),
        "IntentScore": intent,
        "OriginalVerdict0_7": original_verdict,
        "CorrectedMonetizationStatus": monetization_status,
        "OpportunityType": opportunity_type,
        "PriorityScore": score,
        "PriorityBand": band,
        "CorrectedExternalCommercialLinks": len(external_commercial),
        "CorrectedCloakedInternalLinks": len(refined_cloaks),
        "AmazonWithTagLinks": amazon_with_tag,
        "AmazonWithoutTagLinks": amazon_without_tag,
        "ShortAmazonUnverifiable": amazon_short,
        "WrongMarketplace": wrong_market,
        "RetailersDetectedCorrected": ", ".join(retailers),
        "CommercialReasonsCorrected": ", ".join(reasons),
        "SuggestedHubCTA": suggested_cta(retailers, monetization_status, kind),
        "RecommendedAction": action,
        "Notes": " | ".join(notes),
    }


def dedupe_priority_rows(matrix_rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)

    for row in matrix_rows:
        grouped[row["DestinationUrl"]].append(row)

    unique_rows = []

    for dest, rows in grouped.items():
        best = sorted(rows, key=lambda r: -intish(r["PriorityScore"]))[0].copy()
        hubs = sorted({r["HubUrl"] for r in rows})
        best["HubCount"] = len(hubs)
        best["HubUrls"] = " | ".join(hubs)
        unique_rows.append(best)

    unique_rows.sort(key=lambda r: (-intish(r["PriorityScore"]), r["DestinationUrl"]))
    return unique_rows


def main():
    input_dir = find_latest_phase07_input()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = desktop_dir() / f"{PHASE08_PREFIX}{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    hub_destinations = read_csv(input_dir / "hub_destinations.csv")
    validations = read_csv(input_dir / "destination_validation.csv")
    links = read_csv(input_dir / "destination_links.csv")

    validation_by_url = {}

    for row in validations:
        for key in ("DestinationUrl", "FinalUrl"):
            url = canonical_url(row.get(key, ""))
            if url and url not in validation_by_url:
                validation_by_url[url] = row

    links_by_page = defaultdict(list)

    for row in links:
        page_url = canonical_url(row.get("PageUrl", ""))
        if page_url:
            links_by_page[page_url].append(row)

    matrix_rows = []
    missing_validation = 0

    for hub_row in hub_destinations:
        dest = canonical_url(hub_row.get("DestinationUrl", ""))
        if not dest:
            continue

        validation = validation_by_url.get(dest, {})

        if not validation:
            missing_validation += 1

        link_rows = links_by_page.get(dest, [])
        matrix_rows.append(classify_opportunity(hub_row, validation, link_rows))

    matrix_rows.sort(
        key=lambda r: (
            r["HubUrl"],
            r["EligibleDealPost"] != "YES",
            -intish(r["PriorityScore"]),
            intish(r.get("SourceOrder"), 999999),
        )
    )

    deal_post_rows = [r for r in matrix_rows if r["EligibleDealPost"] == "YES"]
    priority_unique_rows = dedupe_priority_rows(matrix_rows)
    priority_unique_deal_posts = [r for r in priority_unique_rows if r["EligibleDealPost"] == "YES"]

    by_hub = defaultdict(list)

    for row in matrix_rows:
        by_hub[row["HubUrl"]].append(row)

    hub_summary_rows = []

    for hub_url, rows in sorted(by_hub.items()):
        deal_rows = [r for r in rows if r["EligibleDealPost"] == "YES"]

        total = len(rows)
        deal_total = len(deal_rows)

        high = sum(1 for r in deal_rows if r["PriorityBand"] == "HIGH")
        med = sum(1 for r in deal_rows if r["PriorityBand"] == "MEDIUM")
        low = sum(1 for r in deal_rows if r["PriorityBand"] == "LOW")

        friction = sum(1 for r in deal_rows if r["OpportunityType"].startswith("HUB_CTA_FRICTION"))
        gaps = sum(1 for r in deal_rows if r["OpportunityType"] == "DESTINATION_AFFILIATE_GAP")
        leaks = sum(1 for r in deal_rows if r["OpportunityType"] == "AFFILIATE_LEAK_FIX")
        network = sum(1 for r in deal_rows if r["OpportunityType"] == "MANUAL_NETWORK_REVIEW")

        external = sum(intish(r["CorrectedExternalCommercialLinks"]) for r in deal_rows)
        cloaked = sum(intish(r["CorrectedCloakedInternalLinks"]) for r in deal_rows)

        avg = round(sum(intish(r["PriorityScore"]) for r in deal_rows) / deal_total, 1) if deal_total else 0

        top = sorted(deal_rows, key=lambda r: -intish(r["PriorityScore"]))[0] if deal_rows else {}

        non_post_rows = total - deal_total

        if leaks:
            strategy = "Primero corregir fugas de tag/marketplace; después optimizar CTAs del hub."
        elif deal_total and friction >= max(1, deal_total // 2):
            strategy = "Prioridad clara: reducir fricción en cards/listado con CTAs comerciales más visibles."
        elif deal_total and gaps >= max(1, deal_total // 2):
            strategy = "Prioridad clara: revisar monetización de posts destino antes de tocar el hub."
        elif gaps:
            strategy = "Estrategia mixta: optimizar CTAs del hub y revisar gaps puntuales de destino."
        elif network:
            strategy = "Requiere revisión manual de redirecciones/red antes de decidir implementación."
        else:
            strategy = "Baja prioridad relativa o señal insuficiente."

        hub_summary_rows.append({
            "HubUrl": hub_url,
            "RowsInMatrix": total,
            "EligibleDealPosts": deal_total,
            "NonPostOrLandingRows": non_post_rows,
            "HighPriorityDealPosts": high,
            "MediumPriorityDealPosts": med,
            "LowPriorityDealPosts": low,
            "HubCtaFrictionOpportunities": friction,
            "DestinationAffiliateGaps": gaps,
            "AffiliateLeakFixes": leaks,
            "ManualNetworkReviews": network,
            "TotalCorrectedExternalCommercialLinks": external,
            "TotalCorrectedCloakedInternalLinks": cloaked,
            "AverageDealPostPriorityScore": avg,
            "TopOpportunityUrl": top.get("DestinationUrl", ""),
            "TopOpportunityScore": top.get("PriorityScore", ""),
            "RecommendedHubStrategy": strategy,
        })

    matrix_fields = [
        "HubUrl",
        "DestinationUrl",
        "DestinationKind",
        "EligibleDealPost",
        "SourceOrder",
        "DestinationOrderInHub",
        "CtaText",
        "IsCtaText",
        "Title",
        "Status",
        "IntentScore",
        "OriginalVerdict0_7",
        "CorrectedMonetizationStatus",
        "OpportunityType",
        "PriorityScore",
        "PriorityBand",
        "CorrectedExternalCommercialLinks",
        "CorrectedCloakedInternalLinks",
        "AmazonWithTagLinks",
        "AmazonWithoutTagLinks",
        "ShortAmazonUnverifiable",
        "WrongMarketplace",
        "RetailersDetectedCorrected",
        "CommercialReasonsCorrected",
        "SuggestedHubCTA",
        "RecommendedAction",
        "Notes",
    ]

    unique_fields = matrix_fields + ["HubCount", "HubUrls"]

    hub_summary_fields = [
        "HubUrl",
        "RowsInMatrix",
        "EligibleDealPosts",
        "NonPostOrLandingRows",
        "HighPriorityDealPosts",
        "MediumPriorityDealPosts",
        "LowPriorityDealPosts",
        "HubCtaFrictionOpportunities",
        "DestinationAffiliateGaps",
        "AffiliateLeakFixes",
        "ManualNetworkReviews",
        "TotalCorrectedExternalCommercialLinks",
        "TotalCorrectedCloakedInternalLinks",
        "AverageDealPostPriorityScore",
        "TopOpportunityUrl",
        "TopOpportunityScore",
        "RecommendedHubStrategy",
    ]

    write_csv(out_dir / "opportunity_matrix_all.csv", matrix_rows, matrix_fields)
    write_csv(out_dir / "opportunity_matrix_deal_posts.csv", deal_post_rows, matrix_fields)
    write_csv(out_dir / "hub_opportunity_summary.csv", hub_summary_rows, hub_summary_fields)
    write_csv(out_dir / "priority_unique_destinations.csv", priority_unique_rows, unique_fields)
    write_csv(out_dir / "priority_unique_deal_posts.csv", priority_unique_deal_posts, unique_fields)

    counts_by_type = defaultdict(int)
    counts_by_status = defaultdict(int)
    counts_by_kind = defaultdict(int)
    counts_by_band = defaultdict(int)

    for row in matrix_rows:
        counts_by_type[row["OpportunityType"]] += 1
        counts_by_status[row["CorrectedMonetizationStatus"]] += 1
        counts_by_kind[row["DestinationKind"]] += 1

    for row in deal_post_rows:
        counts_by_band[row["PriorityBand"]] += 1

    lines = []

    lines.append("FASE 0.8 — MATRIZ DE OPORTUNIDADES POR HUB")
    lines.append(f"Web analizada: {SITE_LABEL}")
    lines.append(f"Input 0.7 usado: {input_dir}")
    lines.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("VALIDACION")
    lines.append(f"- Filas hub_destinations.csv: {len(hub_destinations)}")
    lines.append(f"- Filas destination_validation.csv: {len(validations)}")
    lines.append(f"- Filas destination_links.csv: {len(links)}")
    lines.append(f"- Filas matriz generadas: {len(matrix_rows)}")
    lines.append(f"- Deal posts elegibles: {len(deal_post_rows)}")
    lines.append(f"- Destinos unicos priorizados: {len(priority_unique_rows)}")
    lines.append(f"- Deal posts unicos priorizados: {len(priority_unique_deal_posts)}")
    lines.append(f"- Destinos sin validacion asociada: {missing_validation}")
    lines.append("")
    lines.append("CORRECCIONES APLICADAS SOBRE 0.7")
    lines.append("- La matriz conserva la relacion hub -> destino aunque el destino estuviera deduplicado globalmente en 0.7.")
    lines.append("- Se recalcula el cloaking interno con patron mas estricto: /go/, /out/, /ir/, /comprar/, /redirect/, /recommends/, /link/, /cupon/.")
    lines.append("- /oferta, /ofertas, /amazon y /aliexpress ya no cuentan como cloaking por si solos.")
    lines.append("- /amazon, /aliexpress, /xiaomi y landings similares se separan de los posts producto.")
    lines.append("- UTM por si solo no cuenta como afiliacion.")
    lines.append("")
    lines.append("RESUMEN POR TIPO DE DESTINO")
    for key in sorted(counts_by_kind):
        lines.append(f"- {key}: {counts_by_kind[key]}")
    lines.append("")
    lines.append("RESUMEN POR TIPO DE OPORTUNIDAD")
    for key in sorted(counts_by_type):
        lines.append(f"- {key}: {counts_by_type[key]}")
    lines.append("")
    lines.append("RESUMEN POR MONETIZACION CORREGIDA")
    for key in sorted(counts_by_status):
        lines.append(f"- {key}: {counts_by_status[key]}")
    lines.append("")
    lines.append("PRIORIDAD SOLO EN DEAL POSTS")
    for key in ("HIGH", "MEDIUM", "LOW"):
        lines.append(f"- {key}: {counts_by_band[key]}")
    lines.append("")
    lines.append("RESUMEN POR HUB")
    for row in hub_summary_rows:
        lines.append(
            f"- {row['HubUrl']} | deal_posts={row['EligibleDealPosts']} | non_posts={row['NonPostOrLandingRows']} | "
            f"high={row['HighPriorityDealPosts']} | friction={row['HubCtaFrictionOpportunities']} | "
            f"gaps={row['DestinationAffiliateGaps']} | avg_score={row['AverageDealPostPriorityScore']} | "
            f"top={row['TopOpportunityScore']} | {row['RecommendedHubStrategy']}"
        )
    lines.append("")
    lines.append("TOP 20 DEAL POSTS UNICOS")
    for row in priority_unique_deal_posts[:20]:
        lines.append(
            f"- score={row['PriorityScore']} [{row['PriorityBand']}] | hubs={row['HubCount']} | "
            f"{row['OpportunityType']} | status={row['CorrectedMonetizationStatus']} | "
            f"CTA='{row['SuggestedHubCTA']}' | retailers={row['RetailersDetectedCorrected'] or '-'} | "
            f"{row['DestinationUrl']}"
        )
    lines.append("")
    lines.append("ARCHIVOS GENERADOS")
    lines.append(f"- opportunity_matrix_all.csv: {out_dir / 'opportunity_matrix_all.csv'}")
    lines.append(f"- opportunity_matrix_deal_posts.csv: {out_dir / 'opportunity_matrix_deal_posts.csv'}")
    lines.append(f"- hub_opportunity_summary.csv: {out_dir / 'hub_opportunity_summary.csv'}")
    lines.append(f"- priority_unique_destinations.csv: {out_dir / 'priority_unique_destinations.csv'}")
    lines.append(f"- priority_unique_deal_posts.csv: {out_dir / 'priority_unique_deal_posts.csv'}")
    lines.append(f"- summary.txt: {out_dir / 'summary.txt'}")

    summary_path = out_dir / "summary.txt"
    summary_path.write_text("\n".join(lines), encoding="utf-8")

    zip_path = out_dir / "phase0_8_outputs.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in [
            "summary.txt",
            "opportunity_matrix_all.csv",
            "opportunity_matrix_deal_posts.csv",
            "hub_opportunity_summary.csv",
            "priority_unique_destinations.csv",
            "priority_unique_deal_posts.csv",
        ]:
            z.write(out_dir / name, arcname=name)

    print()
    print("=" * 60)
    print("RESUMEN FASE 0.8")
    print("=" * 60)
    print(summary_path.read_text(encoding="utf-8"))
    print()
    print("Archivos generados en:")
    print(out_dir)
    print()
    print("ZIP para subir:")
    print(zip_path)
    print()


if __name__ == "__main__":
    main()
