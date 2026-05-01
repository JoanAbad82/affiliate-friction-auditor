#!/usr/bin/env python3
import asyncio
import csv
import html
import re
import urllib.parse
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from _site_config import load_site_config_from_cli_or_env
from playwright.async_api import async_playwright

# ============================================================
# FASE 0.7 — AFFILIATE REVENUE OPTIMIZER
# Validacion de monetizacion en posts destino
#
# Mejora respecto a la version anterior:
# - Detecta enlaces internos cloakeados tipo /go/, /out/, /comprar/.
# - Extrae URLs embebidas en onclick/data-url/data-href.
# - UTM por si solo NO cuenta como afiliacion.
# - Filtra mejor requests de red para no generar CSVs gigantes.
# - Añade señales de CommercialReason.
# ============================================================

SITE_LABEL = "Example Affiliate Site"
ROOT_HOST = "example-affiliate-site.test"
EXPECTED_AMAZON_DOMAIN = "amazon.es"
OUTPUT_SLUG = "example_affiliate_site"

HUB_URLS = [
    "https://example-affiliate-site.test/ofertas-en-smartphone",
    "https://example-affiliate-site.test/ofertas-de-drones",
    "https://example-affiliate-site.test/pc-accesorios",
]

MAX_DESTINATIONS_PER_HUB = 12
MAX_TOTAL_DESTINATIONS = 36
MAX_NETWORK_ROWS_PER_DESTINATION = 250

VIEWPORT = {"width": 1366, "height": 900}
TIMEOUT_MS = 45000
WAIT_AFTER_LOAD_MS = 3500

DESKTOP_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

RETAILER_HOST_PATTERNS = [
    ("Amazon", r"(^|\.)amazon\.|^amzn\.to$|^a\.co$"),
    ("AliExpress", r"(^|\.)aliexpress\.|^s\.click\.aliexpress\.com$"),
    ("PcComponentes", r"(^|\.)pccomponentes\."),
    ("MediaMarkt", r"(^|\.)mediamarkt\."),
    ("Miravia", r"(^|\.)miravia\."),
    ("Carrefour", r"(^|\.)carrefour\."),
    ("El Corte Ingles", r"(^|\.)elcorteingles\."),
    ("eBay", r"(^|\.)ebay\."),
    ("Back Market", r"(^|\.)backmarket\."),
    ("Coolmod", r"(^|\.)coolmod\."),
    ("Fnac", r"(^|\.)fnac\."),
    ("Worten", r"(^|\.)worten\."),
    ("Leroy Merlin", r"(^|\.)leroymerlin\."),
    ("Decathlon", r"(^|\.)decathlon\."),
    ("Banggood", r"(^|\.)banggood\."),
    ("Gearbest", r"(^|\.)gearbest\."),
]

AFFILIATE_OR_REDIRECT_HOST_PATTERNS = [
    ("Awin/Redirect", r"(^|\.)awin1\.com$|(^|\.)awin\.com$"),
    ("TradeDoubler/Redirect", r"(^|\.)tradedoubler\.com$"),
    ("TradeTracker/Redirect", r"(^|\.)tradetracker\."),
    ("Adtraction/Redirect", r"(^|\.)adtraction\.com$"),
    ("CJ/Redirect", r"(^|\.)anrdoezrs\.net$|(^|\.)jdoqocy\.com$|(^|\.)tkqlhce\.com$"),
    ("Impact/Redirect", r"(^|\.)impact\.com$|(^|\.)sjv\.io$"),
    ("LinkShare/Redirect", r"(^|\.)linksynergy\.com$"),
    ("Partnerize/Redirect", r"(^|\.)prf\.hn$"),
    ("Skimlinks/Redirect", r"(^|\.)skimresources\.com$|(^|\.)skimlinks\.com$"),
    ("Viglink/Redirect", r"(^|\.)viglink\.com$|(^|\.)sovrn\.com$"),
    ("Geniuslink/Redirect", r"(^|\.)geni\.us$"),
    ("Bitly/Redirect", r"(^|\.)bit\.ly$"),
    ("TinyURL/Redirect", r"(^|\.)tinyurl\.com$"),
]

SOCIAL_OR_UTILITY_HOST_PATTERNS = [
    r"(^|\.)facebook\.com$", r"(^|\.)instagram\.com$", r"(^|\.)x\.com$", r"(^|\.)twitter\.com$",
    r"(^|\.)youtube\.com$", r"(^|\.)youtu\.be$", r"(^|\.)tiktok\.com$", r"(^|\.)pinterest\.",
    r"(^|\.)whatsapp\.com$", r"(^|\.)telegram\.me$", r"(^|\.)t\.me$", r"(^|\.)linkedin\.com$",
    r"(^|\.)google\.com$", r"(^|\.)gstatic\.com$", r"(^|\.)googleapis\.com$", r"(^|\.)gravatar\.com$",
]

CTA_WORDS = [
    "ver más", "ver mas", "leer más", "leer mas", "ver oferta", "ver precio",
    "comprar", "ver producto", "ir a la tienda", "oferta", "chollo",
    "más información", "mas informacion"
]

AFFILIATE_QUERY_KEYS = {
    "tag", "ascsubtag", "aff", "affiliate", "affid", "aff_id", "partner", "partnerid",
    "clickid", "awc", "irclickid", "clickref", "subid", "sub_id", "campid", "campaignid",
    "adid", "pubref", "pubid", "sid", "sscid", "ranmid", "raneaid"
}

TRACKING_QUERY_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"
}

URL_IN_TEXT_RE = re.compile(
    r"(?:(?:https?:)?//[^\s'\"\)<>]+|/[A-Za-z0-9][^\s'\"\)<>]*)",
    re.I,
)

INTERNAL_CLOAK_PATH_RE = re.compile(
    r"/(go|ir|out|outgoing|comprar|compra|oferta|ofertas|tienda|redirect|recommends|recomienda|link|links|cupon|coupon)(/|$|\?|-) ",
    re.I,
)

# Corrige el espacio final accidental del regex anterior en runtime.
INTERNAL_CLOAK_PATH_RE = re.compile(
    r"/(go|ir|out|outgoing|comprar|compra|oferta|ofertas|tienda|redirect|recommends|recomienda|link|links|cupon|coupon)(/|$|\?|-)",
    re.I,
)

load_site_config_from_cli_or_env(globals())

HUB_PATHS = {urllib.parse.urlparse(u).path.rstrip("/").lower() for u in HUB_URLS}


def desktop_dir() -> Path:
    for name in ("Escritorio", "Desktop"):
        candidate = Path.home() / name
        if candidate.exists():
            return candidate
    return Path.home()


stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out_dir = desktop_dir() / f"affiliate_phase0_7_{OUTPUT_SLUG}_{stamp}"
out_dir.mkdir(parents=True, exist_ok=True)

summary_txt = out_dir / "summary.txt"
hub_destinations_csv = out_dir / "hub_destinations.csv"
destination_validation_csv = out_dir / "destination_validation.csv"
destination_links_csv = out_dir / "destination_links.csv"
destination_network_csv = out_dir / "destination_network_requests.csv"
hub_summary_csv = out_dir / "hub_summary.csv"
screens_dir = out_dir / "destination_screenshots"
screens_dir.mkdir(exist_ok=True)


def deep_decode(value: str) -> str:
    if not value:
        return ""
    decoded = str(value)
    for _ in range(4):
        decoded_html = html.unescape(decoded)
        decoded_url = urllib.parse.unquote(decoded_html)
        if decoded_url == decoded:
            break
        decoded = decoded_url
    return decoded.strip()


def normalize_url(base_url: str, value: str) -> str:
    if not value:
        return ""

    value = deep_decode(value).strip()
    low = value.lower()

    if low.startswith(("mailto:", "tel:", "javascript:", "data:", "blob:", "#")):
        return ""

    if value.startswith("//"):
        value = "https:" + value

    try:
        url = urllib.parse.urljoin(base_url, value)
        parsed = urllib.parse.urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            return ""

        parsed = parsed._replace(fragment="")
        return urllib.parse.urlunparse(parsed).rstrip("/")
    except Exception:
        return ""


def extract_url_candidates(base_url: str, raw: str) -> list[str]:
    raw = deep_decode(raw)

    if not raw:
        return []

    candidates = []

    def add(value: str):
        normalized = normalize_url(base_url, value)
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    add(raw)

    for found in URL_IN_TEXT_RE.findall(raw):
        add(found)

    for candidate in list(candidates):
        try:
            parsed = urllib.parse.urlparse(candidate)
            qs = urllib.parse.parse_qs(parsed.query)

            for key in ("url", "u", "target", "to", "redirect", "redirect_url", "destination", "dest", "link"):
                for value in qs.get(key, []):
                    add(value)
        except Exception:
            pass

    return candidates


def get_hostname(url: str) -> str:
    try:
        return (urllib.parse.urlparse(deep_decode(url)).hostname or "").lower()
    except Exception:
        return ""


def get_path(url: str) -> str:
    try:
        return urllib.parse.urlparse(deep_decode(url)).path.rstrip("/").lower() or "/"
    except Exception:
        return ""


def query_keys(url: str) -> set[str]:
    try:
        parsed = urllib.parse.urlparse(deep_decode(url))
        return {k.lower() for k in urllib.parse.parse_qs(parsed.query).keys()}
    except Exception:
        return set()


def is_internal_url(url: str) -> bool:
    host = get_hostname(url)
    return host == ROOT_HOST or host.endswith("." + ROOT_HOST)


def is_external_url(url: str) -> bool:
    host = get_hostname(url)
    return bool(host) and not is_internal_url(url)


def is_asset_url(url: str) -> bool:
    path = get_path(url)
    return bool(
        re.search(
            r"\.(jpg|jpeg|png|gif|webp|svg|css|js|ico|xml|rss|pdf|zip|rar|7z|mp4|mp3|woff|woff2|ttf|eot)$",
            path,
            re.I,
        )
    )


def is_social_or_utility_host(host: str) -> bool:
    return any(re.search(pattern, host, flags=re.I) for pattern in SOCIAL_OR_UTILITY_HOST_PATTERNS)


def is_bad_internal_destination(url: str) -> bool:
    path = get_path(url)

    if not path or path == "/":
        return True

    bad_parts = [
        "/category", "/tag", "/author", "/page", "/feed", "/search",
        "/aviso-legal", "/politica", "/privacidad", "/contact", "/contacto",
        "/comunicate", "/wp-", "/xmlrpc", "/sitemap",
    ]

    if any(x in path for x in bad_parts):
        return True

    if path in HUB_PATHS:
        return True

    if is_asset_url(url):
        return True

    return False


def match_named_patterns(host: str, patterns) -> str:
    for name, pattern in patterns:
        if re.search(pattern, host, flags=re.I):
            return name
    return ""


def detect_retailer_or_redirect(url: str) -> tuple[str, str]:
    host = get_hostname(url)

    retailer = match_named_patterns(host, RETAILER_HOST_PATTERNS)
    if retailer:
        return retailer, "retailer"

    redirector = match_named_patterns(host, AFFILIATE_OR_REDIRECT_HOST_PATTERNS)
    if redirector:
        return redirector, "affiliate_or_redirect"

    return "", ""


def classify_amazon_link(url: str) -> str:
    host = get_hostname(url)

    if host in {"amzn.to", "a.co"}:
        return "ShortAmazonUnverifiable"

    if not re.search(r"(^|\.)amazon\.", host, flags=re.I):
        return "NotAmazon"

    marketplace_ok = EXPECTED_AMAZON_DOMAIN in host
    keys = query_keys(url)
    has_tag = "tag" in keys or bool(re.search(r"(^|[?&])tag=[^&]+", deep_decode(url), flags=re.I))

    if not marketplace_ok:
        return "WrongMarketplace"

    if has_tag:
        return "DirectAmazonWithTag"

    return "DirectAmazonWithoutTag"


def classify_url(url: str) -> dict:
    host = get_hostname(url)
    path = get_path(url)
    external = is_external_url(url)
    internal = is_internal_url(url)
    retailer, link_kind = detect_retailer_or_redirect(url)
    keys = query_keys(url)

    affiliate_query = bool(keys.intersection(AFFILIATE_QUERY_KEYS))
    tracking_query = bool(keys.intersection(TRACKING_QUERY_KEYS))
    cloaked_internal = bool(internal and INTERNAL_CLOAK_PATH_RE.search(path))
    social_or_utility = bool(external and is_social_or_utility_host(host))

    commercial = False
    commercial_reason = ""

    if retailer:
        commercial = True
        commercial_reason = "retailer"
    elif link_kind == "affiliate_or_redirect":
        commercial = True
        commercial_reason = "affiliate_or_redirect"
    elif affiliate_query and not social_or_utility:
        commercial = True
        commercial_reason = "affiliate_query"
    elif cloaked_internal:
        commercial = True
        commercial_reason = "internal_cloak_candidate"

    amazon_class = classify_amazon_link(url) if retailer == "Amazon" else ""

    return {
        "Host": host,
        "External": external,
        "Internal": internal,
        "RetailerOrRedirect": retailer,
        "LinkKind": link_kind,
        "AffiliateQuerySignal": affiliate_query,
        "TrackingQuerySignal": tracking_query,
        "CloakedInternalCandidate": cloaked_internal,
        "CommercialCandidate": commercial,
        "CommercialReason": commercial_reason,
        "AmazonClass": amazon_class,
    }


def score_intent(page_url: str, title: str, h1: str, body_text: str) -> int:
    text = f"{page_url} {title} {h1} {body_text}".lower()

    words = [
        "oferta", "ofertas", "chollo", "chollos", "comprar", "precio", "descuento",
        "rebajado", "cupón", "cupon", "smartphone", "drones", "accesorios", "pc",
        "amazon", "aliexpress", "mediamarkt", "pccomponentes", "xiaomi", "samsung",
        "realme", "oppo", "poco", "drone", "teclado", "monitor", "ratón", "raton",
        "ssd", "auriculares",
    ]

    score = 0

    for word in words:
        if word in text:
            score += 3

    if re.search(r"/ofertas|/cupon|/chollo|/pc-|/smartphone|/drones|/amazon|/aliexpress", page_url, flags=re.I):
        score += 5

    return min(score, 30)


async def auto_scroll(page):
    await page.evaluate(
        """
        async () => {
          let lastHeight = 0;
          let stableRounds = 0;

          for (let i = 0; i < 14; i++) {
            window.scrollBy(0, 800);
            await new Promise(r => setTimeout(r, 250));

            const h = document.body.scrollHeight || 0;

            if (h === lastHeight) stableRounds += 1;
            else stableRounds = 0;

            lastHeight = h;

            if (stableRounds >= 3) break;
          }

          window.scrollTo(0, 0);
        }
        """
    )


async def extract_hub_destinations(page, hub_url: str):
    data = await page.evaluate(
        """
        () => {
          const rows = [];
          const attrs = [
            "href", "data-href", "data-url", "data-link", "data-target",
            "data-redirect", "data-product-url", "onclick"
          ];

          document.querySelectorAll("a, button, [onclick]").forEach((el, idx) => {
            const text = (el.innerText || el.textContent || "").trim().replace(/\\s+/g, " ");
            const parent = el.closest("article, .post, .entry, li, .card, .product, div");
            const parentText = (parent?.innerText || "").trim().replace(/\\s+/g, " ").slice(0, 700);
            const outer = (el.outerHTML || "").slice(0, 900);

            attrs.forEach(attr => {
              const raw = el.getAttribute(attr);
              if (raw) rows.push({idx, text, parentText, attr, raw, outer});
            });
          });

          return rows;
        }
        """
    )

    rows = []
    seen = set()
    cta_lowers = [w.lower() for w in CTA_WORDS]

    for item in data:
        raw = item.get("raw", "")

        for normalized in extract_url_candidates(hub_url, raw):
            if not is_internal_url(normalized):
                continue

            if is_bad_internal_destination(normalized):
                continue

            if get_path(normalized) == get_path(hub_url):
                continue

            if normalized in seen:
                continue

            text = item.get("text", "") or ""
            parent_text = item.get("parentText", "") or ""
            joined = f"{text} {parent_text}".lower()

            is_cta = any(w in joined for w in cta_lowers)
            card_like = bool(
                re.search(
                    r"oferta|chollo|rebaja|descuento|amazon|aliexpress|precio|€|smartphone|drone|pc|teclado|monitor|xiaomi|samsung|realme|oppo|poco|ssd|auriculares",
                    joined,
                    flags=re.I,
                )
            )

            if not is_cta and not card_like:
                continue

            seen.add(normalized)

            rows.append(
                {
                    "HubUrl": hub_url,
                    "DestinationUrl": normalized,
                    "CtaText": text[:300],
                    "IsCtaText": is_cta,
                    "ParentTextSample": parent_text[:500],
                    "SourceOrder": item.get("idx", 0),
                    "SourceAttribute": item.get("attr", ""),
                }
            )

    rows.sort(key=lambda r: (not r["IsCtaText"], r["SourceOrder"], r["DestinationUrl"]))
    return rows[:MAX_DESTINATIONS_PER_HUB]


async def extract_rendered_links(page, page_url: str):
    data = await page.evaluate(
        """
        () => {
          const rows = [];
          const attrs = [
            "href", "data-href", "data-url", "data-link", "data-target",
            "data-redirect", "data-product-url", "onclick"
          ];

          const push = (el, kind, attr, raw) => {
            rows.push({
              kind,
              attr,
              raw: raw || "",
              text: (el.innerText || el.textContent || "").trim().replace(/\\s+/g, " ").slice(0, 300),
              rel: el.getAttribute("rel") || "",
              aria: el.getAttribute("aria-label") || "",
              classes: el.getAttribute("class") || "",
              outer: (el.outerHTML || "").slice(0, 700)
            });
          };

          document.querySelectorAll("a, button, [onclick]").forEach(el => {
            const kind = el.tagName.toLowerCase();

            attrs.forEach(attr => {
              const raw = el.getAttribute(attr);
              if (raw) push(el, kind, attr, raw);
            });
          });

          return rows;
        }
        """
    )

    rows = []
    seen = set()

    for item in data:
        raw = item.get("raw", "")

        for normalized in extract_url_candidates(page_url, raw):
            key = (item.get("kind"), item.get("attr"), normalized, item.get("text", ""))

            if key in seen:
                continue

            seen.add(key)

            cls = classify_url(normalized)

            rows.append(
                {
                    "PageUrl": page_url,
                    "ElementKind": item.get("kind", ""),
                    "Attribute": item.get("attr", ""),
                    "RawValue": raw,
                    "NormalizedUrl": normalized,
                    "Host": cls["Host"],
                    "Text": item.get("text", ""),
                    "Rel": item.get("rel", ""),
                    "AriaLabel": item.get("aria", ""),
                    "External": cls["External"],
                    "RetailerOrRedirect": cls["RetailerOrRedirect"],
                    "LinkKind": cls["LinkKind"],
                    "AffiliateQuerySignal": cls["AffiliateQuerySignal"],
                    "TrackingQuerySignal": cls["TrackingQuerySignal"],
                    "CloakedInternalCandidate": cls["CloakedInternalCandidate"],
                    "CommercialCandidate": cls["CommercialCandidate"],
                    "CommercialReason": cls["CommercialReason"],
                    "AmazonClass": cls["AmazonClass"],
                }
            )

    return rows


def classify_request_rows(captured_requests: list[dict]) -> list[dict]:
    output = []

    for req in captured_requests:
        url = req["RequestUrl"]
        cls = classify_url(url)

        keep = False

        if cls["CommercialCandidate"]:
            keep = True
        elif cls["External"] and req.get("ResourceType") in {"document", "xhr", "fetch", "script"} and not is_asset_url(url):
            keep = True

        if not keep:
            continue

        req.update(
            {
                "RetailerOrRedirect": cls["RetailerOrRedirect"],
                "LinkKind": cls["LinkKind"],
                "AffiliateQuerySignal": cls["AffiliateQuerySignal"],
                "TrackingQuerySignal": cls["TrackingQuerySignal"],
                "CloakedInternalCandidate": cls["CloakedInternalCandidate"],
                "CommercialRequest": cls["CommercialCandidate"],
                "CommercialReason": cls["CommercialReason"],
            }
        )

        output.append(req)

        if len(output) >= MAX_NETWORK_ROWS_PER_DESTINATION:
            break

    return output


async def validate_destination(context, destination_url: str, hub_url: str, order: int):
    page = await context.new_page()
    captured_requests = []

    def on_request(req):
        captured_requests.append(
            {
                "DestinationUrl": destination_url,
                "HubUrl": hub_url,
                "RequestUrl": req.url,
                "Method": req.method,
                "ResourceType": req.resource_type,
                "Host": get_hostname(req.url),
            }
        )

    page.on("request", on_request)

    status = ""
    final_url = ""
    title = ""
    h1 = ""
    body_text = ""
    error = ""

    try:
        response = await page.goto(destination_url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
        status = str(response.status) if response else ""
        final_url = page.url

        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        await page.wait_for_timeout(WAIT_AFTER_LOAD_MS)
        await auto_scroll(page)
        await page.wait_for_timeout(1200)

        title = await page.title()

        try:
            h1 = await page.locator("h1").first.text_content(timeout=3000)
        except Exception:
            h1 = ""

        try:
            body_text = await page.locator("body").inner_text(timeout=10000)
        except Exception:
            body_text = ""

        slug = re.sub(r"[^a-zA-Z0-9]+", "_", urllib.parse.urlparse(destination_url).path.strip("/"))[:80] or f"dest_{order}"
        await page.screenshot(path=str(screens_dir / f"{order:02d}_{slug}.png"), full_page=True)

        links = await extract_rendered_links(page, destination_url)
        request_rows = classify_request_rows(captured_requests)

        intent_score = score_intent(destination_url, title, h1 or "", body_text[:9000])

        commercial_links = [r for r in links if r["CommercialCandidate"]]
        visible_external_commercial = [r for r in commercial_links if r["External"]]
        cloaked_internal_links = [r for r in commercial_links if r["CloakedInternalCandidate"]]
        commercial_requests = [r for r in request_rows if r["CommercialRequest"]]

        amazon_links = [r for r in links if r["RetailerOrRedirect"] == "Amazon"]
        non_amazon_links = [r for r in links if r["RetailerOrRedirect"] and r["RetailerOrRedirect"] != "Amazon"]

        direct_amazon_tag = sum(1 for r in amazon_links if r["AmazonClass"] == "DirectAmazonWithTag")
        direct_amazon_no_tag = sum(1 for r in amazon_links if r["AmazonClass"] == "DirectAmazonWithoutTag")
        short_amazon = sum(1 for r in amazon_links if r["AmazonClass"] == "ShortAmazonUnverifiable")
        wrong_market = sum(1 for r in amazon_links if r["AmazonClass"] == "WrongMarketplace")

        retailers = sorted({r["RetailerOrRedirect"] for r in commercial_links if r["RetailerOrRedirect"]})
        request_retailers = sorted({r["RetailerOrRedirect"] for r in commercial_requests if r["RetailerOrRedirect"]})
        reasons = sorted({r["CommercialReason"] for r in commercial_links if r["CommercialReason"]})

        if direct_amazon_no_tag > 0:
            verdict = "DEST_AMAZON_TAG_LEAK"
            recommendation = "El post destino tiene Amazon directo sin tag visible. Revisar fuga de tag."
        elif wrong_market > 0:
            verdict = "DEST_AMAZON_WRONG_MARKETPLACE"
            recommendation = "El post destino tiene posible marketplace Amazon incorrecto."
        elif visible_external_commercial:
            verdict = "DEST_MONETIZED_VISIBLE"
            recommendation = "El post destino sí tiene enlaces comerciales visibles. El hub podría reducir fricción con enlaces directos destacados."
        elif cloaked_internal_links:
            verdict = "DEST_CLOAKED_MONETIZATION_PROBABLE"
            recommendation = "El post destino parece usar enlaces internos cloakeados/redireccionados. Revisar manualmente el destino final."
        elif commercial_requests:
            verdict = "DEST_COMMERCIAL_NETWORK_ONLY"
            recommendation = "El post destino no muestra enlaces comerciales claros, pero sí requests comerciales/afiliación."
        elif intent_score >= 10:
            verdict = "DEST_GAP_PROBABLE"
            recommendation = "El post destino tiene intención comercial pero no muestra monetización externa renderizada ni cloaking obvio."
        else:
            verdict = "DEST_LOW_CONFIDENCE"
            recommendation = "No hay señal suficiente para clasificar como oportunidad."

        validation = {
            "HubUrl": hub_url,
            "DestinationUrl": destination_url,
            "FinalUrl": final_url,
            "Order": order,
            "Status": status,
            "Title": title,
            "H1": h1 or "",
            "IntentScore": intent_score,
            "RenderedLinksTotal": len(links),
            "RenderedCommercialLinks": len(commercial_links),
            "RenderedExternalCommercialLinks": len(visible_external_commercial),
            "RenderedCloakedInternalLinks": len(cloaked_internal_links),
            "RenderedCommercialRequests": len(commercial_requests),
            "AmazonLinks": len(amazon_links),
            "DirectAmazonWithTag": direct_amazon_tag,
            "DirectAmazonWithoutTag": direct_amazon_no_tag,
            "ShortAmazonUnverifiable": short_amazon,
            "WrongMarketplace": wrong_market,
            "NonAmazonCommercialLinks": len(non_amazon_links),
            "RetailersDetected": ", ".join(retailers),
            "CommercialRequestRetailers": ", ".join(request_retailers),
            "CommercialReasons": ", ".join(reasons),
            "Verdict": verdict,
            "Recommendation": recommendation,
            "Error": error,
        }

        return validation, links, request_rows

    except Exception as exc:
        error = repr(exc)
        request_rows = classify_request_rows(captured_requests)

        validation = {
            "HubUrl": hub_url,
            "DestinationUrl": destination_url,
            "FinalUrl": final_url,
            "Order": order,
            "Status": status or "ERROR",
            "Title": title,
            "H1": h1 or "",
            "IntentScore": 0,
            "RenderedLinksTotal": 0,
            "RenderedCommercialLinks": 0,
            "RenderedExternalCommercialLinks": 0,
            "RenderedCloakedInternalLinks": 0,
            "RenderedCommercialRequests": sum(1 for r in request_rows if r.get("CommercialRequest")),
            "AmazonLinks": 0,
            "DirectAmazonWithTag": 0,
            "DirectAmazonWithoutTag": 0,
            "ShortAmazonUnverifiable": 0,
            "WrongMarketplace": 0,
            "NonAmazonCommercialLinks": 0,
            "RetailersDetected": "",
            "CommercialRequestRetailers": "",
            "CommercialReasons": "",
            "Verdict": "DEST_ERROR",
            "Recommendation": "No se pudo validar el post destino.",
            "Error": error,
        }

        return validation, [], request_rows

    finally:
        await page.close()


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


async def main():
    hub_destination_rows = []
    destination_validation_rows = []
    destination_link_rows = []
    destination_network_rows = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(
            viewport=VIEWPORT,
            user_agent=DESKTOP_UA,
            locale="es-ES",
            timezone_id="Europe/Madrid",
            extra_http_headers={"Accept-Language": "es-ES,es;q=0.9,en;q=0.8"},
        )

        for hub_idx, hub_url in enumerate(HUB_URLS, start=1):
            print(f"[HUB {hub_idx}/{len(HUB_URLS)}] {hub_url}")
            page = await context.new_page()

            try:
                await page.goto(hub_url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)

                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass

                await page.wait_for_timeout(WAIT_AFTER_LOAD_MS)
                await auto_scroll(page)
                await page.wait_for_timeout(1200)

                destinations = await extract_hub_destinations(page, hub_url)

                for i, row in enumerate(destinations, start=1):
                    row["HubOrder"] = hub_idx
                    row["DestinationOrderInHub"] = i
                    row["Error"] = ""
                    hub_destination_rows.append(row)

            except Exception as exc:
                hub_destination_rows.append(
                    {
                        "HubUrl": hub_url,
                        "DestinationUrl": "",
                        "CtaText": "",
                        "IsCtaText": False,
                        "ParentTextSample": "",
                        "SourceOrder": -1,
                        "SourceAttribute": "",
                        "HubOrder": hub_idx,
                        "DestinationOrderInHub": 0,
                        "Error": repr(exc),
                    }
                )

            finally:
                await page.close()

        unique_destinations = []
        seen_dest = set()

        for row in hub_destination_rows:
            dest = row.get("DestinationUrl", "")

            if not dest or dest in seen_dest:
                continue

            seen_dest.add(dest)
            unique_destinations.append(row)

            if len(unique_destinations) >= MAX_TOTAL_DESTINATIONS:
                break

        print(f"Destinos unicos a validar: {len(unique_destinations)}")

        for order, row in enumerate(unique_destinations, start=1):
            dest = row["DestinationUrl"]
            hub = row["HubUrl"]

            print(f"[DEST {order}/{len(unique_destinations)}] {dest}")

            validation, links, requests = await validate_destination(context, dest, hub, order)
            destination_validation_rows.append(validation)

            for link in links:
                link["HubUrl"] = hub
                destination_link_rows.append(link)

            destination_network_rows.extend(requests)

        await browser.close()

    by_hub = defaultdict(list)

    for row in destination_validation_rows:
        by_hub[row["HubUrl"]].append(row)

    hub_summary_rows = []

    for hub_url in HUB_URLS:
        rows = by_hub.get(hub_url, [])

        checked = len(rows)
        monetized = sum(1 for r in rows if r["Verdict"] == "DEST_MONETIZED_VISIBLE")
        cloaked = sum(1 for r in rows if r["Verdict"] == "DEST_CLOAKED_MONETIZATION_PROBABLE")
        gaps = sum(1 for r in rows if r["Verdict"] == "DEST_GAP_PROBABLE")
        leaks = sum(1 for r in rows if r["Verdict"] == "DEST_AMAZON_TAG_LEAK")
        wrong_market = sum(1 for r in rows if r["Verdict"] == "DEST_AMAZON_WRONG_MARKETPLACE")
        network_only = sum(1 for r in rows if r["Verdict"] == "DEST_COMMERCIAL_NETWORK_ONLY")
        errors = sum(1 for r in rows if r["Verdict"] == "DEST_ERROR")

        commercial_links = sum(int(r["RenderedCommercialLinks"]) for r in rows)
        external_commercial_links = sum(int(r["RenderedExternalCommercialLinks"]) for r in rows)
        cloaked_links = sum(int(r["RenderedCloakedInternalLinks"]) for r in rows)
        amazon_links = sum(int(r["AmazonLinks"]) for r in rows)
        non_amazon_links = sum(int(r["NonAmazonCommercialLinks"]) for r in rows)

        if checked == 0:
            hub_verdict = "HUB_NO_DESTINATIONS_FOUND"
            hub_recommendation = "No se encontraron posts destino desde el hub."
        elif leaks > 0:
            hub_verdict = "HUB_DESTINATION_TAG_LEAKS"
            hub_recommendation = "Hay posts destino con fugas de tag Amazon; revisar urgente."
        elif wrong_market > 0:
            hub_verdict = "HUB_DESTINATION_WRONG_MARKETPLACE"
            hub_recommendation = "Hay posts destino con posible marketplace Amazon incorrecto."
        elif (monetized + cloaked) >= max(1, checked // 2):
            hub_verdict = "HUB_FRICTION_OPPORTUNITY"
            hub_recommendation = "Los posts destino monetizan o parecen redirigir; el hub podría reducir fricción con enlaces directos destacados."
        elif gaps >= max(1, checked // 2):
            hub_verdict = "HUB_AFFILIATE_GAP_PROBABLE"
            hub_recommendation = "Muchos posts destino tampoco monetizan; posible gap real de afiliación."
        elif network_only > 0:
            hub_verdict = "HUB_NEEDS_MANUAL_NETWORK_REVIEW"
            hub_recommendation = "Hay señales de red/afiliación sin enlaces claros; revisar manualmente."
        else:
            hub_verdict = "HUB_MIXED_OR_LOW_CONFIDENCE"
            hub_recommendation = "Señal mixta; revisar URLs prioritarias."

        hub_summary_rows.append(
            {
                "HubUrl": hub_url,
                "DestinationsChecked": checked,
                "DestinationsMonetizedVisible": monetized,
                "DestinationsCloakedProbable": cloaked,
                "DestinationsGapProbable": gaps,
                "DestinationsAmazonTagLeaks": leaks,
                "DestinationsWrongMarketplace": wrong_market,
                "DestinationsNetworkOnly": network_only,
                "DestinationErrors": errors,
                "TotalCommercialLinksInDestinations": commercial_links,
                "TotalExternalCommercialLinksInDestinations": external_commercial_links,
                "TotalCloakedInternalLinksInDestinations": cloaked_links,
                "TotalAmazonLinksInDestinations": amazon_links,
                "TotalNonAmazonCommercialLinksInDestinations": non_amazon_links,
                "HubVerdict": hub_verdict,
                "HubRecommendation": hub_recommendation,
            }
        )

    write_csv(
        hub_destinations_csv,
        [r for r in hub_destination_rows if r.get("DestinationUrl")],
        [
            "HubUrl", "DestinationUrl", "CtaText", "IsCtaText", "ParentTextSample",
            "SourceOrder", "SourceAttribute", "HubOrder", "DestinationOrderInHub", "Error",
        ],
    )

    write_csv(
        destination_validation_csv,
        destination_validation_rows,
        [
            "HubUrl", "DestinationUrl", "FinalUrl", "Order", "Status", "Title", "H1",
            "IntentScore", "RenderedLinksTotal", "RenderedCommercialLinks",
            "RenderedExternalCommercialLinks", "RenderedCloakedInternalLinks",
            "RenderedCommercialRequests", "AmazonLinks", "DirectAmazonWithTag",
            "DirectAmazonWithoutTag", "ShortAmazonUnverifiable", "WrongMarketplace",
            "NonAmazonCommercialLinks", "RetailersDetected", "CommercialRequestRetailers",
            "CommercialReasons", "Verdict", "Recommendation", "Error",
        ],
    )

    write_csv(
        destination_links_csv,
        destination_link_rows,
        [
            "HubUrl", "PageUrl", "ElementKind", "Attribute", "RawValue", "NormalizedUrl",
            "Host", "Text", "Rel", "AriaLabel", "External", "RetailerOrRedirect",
            "LinkKind", "AffiliateQuerySignal", "TrackingQuerySignal",
            "CloakedInternalCandidate", "CommercialCandidate", "CommercialReason", "AmazonClass",
        ],
    )

    write_csv(
        destination_network_csv,
        destination_network_rows,
        [
            "DestinationUrl", "HubUrl", "RequestUrl", "Method", "ResourceType", "Host",
            "RetailerOrRedirect", "LinkKind", "AffiliateQuerySignal", "TrackingQuerySignal",
            "CloakedInternalCandidate", "CommercialRequest", "CommercialReason",
        ],
    )

    write_csv(
        hub_summary_csv,
        hub_summary_rows,
        [
            "HubUrl", "DestinationsChecked", "DestinationsMonetizedVisible",
            "DestinationsCloakedProbable", "DestinationsGapProbable",
            "DestinationsAmazonTagLeaks", "DestinationsWrongMarketplace",
            "DestinationsNetworkOnly", "DestinationErrors",
            "TotalCommercialLinksInDestinations",
            "TotalExternalCommercialLinksInDestinations",
            "TotalCloakedInternalLinksInDestinations",
            "TotalAmazonLinksInDestinations",
            "TotalNonAmazonCommercialLinksInDestinations",
            "HubVerdict", "HubRecommendation",
        ],
    )

    verdict_counts = defaultdict(int)

    for row in destination_validation_rows:
        verdict_counts[row["Verdict"]] += 1

    hub_verdict_counts = defaultdict(int)

    for row in hub_summary_rows:
        hub_verdict_counts[row["HubVerdict"]] += 1

    summary = []

    summary.append("FASE 0.7 — VALIDACION DE MONETIZACION EN POSTS DESTINO")
    summary.append(f"Web analizada: {SITE_LABEL}")
    summary.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append("")
    summary.append("HUBS ANALIZADOS")

    for url in HUB_URLS:
        summary.append(f"- {url}")

    summary.append("")
    summary.append("RESULTADOS DESTINOS")
    summary.append(f"Destinos extraidos totales: {len([r for r in hub_destination_rows if r.get('DestinationUrl')])}")
    summary.append(f"Destinos unicos validados: {len(destination_validation_rows)}")

    for key in sorted(verdict_counts):
        summary.append(f"- {key}: {verdict_counts[key]}")

    summary.append("")
    summary.append("RESULTADOS HUBS")

    for key in sorted(hub_verdict_counts):
        summary.append(f"- {key}: {hub_verdict_counts[key]}")

    summary.append("")
    summary.append("DETALLE POR HUB")

    for row in hub_summary_rows:
        summary.append(
            f"- Verdict={row['HubVerdict']} | Destinos={row['DestinationsChecked']} | "
            f"Monetized={row['DestinationsMonetizedVisible']} | Cloaked={row['DestinationsCloakedProbable']} | "
            f"Gaps={row['DestinationsGapProbable']} | Leaks={row['DestinationsAmazonTagLeaks']} | "
            f"CommercialLinks={row['TotalCommercialLinksInDestinations']} | "
            f"ExternalCommercial={row['TotalExternalCommercialLinksInDestinations']} | "
            f"CloakedLinks={row['TotalCloakedInternalLinksInDestinations']} | "
            f"AmazonLinks={row['TotalAmazonLinksInDestinations']} | "
            f"NonAmazonLinks={row['TotalNonAmazonCommercialLinksInDestinations']} | "
            f"{row['HubUrl']}"
        )
        summary.append(f"  Recomendacion: {row['HubRecommendation']}")

    summary.append("")
    summary.append("TOP DESTINOS VALIDADOS")

    for row in destination_validation_rows[:25]:
        summary.append(
            f"- Verdict={row['Verdict']} | Intent={row['IntentScore']} | "
            f"CommercialLinks={row['RenderedCommercialLinks']} | "
            f"ExternalCommercial={row['RenderedExternalCommercialLinks']} | "
            f"Cloaked={row['RenderedCloakedInternalLinks']} | "
            f"Amazon={row['AmazonLinks']} | NonAmazon={row['NonAmazonCommercialLinks']} | "
            f"Retailers={row['RetailersDetected'] or '-'} | "
            f"Reasons={row['CommercialReasons'] or '-'} | "
            f"{row['DestinationUrl']}"
        )

    summary.append("")
    summary.append("ARCHIVOS GENERADOS")
    summary.append(f"hub_destinations.csv: {hub_destinations_csv}")
    summary.append(f"destination_validation.csv: {destination_validation_csv}")
    summary.append(f"destination_links.csv: {destination_links_csv}")
    summary.append(f"destination_network_requests.csv: {destination_network_csv}")
    summary.append(f"hub_summary.csv: {hub_summary_csv}")
    summary.append(f"destination_screenshots/: {screens_dir}")
    summary.append(f"summary.txt: {summary_txt}")
    summary.append("")
    summary.append("INTERPRETACION")
    summary.append("- HUB_FRICTION_OPPORTUNITY: el hub no enlaza fuera, pero los posts destino monetizan o parecen redirigir. Oportunidad: reducir friccion.")
    summary.append("- HUB_AFFILIATE_GAP_PROBABLE: ni hub ni muchos destinos monetizan. Oportunidad mas fuerte: gap real.")
    summary.append("- DEST_MONETIZED_VISIBLE: post destino con enlaces comerciales externos renderizados.")
    summary.append("- DEST_CLOAKED_MONETIZATION_PROBABLE: post destino con enlaces internos tipo /go/, /out/, /comprar/ que probablemente redirigen.")
    summary.append("- DEST_GAP_PROBABLE: post destino comercial sin monetizacion externa renderizada ni cloaking obvio.")
    summary.append("- DEST_AMAZON_TAG_LEAK: posible fuga real de tag Amazon.")
    summary.append("")
    summary.append("NOTA")
    summary.append("- UTM por si solo no se considera afiliacion para evitar falsos positivos.")
    summary.append("- Los enlaces cortos Amazon se clasifican como ShortAmazonUnverifiable porque no se resuelve el destino final para no disparar clics comerciales.")

    summary_txt.write_text("\n".join(summary), encoding="utf-8")

    print()
    print("============================================================")
    print("RESUMEN")
    print("============================================================")
    print(summary_txt.read_text(encoding="utf-8"))
    print()
    print("Archivos generados en:")
    print(out_dir)
    print()


if __name__ == "__main__":
    asyncio.run(main())
