PRIVACY_ACTIONS = {
    "collect", "gather", "obtain", "receive",
    "share", "disclose", "sell", "use", "process",
    "store", "retain", "keep",
}

ACTION_CATEGORY = {
    "collect": "collect", "gather": "collect", "obtain": "collect", "receive": "collect",
    "share": "share", "disclose": "share",
    "use": "use", "process": "use",
    "sell": "sell",
    "store": "retain", "retain": "retain", "keep": "retain",
}
def validate_claim(claim):
    try:
        problems = []

        if not claim:
            return {
                "valid": False,
                "status": "failed",
                "needs_llm": True,
                "llm_mode": "extract",
                "problems": ["claim is empty"],
            }

        if not claim.get("sentence"):
            problems.append("missing sentence")

        action = claim.get("action")
        action_ok = bool(action) and action in PRIVACY_ACTIONS
        if not action:
            problems.append("missing action")
        elif action not in PRIVACY_ACTIONS:
            problems.append("unknown action")

        if claim.get("polarity") not in {"affirms", "denies"}:
            problems.append("invalid polarity")

        has_context = any(claim.get(f) for f in ("actor", "data_object", "entity"))
        if action_ok and not has_context:
            problems.append("no actor/data_object/entity found")

        # FIX 2: three-way status instead of binary valid/needs_llm, so the
        # caller knows WHICH llm_fallback mode to use.
        if not action_ok:
            status = "failed"
            llm_mode = "extract"  # nothing usable to repair — start over
        elif not has_context or "invalid polarity" in problems:
            status = "partial"
            llm_mode = "repair"   # action is right, fill in the rest
        else:
            status = "complete"
            llm_mode = None

        result = {
            "valid": status == "complete",
            "status": status,
            "needs_llm": status != "complete",
            "llm_mode": llm_mode,
            "problems": problems,
        }

        if action_ok:
            result["action_category"] = ACTION_CATEGORY[action]

        return result

    except Exception as ex:
        print(f"[ERROR] Claim validation failed: {ex}")
        return {
            "valid": False,
            "status": "failed",
            "needs_llm": True,
            "llm_mode": "extract",
            "problems": [f"validator error: {str(ex)}"],
        }
def validate_claims(claims):
    try:
        results = []
        for claim in claims:
            validation = validate_claim(claim)
            results.append({"claim": claim, "validation": validation})
        return results
    except Exception as ex:
        print(f"[ERROR] Claims validation failed: {ex}")
        return []