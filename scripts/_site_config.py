#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


CONFIG_TO_GLOBAL = {
    "site_label": "SITE_LABEL",
    "root_host": "ROOT_HOST",
    "expected_amazon_domain": "EXPECTED_AMAZON_DOMAIN",
    "hub_urls": "HUB_URLS",
    "max_destinations_per_hub": "MAX_DESTINATIONS_PER_HUB",
    "max_total_destinations": "MAX_TOTAL_DESTINATIONS",
    "phase07_prefix": "PHASE07_PREFIX",
    "phase08_prefix": "PHASE08_PREFIX",
    "phase09_prefix": "PHASE09_PREFIX",
    "output_slug": "OUTPUT_SLUG",
}


def load_json_config(path):
    config_path = Path(path).expanduser()
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def pop_cli_option(argv, option_name):
    try:
        idx = argv.index(option_name)
    except ValueError:
        return None

    if idx + 1 >= len(argv):
        raise SystemExit(f"ERROR: {option_name} requiere un valor.")

    value = argv[idx + 1]
    del argv[idx:idx + 2]
    return value


def apply_site_config(module_globals, config):
    if not config:
        return

    explicit_keys = set(config)

    for config_key, global_name in CONFIG_TO_GLOBAL.items():
        if config_key in config and global_name in module_globals:
            module_globals[global_name] = config[config_key]

    output_slug = config.get("output_slug")
    if not output_slug:
        return

    derived_prefixes = {
        "phase07_prefix": ("PHASE07_PREFIX", f"affiliate_phase0_7_{output_slug}_"),
        "phase08_prefix": ("PHASE08_PREFIX", f"affiliate_phase0_8_{output_slug}_"),
        "phase09_prefix": ("PHASE09_PREFIX", f"affiliate_phase0_9_{output_slug}_"),
    }

    for config_key, (global_name, value) in derived_prefixes.items():
        if config_key not in explicit_keys and global_name in module_globals:
            module_globals[global_name] = value


def load_site_config_from_cli_or_env(module_globals):
    config_path = pop_cli_option(sys.argv, "--config") or os.environ.get("AFA_SITE_CONFIG")
    if not config_path:
        return None

    config = load_json_config(config_path)
    apply_site_config(module_globals, config)
    return config
