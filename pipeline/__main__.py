"""Pipeline commands; run `python -m pipeline <command> --help` from the repository root."""
import importlib
import sys

# COMMANDS maps each command to its module; host steps reach the network, offline steps refuse to.
COMMANDS = {
    "extract": ("pipeline.samples.extract", "offline: unpack the archives an extraction plan lists"),
    "typical": ("pipeline.datasets.typical", "host: draw the typical pairs and fetch their tarballs"),
    "pairs": ("pipeline.datasets.pairs", "offline: build a pair subset, or merge them into pairs.jsonl"),
    "devset": ("pipeline.datasets.devset", "draw on the host, build offline"),
    "kb": ("pipeline.datasets.kb.select", "fetch Datadog samples on the host, select cards offline"),
    "kb-promote": ("pipeline.datasets.kb.promote", "offline: write kb.jsonl from approved cards"),
    "hn-path-a": ("pipeline.datasets.hn.path_a", "prefilter on the host, screen offline"),
    "hn-path-b": ("pipeline.datasets.hn.path_b", "fetch and verify on the host, match offline"),
    "hn-queue": ("pipeline.datasets.hn.queue", "offline: build the verification queue"),
    "capability": ("pipeline.features.capability", "offline: capability delta of two versions"),
    "smartdiff": ("pipeline.features.smartdiff", "offline: smart-diff of two versions"),
    "intent": ("pipeline.features.intent", "offline: intent profile of one version"),
    "campaign": ("pipeline.features.campaign", "offline: cluster items into campaigns"),
    "run": ("pipeline.experiment.runner", "host: run configurations against vLLM"),
    "report": ("pipeline.results.report", "measures and comparisons as JSON"),
    "tables": ("pipeline.results.tables", "result workbook"),
    "plots": ("pipeline.results.plots", "result figures"),
    "selfcheck": ("pipeline.tests", "run every test module"),
}


def usage():
    width = max(map(len, COMMANDS))
    lines = [f"  {name:<{width}}  {summary}" for name, (_, summary) in COMMANDS.items()]
    return "usage: python -m pipeline <command> [options]\n\ncommands:\n" + "\n".join(lines)


def main(argv):
    if not argv or argv[0] in ("-h", "--help") or argv[0] not in COMMANDS:
        print(usage())
        return 0 if argv and argv[0] in ("-h", "--help") else 2
    module = importlib.import_module(COMMANDS[argv[0]][0])
    return module.main(argv[1:]) or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
