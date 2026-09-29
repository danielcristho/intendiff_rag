"""Token counters for the context budgets, which are measured in Qwen2.5-Coder-3B tokens."""

TOKENIZER = "Qwen/Qwen2.5-Coder-3B-Instruct"


def qwen_counter(model=TOKENIZER):
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:  # pragma: no cover - depends on the host
        raise RuntimeError("install transformers, or pass a counter explicitly") from exc
    tokenizer = AutoTokenizer.from_pretrained(model)
    return lambda text: len(tokenizer(text)["input_ids"])


# approx_counter counts four characters per token, for quick runs without the tokenizer.
def approx_counter(text):
    return len(text) // 4
