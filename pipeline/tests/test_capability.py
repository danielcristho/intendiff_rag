from pipeline.features.capability import MAX_EVIDENCE, capabilities, delta, delta_evidence, explain_version, scan_version
from pipeline.tests.fixtures import Versions

pkg = Versions()


def test_network_counts_modules_node_prefix_and_browser_calls():
    assert "network" in scan_version(pkg({"a.js": "const h = require('https');"}))
    assert "network" in scan_version(pkg({"a.js": "import dns from 'node:dns';"}))
    assert "network" in scan_version(pkg({"a.js": "await fetch(url);"}))
    assert "network" in scan_version(pkg({"a.js": "navigator.sendBeacon(u, d);"}))
    assert "network" not in scan_version(pkg({"a.js": "const p = require('path');"}))
    assert "process_exec" in scan_version(pkg({"a.js": "const {exec} = require('child_process');"}))


def test_host_info_counts_whole_environment_reads_not_named_ones():
    assert "host_info" in scan_version(pkg({"a.js": "send(JSON.stringify(process.env));"}))
    assert "host_info" in scan_version(pkg({"a.js": "os.hostname();"}))
    assert "host_info" not in scan_version(pkg({"a.js": "if (process.env.NODE_ENV) {}"}))
    assert "host_info" not in scan_version(pkg({"a.js": 'const k = process.env["API_KEY"];'}))


def test_sensitive_files_browser_data_and_dynamic_code_are_detected():
    assert "fs_sensitive" in scan_version(pkg({"a.js": "read('~/.ssh/id_rsa');"}))
    assert "browser_data" in scan_version(pkg({"a.js": "const c = document.cookie;"}))
    assert "browser_data" in scan_version(pkg({"a.js": 'el.addEventListener("submit", f);'}))
    assert "dynamic_code" in scan_version(pkg({"a.js": "eval(payload);"}))
    assert "dynamic_code" in scan_version(pkg({"a.js": "new Function('return 1')();"}))


def test_obfuscation_starts_at_two_hundred_packed_characters():
    assert "obfuscation" in scan_version(pkg({"a.js": "var _0x4f2a = 1;"}))
    assert "obfuscation" in scan_version(pkg({"a.js": "Buffer.from(s, 'base64');"}))
    assert "obfuscation" in scan_version(pkg({"a.js": "atob(s);"}))
    assert "obfuscation" in scan_version(pkg({"a.js": f'var s = "{"A" * 200}";'}))
    assert "obfuscation" not in scan_version(pkg({"a.js": 'var s = "' + "A" * 199 + '";'}))
    assert "obfuscation" not in scan_version(pkg({"a.js": 'var s = "' + "hello world " * 30 + '";'}))


def test_install_hooks_count_and_binary_files_do_not_crash_the_scan():
    assert "install_script" in scan_version(pkg({"package.json": '{"scripts": {"postinstall": "node s.js"}}'}))
    assert "install_script" not in scan_version(pkg({"package.json": '{"scripts": {"test": "jest"}}'}))
    assert scan_version(pkg({"logo.png": b"\x89PNG\r\n\x1a\n\x00\xff", "a.js": "x=1;"})) == set()


def test_delta_lists_new_capabilities_in_table_order():
    before = pkg({"a.js": "const h = require('https');", "package.json": "{}"})
    after = pkg({"a.js": "const h = require('https');\nconst {exec} = require('child_process');\neval(x);",
                 "package.json": "{}"})
    assert delta(before, after) == ["process_exec", "dynamic_code"]


def test_a_changed_install_command_enters_the_delta():
    before = pkg({"package.json": '{"scripts": {"postinstall": "node build.js"}}'})
    assert delta(before, pkg({"package.json": '{"scripts": {"postinstall": "node evil.js"}}'})) == ["install_script"]
    assert delta(before, pkg({"package.json": '{"scripts": {"postinstall": "node build.js"}}'})) == []


def test_dependency_change_means_a_new_name_or_a_spec_off_the_registry():
    before = pkg({"package.json": '{"dependencies": {"axios": "^1.0.0"}}'})
    for after in ('{"axios": "^1.0.0", "x": "^1.0.0"}', '{"axios": "git+https://e.com/a.git"}', '{"axios": "user/repo"}'):
        assert delta(before, pkg({"package.json": f'{{"dependencies": {after}}}'})) == ["dependency_change"]
    assert delta(before, pkg({"package.json": '{"dependencies": {"axios": "^2.0.0"}}'})) == []


def test_large_deletion_needs_half_the_text_files_gone():
    four = pkg({"a.js": "1", "b.js": "1", "c.js": "1", "d.js": "1"})
    assert delta(four, pkg({"a.js": "1", "b.js": "1"})) == ["large_deletion"]
    assert delta(four, pkg({"a.js": "1", "b.js": "1", "c.js": "1"})) == []


def test_a_package_without_predecessor_reports_its_whole_capability_set():
    card = pkg({"a.js": "require('https'); eval(x);", "package.json": '{"scripts": {"install": "s"}}'})
    assert capabilities(card) == ["network", "dynamic_code", "install_script"]


def test_evidence_names_file_line_and_match_for_delta_signals_only():
    before = pkg({"index.js": "module.exports = s => s.trim();", "package.json": "{}"})
    after = pkg({"index.js": "module.exports = s => s.trim();",
                 "scripts/setup.js": "const https = require('https');\nconst env = JSON.stringify(process.env);\n",
                 "package.json": '{"scripts": {"preinstall": "node ./scripts/setup.js"}}'})
    why = delta_evidence(before, after)
    assert set(why) == {"network", "host_info", "install_script"}
    assert why["network"][0]["file"] == "scripts/setup.js" and why["network"][0]["line"] == 1
    assert why["host_info"][0]["line"] == 2 and why["install_script"][0]["hook"] == "preinstall"
    assert set(delta_evidence(pkg({"a.js": "require('https');"}), pkg({"a.js": "require('https'); eval(x);"}))) \
        == {"dynamic_code"}


def test_change_signal_evidence_names_the_dependency_and_the_counts():
    before = pkg({"package.json": '{"dependencies": {"axios": "^1.0.0"}}'})
    dep = delta_evidence(before, pkg({"package.json": '{"dependencies": {"axios": "git+https://e.com/a.git"}}'}))
    assert dep["dependency_change"][0]["dependency"] == "axios" and dep["dependency_change"][0]["before"] == "^1.0.0"
    four = pkg({"a.js": "1", "b.js": "1", "c.js": "1", "d.js": "1"})
    assert delta_evidence(four, pkg({"a.js": "1"}))["large_deletion"] == [{"removed": 3, "of": 4}]
    assert len(explain_version(pkg({"a.js": "\n".join("eval(x);" for _ in range(10))}))["dynamic_code"]) == MAX_EVIDENCE
