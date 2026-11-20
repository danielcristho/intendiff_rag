# Security policy

## Reporting a vulnerability

Do not open a public issue. Use the repository's **Security** tab and choose **Report a vulnerability**.

Include the affected version or commit, the steps to reproduce and the impact. Maintainers work on a best-effort basis, will reply as soon as they can, and will agree a disclosure date with you.

A malicious npm package is not a vulnerability in this project. Report a new one to npm; the packages named in `data/` are already known.

## Supported versions

IntentDiff-RAG is a research experiment with pre-releases only. Only the `main` branch receives fixes.

## What to keep in mind

The pipeline handles malicious npm packages. It analyses them statically: extraction runs in `docker run --network none`, rejects archive members that escape the target directory or are links, and checks each archive's sha256 first. Anything that makes the pipeline install or execute sample code, write outside the extraction directory, or reach the network from that container is in scope.

Sample archives are not distributed. `data/` still holds malicious code as text, in diffs and knowledge-base excerpts; never run it.

The audit UI has no authentication: the annotator name only picks a file. Run it on localhost or a trusted network (`BIND_ADDR` in `.env`), never on the public internet.
