"""Study definitions kept as data in pipeline/specs, so code holds no research labels."""
import json
from pathlib import Path

SPECS = Path(__file__).resolve().parent.parent / "specs"


def load_spec(name):
    return json.loads((SPECS / f"{name}.json").read_text())


# hn_categories maps each category number to its name, search keywords and filter signals.
def hn_categories():
    return {int(number): {**spec, "signals": set(spec["signals"])}
            for number, spec in load_spec("hn_categories").items()}


def configurations():
    return load_spec("configurations")


def prompt_text():
    return load_spec("prompt")
