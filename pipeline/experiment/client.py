"""Chat completion requests to the OpenAI-compatible vLLM server."""
import json
import time
import urllib.request

MAX_TOKENS = 512


# call_llm sends one request and retries with an exponential backoff.
def call_llm(base_url, model, messages, seed, timeout, sampling, retries=3):
    payload = json.dumps({"model": model, "messages": messages, "seed": seed,
                          "max_tokens": MAX_TOKENS, **sampling}).encode()
    request = urllib.request.Request(f"{base_url.rstrip('/')}/v1/chat/completions", data=payload,
                                     headers={"Content-Type": "application/json"})
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read())
        # OSError covers ConnectionResetError, which a URLError clause would let escape unretried.
        except (OSError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"failed after {retries} attempts: {last}")
