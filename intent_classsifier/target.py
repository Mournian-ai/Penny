def detect_target(text):
    """Detect if user is addressing Penny or someone else."""
    text = text.strip().lower()

    # Keywords that suggest user is talking to chat or others
    not_penny_keywords = ["chat", "guys", "everyone", "folks", "all", "myriad", "alex", "team", "stream", "yall"]

    # Keywords that suggest user is talking to Penny
    penny_keywords = ["penny", "pennybot", "hey penny", "yo penny", "oi penny"]

    for word in penny_keywords:
        if word in text:
            return "penny"

    for word in not_penny_keywords:
        if word in text:
            return "not_penny"

    return "unknown"
