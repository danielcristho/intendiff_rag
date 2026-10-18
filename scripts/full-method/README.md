# D92 per-model runners

Each `run_<tag>.sh` resumes the frozen D92 batch (973 pairs x IDS-D/IDS-I/VERIFY-I
= 2,919 generations) for one model via the official `run_model`: pins, token
check, vLLM on 127.0.0.1:8101, verification. Stop with Ctrl+C; rerun resumes.

    ./status.sh                  # progress per model
    ./run_qwen25_7b.sh           # then qwen3_8b, phi4_mini, llama31_8b, granite33_8b

One model at a time (a lock enforces it); port 8101 must be free. Logs:
`data/evaluation/full-method-20261012/<tag>.run.log` and `<tag>.server.log`.
