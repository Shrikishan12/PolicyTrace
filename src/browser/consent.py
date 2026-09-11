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


def click_consent(page, action):
    if action == "accept":
        texts = ACCEPT_TEXTS
    elif action == "reject":
        texts = REJECT_TEXTS
    else:
        raise ValueError("action must be 'accept' or 'reject'")

    for text in texts:
        try:
            button = page.get_by_role(
                "button",
                name=text,
                exact=True
            )

            if button.count() > 0:
                button.first.click(timeout=2000)
                return True

        except Exception:
            continue

    return False