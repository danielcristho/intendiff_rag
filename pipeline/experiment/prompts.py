"""Prompt assembly for one configuration; the texts and configurations live in pipeline/specs."""
from pipeline.shared.specs import configurations, prompt_text

TEXT = prompt_text()
SYSTEM, FORMAT_INSTRUCTION, MISSING = TEXT["system"], TEXT["format_instruction"], TEXT["missing"]
CONFIGS = list(configurations())


def uses_intent(config):
    return configurations()[config]["intent"]


def uses_retrieval(config):
    return configurations()[config]["cards"] != "none"


def as_text(value):
    if value is None or value == "" or value == [] or value == {}:
        return MISSING
    if isinstance(value, dict):
        return "\n".join(f"{name}: {command}" for name, command in value.items())
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


# intent_block renders the intent profile, which comes from the previous version.
def intent_block(pair):
    intent = pair.get("intent") or {}
    if not isinstance(intent, dict):
        intent = {"description": intent}
    return (f"Package intent profile (from version {pair.get('before', '?')}):\n"
            f"Description: {as_text(intent.get('description'))}\n"
            f"Keywords: {as_text(intent.get('keywords'))}\n"
            f"Scripts:\n{as_text(intent.get('scripts'))}\n"
            f"README excerpt:\n{as_text(intent.get('readme'))}\n\n")


# examples_block labels each card by the card in that slot, since the order is counterbalanced.
def examples_block(cards):
    if not cards:
        return ""
    parts = ["Reference examples:\n"]
    for position, card in enumerate(cards, start=1):
        parts.append(f"\nExample {position} (label: {str(card.get('label', '')).upper()})\n"
                     f"Package purpose: {as_text(card.get('intent'))}\n"
                     f"Behavior: {as_text(card.get('behavior_chain'))}\n"
                     f"Code excerpt:\n{as_text(card.get('code_excerpt'))}\n"
                     f"Why: {as_text(card.get('rationale'))}\n")
    parts.append("\n---\n\n")
    return "".join(parts)


# build returns the chat messages; the package name and the capability delta stay out of them.
def build(config, pair, cards=()):
    if config not in CONFIGS:
        raise ValueError(f"unknown configuration: {config}")
    user = (f"{examples_block(cards) if uses_retrieval(config) else ''}"
            "Update under review\n"
            f"Version change: {pair.get('before', '?')} -> {pair.get('after', '?')}\n"
            f"{intent_block(pair) if uses_intent(config) else ''}"
            f"Smart-diff:\n{pair.get('diff', '')}\n\n"
            f"{FORMAT_INSTRUCTION}")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
