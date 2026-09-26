# Deploying to the GPU host

`gpu-host` is shared with production. The two risks below matter more than
the command sequence.

## Read first: two risks

**1. vLLM can take down production.** vLLM pre-allocates
`--gpu-memory-utilization` as a fraction of **total** GPU memory, not of what is
free. Left at the 0.9 default it claims roughly 11 GiB of the 12 GiB card, and
`production-service` sharing that card runs out of memory.

Check what is genuinely free, with yolo running:

```
nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv
```

Then set `VLLM_GPU_UTIL` below that figure. For scale: Qwen2.5-Coder-3B needs
about 6.9 GiB and Qwen3-4B about 11.95 GiB (D44). If less than that is free,
**do not force it** — schedule a window with yolo stopped, or use another
machine (D45, option A).

**2. The audit UI has no authentication.** Ports publish to `0.0.0.0`, so anyone
who can reach the host can read and change research labels. There is no login
and no token.

To narrow that without losing remote access, set `BIND_ADDR` in `.env` to the
host's VPN address:

```
BIND_ADDR=192.0.2.11
```

That matches how the other containers on this host are published and keeps the
ports off the LAN. `BIND_ADDR=127.0.0.1` closes them entirely, reachable then
through `ssh -L 5174:localhost:5174 <user>@<gpu-host>`.

## Steps

```bash
# 1. Get the code
git clone git@github.com:danielcristho/intendiff_rag.git
cd intendiff_rag

# 2. Configure
cp .env.example .env
sed -i "s/^APP_UID=.*/APP_UID=$(id -u)/; s/^APP_GID=.*/APP_GID=$(id -g)/" .env

# 3. Confirm the ports are still free on this host
docker ps --format '{{.Names}}\t{{.Ports}}'

# 4. Start the audit UI (no GPU required)
docker compose up -d --build backend frontend
curl localhost:8100/health          # -> ok
```

Open the UI at `http://<host>:5174`. Each annotator enters their own name at the
identity gate, and their decisions are stored separately in
`data/audit_decisions.<name>.json`.

## Model server (only while running experiments)

```bash
# Re-read the warnings above first.
docker compose --profile model up -d vllm
docker compose logs -f vllm            # wait for "Application startup complete"

python pipeline/runner.py --model Qwen/Qwen2.5-Coder-3B-Instruct
# --base-url already defaults to http://localhost:8101

docker compose --profile model down    # release the GPU as soon as you are done
```

vLLM deliberately has no `restart:` policy — a reboot must not silently seize
the GPU.

## Data

`./data` is bind-mounted into the container and holds the only copy of your
research labels. It is an artefact you cannot regenerate:
`audit_decisions.*.json` is in `.gitignore`, so it is never pushed.

```bash
tar czf ~/audit-backup-$(date +%F).tar.gz data/
```

Back up before Gate G1, and after every long labelling session.

## Updates

```bash
git pull
docker compose up -d --build backend frontend
```

While editing code, `make docker-watch` (`docker compose watch backend frontend`)
rebuilds and replaces a container whenever its sources change, so no `down`/`up` is
needed. Each rebuild is a full image build, so a backend change takes as long as a
release compile of `backend/src`. Ctrl-C stops the watch; the containers keep running.

The backend and frontend containers are stateless; all state lives in `./data`.
