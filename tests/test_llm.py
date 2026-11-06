import json

import httpx
import pytest

from pulse.llm import (
    LLM,
    GeminiProvider,
    GroqProvider,
    LLMError,
    LLMUnavailable,
    PromptBlocked,
    ProviderError,
    ResultCache,
    run_batched,
)

SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
    "additionalProperties": False,
}
GOOD = '{"answer": "ok"}'


class Fake:
    """Provider whose replies are scripted: a string is returned, an exception is raised."""

    def __init__(self, name, script, min_interval_s=0.0):
        self.name = name
        self.min_interval_s = min_interval_s
        self.script = list(script)
        self.calls = 0
        self.prompts = []

    def generate(self, prompt, schema):
        self.prompts.append(prompt)
        item = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return item


def rate_limited(retry_after=None):
    return ProviderError("rate limited", status=429, retryable=True, retry_after=retry_after)


def make_llm(*providers, **kw):
    sleeps = []
    llm = LLM(providers, sleep=sleeps.append, **kw)
    return llm, sleeps


# ---- retry, failover, guard ------------------------------------------------
def test_returns_parsed_json():
    llm, _ = make_llm(Fake("a", [GOOD]))
    assert llm.complete("hi", SCHEMA) == {"answer": "ok"}
    assert llm.last_provider == "a"


def test_retries_a_429_then_succeeds():
    a = Fake("a", [rate_limited(), GOOD])
    llm, sleeps = make_llm(a)
    assert llm.complete("hi", SCHEMA) == {"answer": "ok"}
    assert a.calls == 2 and len(sleeps) == 1 and llm.stats["retries"] == 1


def test_retry_after_header_is_honoured():
    llm, sleeps = make_llm(Fake("a", [rate_limited(retry_after=7), GOOD]))
    llm.complete("hi", SCHEMA)
    assert sleeps == [7]


def test_backoff_grows_between_retries():
    llm, sleeps = make_llm(Fake("a", [rate_limited(), rate_limited(), GOOD]), base_delay=1.0)
    llm.complete("hi", SCHEMA)
    assert sleeps == [1.0, 2.0]


def test_persistent_429_fails_over_to_the_backup():
    a, b = Fake("a", [rate_limited()]), Fake("b", [GOOD])
    llm, _ = make_llm(a, b, max_retries=2)
    assert llm.complete("hi", SCHEMA) == {"answer": "ok"}
    assert a.calls == 3 and b.calls == 1  # first try plus two retries
    assert llm.last_provider == "b" and llm.stats["failovers"] == 1


def test_a_very_long_retry_after_skips_the_provider_instead_of_waiting():
    a, b = Fake("a", [rate_limited(retry_after=3600)]), Fake("b", [GOOD])
    llm, sleeps = make_llm(a, b, max_wait=60)
    llm.complete("hi", SCHEMA)
    assert a.calls == 1 and sleeps == [] and llm.last_provider == "b"


def test_non_retryable_error_fails_over_without_retrying():
    a = Fake("a", [ProviderError("bad key", status=401)])
    b = Fake("b", [GOOD])
    llm, sleeps = make_llm(a, b)
    llm.complete("hi", SCHEMA)
    assert a.calls == 1 and sleeps == []


def test_malformed_json_is_retried_once_then_fails_over():
    a, b = Fake("a", ["not json"]), Fake("b", [GOOD])
    llm, _ = make_llm(a, b)
    assert llm.complete("hi", SCHEMA) == {"answer": "ok"}
    assert a.calls == 2


def test_output_that_breaks_the_schema_is_treated_the_same_way():
    a, b = Fake("a", ['{"wrong": 1}']), Fake("b", [GOOD])
    llm, _ = make_llm(a, b)
    assert llm.complete("hi", SCHEMA) == {"answer": "ok"}
    assert a.calls == 2


def test_all_providers_failing_raises_and_names_each():
    a = Fake("a", [ProviderError("down", status=500, retryable=True)])
    b = Fake("b", [ProviderError("bad key", status=401)])
    llm, _ = make_llm(a, b, max_retries=1)
    with pytest.raises(LLMUnavailable) as err:
        llm.complete("hi", SCHEMA)
    assert "a:" in str(err.value) and "b:" in str(err.value)


def test_prompt_guard_blocks_before_anything_is_sent():
    a = Fake("a", [GOOD])

    def guard(text):
        if "secret" in text:
            raise PromptBlocked("pii found")

    llm, _ = make_llm(a, prompt_guard=guard)
    with pytest.raises(PromptBlocked):
        llm.complete("my secret", SCHEMA)
    assert a.calls == 0


def test_requests_are_spaced_by_min_interval():
    now = [0.0]
    sleeps = []

    def sleep(s):
        sleeps.append(s)
        now[0] += s

    a = Fake("a", [GOOD], min_interval_s=5.0)
    llm = LLM([a], sleep=sleep, clock=lambda: now[0])
    llm.complete("one", SCHEMA)
    llm.complete("two", SCHEMA)
    assert sleeps == [5.0]


# ---- HTTP providers --------------------------------------------------------
def client_for(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_gemini_request_and_response_shape():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get("x-goog-api-key")
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"thought": True, "text": "hmm"}, {"text": GOOD}]}}]},
            headers={"x-ratelimit-remaining": "9"},
        )

    p = GeminiProvider("KEY123", "gemini-test", client=client_for(handler))
    assert p.generate("hello", SCHEMA) == GOOD  # thought parts are dropped
    assert "gemini-test:generateContent" in seen["url"] and "KEY123" not in seen["url"]
    assert seen["key"] == "KEY123"
    cfg = seen["body"]["generationConfig"]
    assert cfg["responseMimeType"] == "application/json" and cfg["responseJsonSchema"] == SCHEMA
    assert p.last_headers == {"x-ratelimit-remaining": "9"}


def test_groq_request_and_response_shape():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("authorization")
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": GOOD}}]})

    p = GroqProvider("KEY456", "openai/gpt-oss-20b", client=client_for(handler))
    assert p.generate("hello", SCHEMA) == GOOD
    assert seen["auth"] == "Bearer KEY456"
    fmt = seen["body"]["response_format"]
    assert fmt["type"] == "json_schema" and fmt["json_schema"]["strict"] is True
    assert seen["body"]["model"] == "openai/gpt-oss-20b"


def test_http_429_becomes_a_retryable_error_with_retry_after():
    def handler(request):
        return httpx.Response(429, text="slow down", headers={"retry-after": "12"})

    p = GroqProvider("k", "m", client=client_for(handler))
    with pytest.raises(ProviderError) as err:
        p.generate("x", SCHEMA)
    assert err.value.retryable and err.value.retry_after == 12.0 and err.value.status == 429


def test_http_401_is_not_retryable():
    p = GeminiProvider("k", "m", client=client_for(lambda r: httpx.Response(401, text="bad key")))
    with pytest.raises(ProviderError) as err:
        p.generate("x", SCHEMA)
    assert not err.value.retryable


def test_network_failure_is_retryable():
    def handler(request):
        raise httpx.ConnectError("boom")

    p = GroqProvider("k", "m", client=client_for(handler))
    with pytest.raises(ProviderError) as err:
        p.generate("x", SCHEMA)
    assert err.value.retryable


def test_keys_never_appear_in_repr_or_errors():
    p = GeminiProvider("SUPERSECRET", "m", client=client_for(lambda r: httpx.Response(500, text="oops")))
    assert "SUPERSECRET" not in repr(p)
    with pytest.raises(ProviderError) as err:
        p.generate("x", SCHEMA)
    assert "SUPERSECRET" not in str(err.value)


# ---- batching and cache ----------------------------------------------------
ITEM_SCHEMA = {
    "type": "object",
    "properties": {"ids": {"type": "array", "items": {"type": "string"}}},
    "required": ["ids"],
    "additionalProperties": False,
}


class Echo:
    """Provider that echoes the ids found in the prompt."""

    name = "echo"
    min_interval_s = 0.0

    def __init__(self):
        self.calls = 0

    def generate(self, prompt, schema):
        self.calls += 1
        ids = [line.split("|")[0] for line in prompt.splitlines() if "|" in line]
        return json.dumps({"ids": ids})


def batched(llm, items, cache, size=2):
    return run_batched(
        llm,
        "echo-v1",
        items,
        item_id=lambda x: x,
        make_prompt=lambda b: "\n".join(f"{i}|x" for i in b),
        schema=ITEM_SCHEMA,
        extract=lambda data, batch: {i: "done" for i in data["ids"]},
        cache=cache,
        batch_size=size,
    )


def test_batches_split_the_work(tmp_path):
    echo = Echo()
    out = batched(LLM([echo]), ["1", "2", "3", "4", "5"], ResultCache(tmp_path))
    assert echo.calls == 3 and set(out) == {"1", "2", "3", "4", "5"}


def test_rerun_makes_no_new_calls_and_new_items_only_send_the_new_ones(tmp_path):
    cache = ResultCache(tmp_path)
    echo = Echo()
    batched(LLM([echo]), ["1", "2", "3"], cache)
    first = echo.calls
    batched(LLM([echo]), ["1", "2", "3"], cache)
    assert echo.calls == first  # everything came from the cache
    batched(LLM([echo]), ["1", "2", "3", "4"], cache)
    assert echo.calls == first + 1


def test_a_model_that_skips_items_is_an_error(tmp_path):
    class Lazy(Echo):
        def generate(self, prompt, schema):
            return json.dumps({"ids": ["1"]})

    with pytest.raises(LLMError):
        batched(LLM([Lazy()]), ["1", "2"], ResultCache(tmp_path))


def test_duplicate_item_ids_are_rejected(tmp_path):
    with pytest.raises(ValueError):
        batched(LLM([Echo()]), ["1", "1"], ResultCache(tmp_path))
