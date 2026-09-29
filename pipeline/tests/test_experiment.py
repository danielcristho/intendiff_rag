import time
import urllib.request

from pipeline.experiment import client
from pipeline.experiment.parsing import parse_verdict
from pipeline.experiment.prompts import CONFIGS, FORMAT_INSTRUCTION, MISSING, SYSTEM, build, uses_retrieval
from pipeline.experiment.retrieval import rank, retrieval_log, retrieve, score
from pipeline.experiment.runner import done_keys, run_key
from pipeline.tests.fixtures import temp_dir

PAIR = {"id": "p1", "name": "fmt-cli", "before": "2.0.3", "after": "2.0.4", "delta": ["network"],
        "intent": {"description": "Formatter CLI", "keywords": ["format"], "scripts": {"test": "jest"},
                   "readme": "Formats files."}, "diff": "+const https = require('https');"}
CARDS = [{"id": "b1", "label": "benign", "intent": "CLI with opt-in telemetry", "behavior_chain": "run -> counter",
          "code_excerpt": "post(c)", "rationale": "Opt-in."},
         {"id": "m1", "label": "malicious", "intent": "Formatter", "behavior_chain": "install -> env -> POST",
          "code_excerpt": "https.request(e)", "rationale": "Mismatch."}]
KB = [{"id": "m1", "label": "malicious", "delta": ["network"], "campaign": "c1", "name": "a"},
      {"id": "m2", "label": "malicious", "delta": ["network"], "campaign": "c2", "name": "b"},
      {"id": "b1", "label": "benign", "delta": ["network"], "campaign": "c3", "name": "c"}]
TARGET = {"id": "p1", "name": "z", "campaign": "c9", "delta": ["network"]}


def test_the_prompt_hides_the_name_and_delta_but_keeps_the_version_change():
    system, user = build("E4", PAIR, CARDS)
    body = user["content"]
    assert system["content"] == SYSTEM and "fmt-cli" not in body and "2.0.3 -> 2.0.4" in body
    assert "network" not in body.replace("require('https')", "")
    assert body.index("Reference examples") < body.index("Update under review") < body.index("Respond with JSON only")
    assert "Example 1 (label: BENIGN)" in body and "Example 2 (label: MALICIOUS)" in body


def test_each_configuration_adds_or_drops_the_intent_and_examples_blocks():
    assert "Package intent profile" in build("E4", PAIR, CARDS)[1]["content"]
    assert "Package intent profile" not in build("E4-noint", PAIR, CARDS)[1]["content"]
    assert "Reference examples" not in build("E0", PAIR, [])[1]["content"]
    assert "Package intent profile" not in build("E0-noint", PAIR, [])[1]["content"]
    for config in CONFIGS:
        messages = build(config, PAIR, CARDS if uses_retrieval(config) else [])
        assert messages[0]["content"] == SYSTEM and messages[1]["content"].endswith(FORMAT_INSTRUCTION)
    assert f"Keywords: {MISSING}" in build("E0", dict(PAIR, intent={"description": "Only this"}), [])[1]["content"]
    try:
        build("E1", PAIR, [])
    except ValueError:
        return
    raise AssertionError("an unknown configuration must be rejected")


def test_retrieval_excludes_the_same_package_or_campaign_and_breaks_ties_by_hash():
    assert score(["x"], ["x"]) == 1.0 and score([], []) == 0.0 and score(["x", "y"], ["x"]) == 0.5
    assert retrieve("E0", TARGET, KB) == [] and retrieve("E4", TARGET, []) == []
    assert all(card["id"] != "m1" for card in rank(dict(TARGET, campaign="c1"), KB))
    assert all(card["id"] != "m2" for card in rank(dict(TARGET, name="b"), KB))
    assert [c["id"] for c in rank(TARGET, KB)] == [c["id"] for c in rank(TARGET, list(reversed(KB)))]


def test_contrastive_configurations_share_cards_and_counterbalance_the_order():
    assert {c["label"] for c in retrieve("E4", TARGET, KB)} == {"malicious", "benign"}
    assert retrieve("E4", TARGET, KB) == retrieve("E4-noint", TARGET, KB)
    top = retrieve("E3", TARGET, KB)[0]["id"]
    for config in ("E3-k2", "E4"):
        assert [c["id"] for c in retrieve(config, TARGET, KB)].index(top) == \
            [c["id"] for c in retrieve("E3-k2", TARGET, KB)].index(top)
    positions = {next(i for i, c in enumerate(retrieve("E4", dict(TARGET, id=f"p{n}"), KB)) if c["label"] == "malicious")
                 for n in range(12)}
    assert positions == {0, 1} and len(retrieve("E3-k2", TARGET, [KB[0]])) == 1
    log = retrieval_log(TARGET, retrieve("E4", TARGET, KB))
    assert [entry["position"] for entry in log] == [1, 2] and all(entry["score"] == 1.0 for entry in log)


def test_a_verdict_needs_the_three_keys_with_the_right_types():
    ok = '{"evidence":["+x"],"reason":"r","verdict":"benign"}'
    assert parse_verdict(f"Here it is: {ok}")["verdict"] == "benign"
    assert parse_verdict(f"{ok}\nNote: the object {{...}} above is my answer.") is not None
    assert parse_verdict("no json here") is None and parse_verdict('{"broken": }') is None
    assert parse_verdict('{"evidence":[],"reason":"r","verdict":"MALICIOUS "}')["verdict"] == "malicious"
    for bad in ('{"evidence":[],"reason":"r","verdict":"suspicious"}', '{"evidence":"+x","reason":"r","verdict":"benign"}',
                '{"evidence":[1],"reason":"r","verdict":"benign"}', '{"evidence":[],"verdict":"benign"}'):
        assert parse_verdict(bad) is None
    assert parse_verdict('{"evidence":[],"reason":"r","verdict":"benign","extra":1}') is not None


def test_a_transport_error_is_retried_and_a_resume_skips_only_real_results():
    path = temp_dir() / "r.jsonl"
    path.write_text('{"run_key":"m|E0|a|0|0.0","error":"refused"}\n{"run_key":"m|E4|a|0|0.0","verdict":"benign"}\n'
                    '{"run_key":"m|E3|a|0|0.0","verdict":null,"json_valid":false}\n')
    assert done_keys(path) == {"m|E4|a|0|0.0", "m|E3|a|0|0.0"}
    assert run_key("m", "E0", "a", 0, 0.0) != run_key("m", "E0", "a", 0, 0.7)
    attempts = []

    def refuse(*_args, **_kwargs):
        attempts.append(1)
        raise ConnectionResetError(104, "Connection reset by peer")

    real = urllib.request.urlopen, time.sleep
    urllib.request.urlopen, time.sleep = refuse, lambda _seconds: None
    try:
        client.call_llm("http://x", "m", [], 0, 1, {"temperature": 0})
    except RuntimeError as exc:
        assert "failed after 3 attempts" in str(exc)
    finally:
        urllib.request.urlopen, time.sleep = real
    assert len(attempts) == 3
