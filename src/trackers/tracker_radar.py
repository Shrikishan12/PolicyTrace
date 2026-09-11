import json
from pathlib import Path

import tldextract


BASE_DIR = Path(__file__).resolve().parents[2]


TRACKER_RADAR_DIR = (
    BASE_DIR
    / "data"
    / "trackers"
    / "tracker-radar"
    / "domains"
    / "US"
)


def get_registered_domain(hostname):
    try:
        extracted = tldextract.extract(hostname)

        if not extracted.domain or not extracted.suffix:
            return None

        return f"{extracted.domain}.{extracted.suffix}"

    except Exception as ex:
        print(f"[ERROR] Could not extract registered domain: {ex}")
        return None


def lookup_domain(hostname):
    try:
        registered_domain = get_registered_domain(
            hostname
        )

        if not registered_domain:
            return None

        file_path = (
            TRACKER_RADAR_DIR
            / f"{registered_domain}.json"
        )

        if not file_path.exists():
            return None

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        owner = data.get(
            "owner",
            {}
        )

        subdomains = data.get(
            "subdomains",
            []
        )

        return {
            "observed_domain": hostname,
            "tracker_radar_domain": data.get("domain"),
            "owner": owner.get("name"),
            "display_name": owner.get("displayName"),
            "categories": data.get("categories", []),
            "fingerprinting": data.get("fingerprinting"),
            "prevalence": data.get("prevalence"),
            "cookies": data.get("cookies"),
            "types": data.get("types", []),
            "subdomains": subdomains,
            "source": data.get("source")
        }

    except json.JSONDecodeError as ex:
        print(
            f"[ERROR] Invalid JSON for {hostname}: {ex}"
        )

        return None

    except Exception as ex:
        print(
            f"[ERROR] Tracker Radar lookup failed for {hostname}: {ex}"
        )

        return None