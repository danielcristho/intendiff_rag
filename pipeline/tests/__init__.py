"""Test modules; `python -m pipeline selfcheck [module...]` runs their test_ functions."""
import importlib
import inspect
import traceback

MODULES = ("test_shared", "test_samples", "test_capability", "test_smartdiff", "test_intent",
           "test_campaign", "test_pairs", "test_devset", "test_kb", "test_hn", "test_experiment",
           "test_results", "test_tables", "test_plots")


def main(argv=None):
    selected = [f"test_{name}" for name in argv] if argv else MODULES
    total = failed = 0
    for name in selected:
        module = importlib.import_module(f"pipeline.tests.{name}")
        for test_name, test in inspect.getmembers(module, inspect.isfunction):
            if not test_name.startswith("test_") or test.__module__ != module.__name__:
                continue
            total += 1
            try:
                test()
            except Exception:  # noqa: BLE001 - report every failure, then fail the run
                failed += 1
                print(f"FAIL {name}.{test_name}")
                traceback.print_exc()
    print(f"{total - failed} of {total} tests passed")
    return 1 if failed else 0
