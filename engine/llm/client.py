"""LLM clients. Everything else talks to the LLMClient protocol, so the model is swappable/mockable."""

import json
import logging
import random
import urllib.error
import urllib.request
from typing import Any, Protocol

log = logging.getLogger(__name__)


class LLMError(Exception):
    """The LLM couldn't give a usable answer (offline, timeout, bad JSON)."""


class LLMClient(Protocol):
    def complete_json(self, system: str, user: str, schema: dict, max_tokens: int = 400) -> dict: ...


class LlamaServerClient:
    """llama-server (scripts/llm-server.sh) via its OpenAI-compatible API.

    The reply is constrained to `schema` (json_schema response_format), so enums in the schema
    are the only values the model can produce.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8080", timeout: float = 60, temperature: float = 0.9):
        self.url = base_url.rstrip("/") + "/v1/chat/completions"
        self.timeout = timeout
        self.temperature = temperature

    def complete_json(self, system: str, user: str, schema: dict, max_tokens: int = 400) -> dict:
        body = {
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "reply", "schema": schema}},
            "max_tokens": max_tokens,
            "temperature": self.temperature,
        }
        request = urllib.request.Request(
            self.url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.load(response)
            content = data["choices"][0]["message"]["content"]
            log.info("LLM reply: %s", content)
            result = json.loads(content)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise LLMError(f"LLM server unreachable at {self.url}: {e}") from e
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise LLMError(f"LLM returned unusable output: {e}") from e
        if not isinstance(result, dict):
            raise LLMError("LLM reply is not a JSON object")
        return result


class RandomLLM:
    """Offline stand-in: a random answer that fits the schema. Used as fallback and in tests."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def complete_json(self, system: str, user: str, schema: dict, max_tokens: int = 400) -> dict:
        return _sample(schema, self.rng)


def _sample(schema: dict, rng: random.Random) -> Any:
    if "enum" in schema:
        return rng.choice(schema["enum"])
    match schema.get("type"):
        case "object":
            return {k: _sample(v, rng) for k, v in schema.get("properties", {}).items()}
        case "array":
            n = rng.randint(schema.get("minItems", 0), schema.get("maxItems", 3))
            return [_sample(schema["items"], rng) for _ in range(n)]
        case "string":
            return rng.choice(schema.get("examples", [""]))
        case "integer":
            return rng.randint(schema.get("minimum", 0), schema.get("maximum", 10))
        case "boolean":
            return rng.random() < 0.5
    return None
