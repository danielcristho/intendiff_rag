FROM node:24-bookworm-slim@sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54 AS node
FROM python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 diffutils build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /opt/npm
WORKDIR /opt/tools
COPY package.json package-lock.json ./
RUN node /opt/npm/bin/npm-cli.js ci --ignore-scripts --omit=dev
RUN node /opt/npm/bin/npm-cli.js rebuild @dodona/dolos-parsers
ENV PATH="/opt/tools/node_modules/.bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends unzip \
    && rm -rf /var/lib/apt/lists/*
COPY dolos_pairs.mjs /opt/tools/dolos_pairs.mjs
RUN chmod +x /opt/tools/dolos_pairs.mjs \
    && ln -s /opt/tools/dolos_pairs.mjs /usr/local/bin/dolos-pairs
COPY normalize_pair.mjs /opt/tools/normalize_pair.mjs
RUN chmod +x /opt/tools/normalize_pair.mjs \
    && ln -s /opt/tools/normalize_pair.mjs /usr/local/bin/normalize-pair
COPY dolos_fingerprints.mjs /opt/tools/dolos_fingerprints.mjs
RUN chmod +x /opt/tools/dolos_fingerprints.mjs \
    && ln -s /opt/tools/dolos_fingerprints.mjs /usr/local/bin/dolos-fingerprints
