# Positioning against RogueOne

**Source:** Sofaer, David, Kang, Yu, Cao, Yang, Nieh. *RogueOne: Detecting Rogue
Updates via Differential Data-flow Analysis Using Trust Domains.* ICSE 2024.
DOI 10.1145/3597503.3639199. Repository: https://github.com/columbia/rogueone.

Read directly from the paper PDF on 2026-09-13. The related decisions are D18
and D20 in `docs/decisions.md` (on the `latex` branch).

## RogueOne in brief

- **How it works:** it compares the old and the new version of a package. An update is flagged rogue when a **new data flow between trust domains** appears.
- **Trust domain:** objects are grouped by origin: the package itself, each dependency, or a system API. Objects from the same package are assumed to be controlled by the same developer.
- **Data-flow tracking:** through an Object Data-flow Relationship Graph (ODRG) built with abstract interpretation (based on ODGen and FAST).
- **No deny-list:** it does not use a list of suspicious APIs.

**Its threat model matches this study's:** a malicious update to an existing
benign package ("Inject into Source" and "Inject into Repository System" in Ohm
et al.'s taxonomy). Packages malicious from birth, such as typosquats, are out
of scope. That is why typosquats appear here only as KB cards, never as pairs (D13).

## Quotable numbers

**Datasets**

- Multi-version: 333 updates from 12 packages (7 rogue).
- Single-update: 341 updates: 300 benign (latest update of popular and random packages), 29 rogue from Backstabber's Knife Collection, and 12 other rogue.

**Detection**

| Configuration | Dataset | Rogue detected | False positives |
|---|---|---|---|
| RogueOne (default) | single-update | 31/41 (75.6 %) | 14/300 (4.7 %) |
| RogueOne-Paranoid | single-update | 38/41 (92.7 %) | 120/300 (40.0 %) |
| RogueOne (default) | multi-version | 7/7 | 17/326 (5.2 %) |

By attack type, over both datasets combined (48 rogue), detection is 79 % for
default and 94 % for Paranoid.

**Analysis time**

- 5 updates hit the 1-hour timeout.
- The rest average 226.7 s per update; 90 % finish in under 4 s, 95 % in under 30 minutes.
- Errors and timeouts count as benign.

## Ideas taken

| RogueOne idea | Form in IntentDiff-RAG | Status |
|---|---|---|
| Differential analysis: judge the change between versions, not the whole package | smart-diff and capability delta (v_t minus v_{t−1}) | taken |
| Trust domains: what is suspicious is a new interaction with something outside the package | capability delta as a coarse version: newly appearing capabilities (network, exec, fs, dependency) | taken as a concept, without data flow |
| A new dependency as a signal (event-stream / flatmap-stream) | the `package.json` diff is always included, plus the `dependency_change` capability | taken (D15) |
| Single-update dataset: latest updates of popular and random packages as benign, public incidents as rogue | through Wyss et al., who extend this methodology; TYP comes from the Wyss data | taken |
| Errors and timeouts count as benign | invalid output counts as benign, with a sensitivity analysis | taken (D18) |
| Sensitivity trade-off between default and Paranoid | argument for focusing on FPR, and the basis for "partially supported" at the recall margin | taken as an argument |

## Ideas skipped

| RogueOne idea | Why skipped |
|---|---|
| ODRG with abstract interpretation (ODGen/FAST) | heavy and timeout-prone; this study's RQs are about LLMs, not data-flow analysis |
| Recursive analysis of transitive dependencies | needs dependency code and analysis time; outside the eight-week scope |
| Per-value trust domains (Paranoid) | no text-level equivalent, and 40 % FP on the single-update dataset |
| Running RogueOne as a baseline on our data | D20: 226.7 s per update on average, 1-hour timeouts, ODGen setup. Comparing against the paper's numbers is not valid either, because the data differ |

## Lessons that shaped the design

- **Disguised attacks (CC-Harvest).** When the payload uses APIs the previous version already used, default RogueOne misses 10 of 10 cases because there is no new data flow. Capability delta has the same blind spot: the delta can be empty. Recall on MAL pairs with an empty delta is therefore reported separately. Retrieval has no signal on such pairs either, since every card scores 0.
- **RogueOne's false positives resemble our HN categories.** Table 4 (Paranoid counts over both datasets): new dependency 41, install script 14, new system API 8. This supports HN categories 1 (tooling/install script), 4 (network) and 5 (dependency change).
- **Obfuscation.** Minification does not affect RogueOne, but techniques such as a global array cause over-approximation. Robustness to obfuscation is out of scope here.
- **False-positive review** usually takes no more than two minutes per case through a simple UI. That is the same role our audit UI plays in error analysis (EA4).

## How to write about RogueOne in the manuscript

- **Place it in related work** as the closest non-LLM approach to rogue updates. It is strong, but computationally expensive and forced to trade recall for false positives (default vs Paranoid).
- **Do not write that IntentDiff-RAG is better or cheaper** based on the paper's numbers; the data differ.
- **Allowed:** describe the difference in the kind of cost qualitatively (abstract interpretation per update vs one LLM inference per configuration), then present our own latency from RQ4.
