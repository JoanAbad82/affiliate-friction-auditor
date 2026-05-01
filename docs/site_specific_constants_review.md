# Site-specific constants review

Generated during phase 1.2A.

Goal: identify values that should move from prototype scripts into configuration files.

## Matches

### scripts/phase0_7_destination_posts.py

25:SITE_LABEL = "Nolodejesescapar"
26:ROOT_HOST = "nolodejesescapar.com"
27:EXPECTED_AMAZON_DOMAIN = "amazon.es"
29:HUB_URLS = [
30:    "https://nolodejesescapar.com/ofertas-en-smartphone",
31:    "https://nolodejesescapar.com/ofertas-de-drones",
32:    "https://nolodejesescapar.com/pc-accesorios",
35:MAX_DESTINATIONS_PER_HUB = 12
36:MAX_TOTAL_DESTINATIONS = 36
122:HUB_PATHS = {urllib.parse.urlparse(u).path.rstrip("/").lower() for u in HUB_URLS}
134:out_dir = desktop_dir() / f"affiliate_phase0_7_nolodejesescapar_{stamp}"
242:    return host == ROOT_HOST or host.endswith("." + ROOT_HOST)
319:    marketplace_ok = EXPECTED_AMAZON_DOMAIN in host
506:    return rows[:MAX_DESTINATIONS_PER_HUB]
815:        for hub_idx, hub_url in enumerate(HUB_URLS, start=1):
816:            print(f"[HUB {hub_idx}/{len(HUB_URLS)}] {hub_url}")
870:            if len(unique_destinations) >= MAX_TOTAL_DESTINATIONS:
899:    for hub_url in HUB_URLS:
1034:    summary.append(f"Web analizada: {SITE_LABEL}")
1039:    for url in HUB_URLS:

### scripts/phase0_8_opportunity_matrix.py

11:SITE_LABEL = "Nolodejesescapar"
12:ROOT_HOST = "nolodejesescapar.com"
13:PHASE07_PREFIX = "affiliate_phase0_7_nolodejesescapar_"
14:PHASE08_PREFIX = "affiliate_phase0_8_nolodejesescapar_"
105:    return host == ROOT_HOST or host.endswith("." + ROOT_HOST)
166:        folder_candidates.extend([p for p in root.glob(PHASE07_PREFIX + "*") if has_required_files(p)])
167:        zip_candidates.extend([p for p in root.glob(PHASE07_PREFIX + "*.zip") if p.is_file()])
180:        extracted_candidates = [p for p in extract_root.rglob(PHASE07_PREFIX + "*") if has_required_files(p)]
189:    print("Coloca la carpeta o ZIP affiliate_phase0_7_nolodejesescapar_* en Desktop, Downloads o $HOME/affiliate_phase0.", file=sys.stderr)
470:    out_dir = desktop_dir() / f"{PHASE08_PREFIX}{stamp}"
659:    lines.append(f"Web analizada: {SITE_LABEL}")

### scripts/phase0_9_product_offer.py

10:SITE_LABEL = "Nolodejesescapar"
11:PHASE08_PREFIX = "affiliate_phase0_8_nolodejesescapar_"
12:PHASE09_PREFIX = "affiliate_phase0_9_nolodejesescapar_"
151:        folder_candidates.extend([p for p in root.glob(PHASE08_PREFIX + "*") if has_required_files(p)])
152:        zip_candidates.extend([p for p in root.glob(PHASE08_PREFIX + "*.zip") if p.is_file()])
164:    print("Coloca affiliate_phase0_8_nolodejesescapar_* en Desktop, Downloads o $HOME/affiliate_phase0.", file=sys.stderr)
166:    print("python3 phase0_9_nolodejesescapar_product_offer.py /ruta/al/phase0_8_outputs.zip", file=sys.stderr)
367:    lines.append(f"- Web auditada: **{SITE_LABEL}**.")
595:    out_dir = desktop_dir() / f"{PHASE09_PREFIX}{stamp}"
689:    summary_lines.append(f"Web base: {SITE_LABEL}")

## Recommendation for phase 1.2B

- Add `--config` support to phase 0.7.
- Add `--input` support to phase 0.8 and 0.9.
- Keep demo config public-safe.
- Keep real per-site configs untracked unless explicitly approved.
- Move hardcoded target URLs out of reusable logic.
