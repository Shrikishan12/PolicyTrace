import re


ACCEPT_TEXTS = [
    "Accept All",
    "Accept",
    "Allow All",
    "Allow",
    "I Agree",
    "Agree",
    "Accept Cookies",
    "Accept All Cookies",
]

REJECT_TEXTS = [
    "Reject All",
    "Reject",
    "Decline",
    "Deny",
    "Reject Cookies",
    "Reject All Cookies",
]


def find_consent_control(page, action):
    """Find a recognised consent button without clicking it."""
    if action == "accept":
        texts = ACCEPT_TEXTS
    elif action == "reject":
        texts = REJECT_TEXTS
    else:
        raise ValueError("action must be 'accept' or 'reject'")

    for text in texts:
        try:
            # An anchored, case-insensitive match avoids clicking controls with
            # unrelated longer labels while accommodating normal case changes.
            button = page.get_by_role(
                "button",
                name=re.compile(rf"^\\s*{re.escape(text)}\\s*$", re.IGNORECASE),
            )

            if button.count() and button.first.is_visible():
                return {
                    "found": True,
                    "label": text,
                    "control": button.first,
                }
        except Exception:
            continue

    return {
        "found": False,
        "label": None,
        "control": None,
    }


def detect_consent_actions(page):
    """Report which recognised consent choices are visible on the page."""
    return [
        action
        for action in ("accept", "reject")
        if find_consent_control(page, action)["found"]
    ]


def click_consent(page, action):
    """Click a recognised consent control and preserve audit details."""
    match = find_consent_control(page, action)

    if not match["found"]:
        return {
            "action": action,
            "clicked": False,
            "status": "not_found",
            "matched_label": None,
        }

    try:
        match["control"].click(timeout=2000)
        return {
            "action": action,
            "clicked": True,
            "status": "clicked",
            "matched_label": match["label"],
        }
    except Exception:
        return {
            "action": action,
            "clicked": False,
            "status": "click_failed",
            "matched_label": match["label"],
        }
