"""Classify third-party services conservatively for audit reporting."""


# These categories indicate advertising, audience measurement, or analytics.
# Other Tracker Radar categories (for example CDN or Embedded Content) remain
# useful evidence, but are not called tracking activity by PolicyTrace.
TRACKING_CATEGORIES = {
    "ad motivated tracking",
    "advertising",
    "analytics",
    "audience measurement",
    "third-party analytics marketing",
    "action pixels",
}


def has_fingerprinting_signal(value):
    """Interpret Tracker Radar's numeric/string fingerprinting field safely."""
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value == 1

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}

    return False


def is_likely_tracking_request(request):
    """Return True only for high-signal tracking or fingerprinting evidence."""
    tracker_info = request.get("tracker_radar") or {}
    categories = tracker_info.get("categories") or []

    normalized_categories = {
        str(category).strip().lower()
        for category in categories
    }

    fingerprinting = has_fingerprinting_signal(
        tracker_info.get("fingerprinting")
    )

    return bool(
        normalized_categories.intersection(TRACKING_CATEGORIES)
        or fingerprinting
    )


def unique_likely_tracking_domains(requests):
    """Return sorted domains with high-signal tracking evidence."""
    return sorted({
        request.get("domain")
        for request in requests
        if request.get("domain") and is_likely_tracking_request(request)
    })
