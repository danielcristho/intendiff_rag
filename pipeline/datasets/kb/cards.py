"""The card schema shared by selection and promotion."""

TEXT_FIELDS = ("intent", "behavior_chain", "code_excerpt", "rationale")
SCHEMA = ("id", "name", "label", "campaign", "source", "delta", *TEXT_FIELDS)


# card merges a skeleton row with its written text and keeps the schema fields alone.
def card(row, entry):
    merged = {**row, **{field: entry[field] for field in TEXT_FIELDS}}
    return {field: merged[field] for field in SCHEMA}
