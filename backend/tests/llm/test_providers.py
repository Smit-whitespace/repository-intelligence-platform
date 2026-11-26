"""Tests for the provider adapters and the factory.

Network calls are replaced with ``httpx.MockTransport`` (OpenAI-compatible)
or a fake SDK client (Anthropic), so no API key or server is needed.
"""

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from app.chat.exceptions import ChatProviderError
from app.chat.models import (
    ChatMessage,
    ChatPrompt,
    ChatRole,
)
from app.chat.ollama_provider import (
    MAX_OUTPUT_TOKENS,
    TRUNCATION_NOTE,
    OllamaChatProvider,
)
from app.core.config.models import OllamaSettings
from app.indexing.exceptions import EmbeddingError
from app.indexing.ollama_provider import OllamaEmbeddingProvider
from app.llm.config import (
    ModelConfiguration,
    Task,
)
from app.llm.exceptions import ModelConfigurationError
from app.llm.factory import (
    LazyEmbeddingProvider,
    build_chat_provider,
    build_embedding_provider,
)
from app.llm.providers.anthropic_provider import AnthropicChatProvider
from app.llm.providers.openai_compatible import (
    OpenAICompatibleChatProvider,
    OpenAICompatibleEmbeddingProvider,
)
from app.llm.resolver import ModelResolver

PROMPT = ChatPrompt(
    messages=[
        ChatMessage(
            role=ChatRole.SYSTEM,
            content="Answer from the repository context.",
        ),
        ChatMessage(
            role=ChatRole.USER,
            content="Where are edits applied?",
        ),
    ],
)


def _client(
    handler: Any,
) -> httpx.Client:
    return httpx.Client(
        transport=httpx.MockTransport(
            handler,
        ),
    )


# --- OpenAI-compatible chat ----------------------------------------------


def test_openai_compatible_generate_sends_messages_and_reads_the_answer() -> None:
    seen: dict = {}

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)

        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": "In change_applier.py"}},
                ],
            },
        )

    provider = OpenAICompatibleChatProvider(
        base_url="https://api.example.test/v1/",
        model="gpt-5",
        api_key="sk-test",
        client=_client(handler),
    )

    assert provider.generate(PROMPT).content == "In change_applier.py"

    assert seen["url"] == "https://api.example.test/v1/chat/completions"

    assert seen["body"]["model"] == "gpt-5"

    assert [message["role"] for message in seen["body"]["messages"]] == [
        "system",
        "user",
    ]


def test_openai_compatible_stream_yields_deltas_until_done() -> None:
    events = [
        {"choices": [{"delta": {"role": "assistant"}}]},
        {"choices": [{"delta": {"content": "Hello"}}]},
        {"choices": [{"delta": {"content": " world\nline 2"}}]},
    ]

    body = "".join(
        f"data: {json.dumps(event)}\n\n"
        for event in events
    ) + "data: [DONE]\n\n" + 'data: {"choices": [{"delta": {"content": "ignored"}}]}\n\n'

    provider = OpenAICompatibleChatProvider(
        base_url="https://api.example.test/v1",
        model="gpt-5",
        api_key=None,
        client=_client(
            lambda request: httpx.Response(200, text=body),
        ),
    )

    assert [chunk.content for chunk in provider.stream(PROMPT)] == [
        "Hello",
        " world\nline 2",
    ]


def test_openai_compatible_errors_are_clear_and_never_leak_the_key() -> None:
    provider = OpenAICompatibleChatProvider(
        base_url="https://api.example.test/v1",
        model="gpt-5",
        api_key="sk-secret-value",
        client=_client(
            lambda request: httpx.Response(401, json={"error": "invalid api key"}),
        ),
    )

    with pytest.raises(
        ChatProviderError,
        match="HTTP 401",
    ) as error:
        provider.generate(PROMPT)

    assert "sk-secret-value" not in str(error.value)


def test_openai_compatible_unreachable_server_is_a_clear_error() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    provider = OpenAICompatibleChatProvider(
        base_url="http://localhost:1234/v1",
        model="local-model",
        api_key=None,
        client=_client(handler),
    )

    with pytest.raises(
        ChatProviderError,
        match="Could not reach",
    ):
        provider.generate(PROMPT)


def test_api_key_is_sent_as_a_bearer_token() -> None:
    seen: dict = {}

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization")

        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )

    transport = httpx.MockTransport(handler)

    provider = OpenAICompatibleChatProvider(
        base_url="https://api.example.test/v1",
        model="gpt-5",
        api_key="sk-test",
    )

    # Swap in the mock transport while keeping the provider's own headers.
    provider._client._transport = transport  # noqa: SLF001

    provider.generate(PROMPT)

    assert seen["authorization"] == "Bearer sk-test"


# --- OpenAI-compatible embeddings ----------------------------------------


def test_openai_compatible_embeddings_keep_input_order() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert json.loads(request.content)["input"] == ["a", "b"]

        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [0.0, 1.0]},
                    {"index": 0, "embedding": [1.0, 0.0]},
                ],
            },
        )

    provider = OpenAICompatibleEmbeddingProvider(
        base_url="https://api.example.test/v1",
        model="text-embedding-3-small",
        api_key="sk-test",
        client=_client(handler),
    )

    vectors = provider.embed(
        [
            "a",
            "b",
        ],
    )

    assert [vector.values for vector in vectors] == [
        [1.0, 0.0],
        [0.0, 1.0],
    ]


def test_embedding_identity_includes_endpoint_and_model() -> None:
    """The same model name on another server may produce other vectors."""

    first = OpenAICompatibleEmbeddingProvider(
        base_url="https://api.openai.com/v1",
        model="text-embedding-3-small",
        api_key=None,
    )

    second = OpenAICompatibleEmbeddingProvider(
        base_url="http://localhost:1234/v1",
        model="text-embedding-3-small",
        api_key=None,
    )

    assert first.identity != second.identity

    assert "text-embedding-3-small" in first.identity


def test_embedding_error_status_is_an_embedding_error() -> None:
    provider = OpenAICompatibleEmbeddingProvider(
        base_url="https://api.example.test/v1",
        model="m",
        api_key=None,
        client=_client(
            lambda request: httpx.Response(500, text="boom"),
        ),
    )

    with pytest.raises(
        EmbeddingError,
        match="HTTP 500",
    ):
        provider.embed(
            [
                "x",
            ],
        )


# --- Anthropic -----------------------------------------------------------


class _FakeStream:
    def __init__(
        self,
        texts: list[str],
        final: Any,
    ) -> None:
        self.text_stream = iter(
            texts,
        )

        self._final = final

    def __enter__(
        self,
    ) -> "_FakeStream":
        return self

    def __exit__(
        self,
        *args: object,
    ) -> None:
        return None

    def get_final_message(
        self,
    ) -> Any:
        return self._final


class _FakeMessages:
    def __init__(
        self,
        message: Any,
        stream_texts: list[str] | None = None,
    ) -> None:
        self.message = message

        self.stream_texts = stream_texts or []

        self.requests: list[dict] = []

    def create(
        self,
        **request: Any,
    ) -> Any:
        self.requests.append(
            request,
        )

        return self.message

    def stream(
        self,
        **request: Any,
    ) -> _FakeStream:
        self.requests.append(
            request,
        )

        return _FakeStream(
            self.stream_texts,
            self.message,
        )


def _message(
    *blocks: Any,
    stop_reason: str = "end_turn",
    stop_details: Any = None,
) -> Any:
    return SimpleNamespace(
        content=list(
            blocks,
        ),
        stop_reason=stop_reason,
        stop_details=stop_details,
    )


def _text(
    text: str,
) -> Any:
    return SimpleNamespace(
        type="text",
        text=text,
    )


def _anthropic(
    messages: _FakeMessages,
) -> AnthropicChatProvider:
    return AnthropicChatProvider(
        model="claude-opus-5-5",
        api_key="unused",
        client=SimpleNamespace(
            messages=messages,
        ),
    )


def test_anthropic_moves_system_messages_to_the_system_field() -> None:
    messages = _FakeMessages(
        _message(
            SimpleNamespace(type="thinking", thinking=""),
            _text("Edits are applied in ChangeApplier."),
        ),
    )

    response = _anthropic(messages).generate(
        PROMPT,
    )

    # Thinking blocks are not part of the answer.
    assert response.content == "Edits are applied in ChangeApplier."

    request = messages.requests[0]

    assert request["model"] == "claude-opus-5-5"

    assert request["system"] == "Answer from the repository context."

    assert request["messages"] == [
        {
            "role": "user",
            "content": "Where are edits applied?",
        },
    ]

    assert request["max_tokens"] > 0


def test_anthropic_stream_yields_text_fragments() -> None:
    messages = _FakeMessages(
        _message(
            _text("Hello world"),
        ),
        stream_texts=[
            "Hello",
            "",
            " world",
        ],
    )

    assert [chunk.content for chunk in _anthropic(messages).stream(PROMPT)] == [
        "Hello",
        " world",
    ]


def test_anthropic_refusal_is_an_error_without_switching_models() -> None:
    messages = _FakeMessages(
        _message(
            stop_reason="refusal",
            stop_details=SimpleNamespace(category="cyber"),
        ),
    )

    with pytest.raises(
        ChatProviderError,
        match="declined to answer \\(category: cyber\\)",
    ):
        _anthropic(messages).generate(
            PROMPT,
        )

    # Exactly one request: no automatic retry on another model.
    assert len(messages.requests) == 1

    assert "fallbacks" not in messages.requests[0]


# --- Factory -------------------------------------------------------------


def _configuration() -> ModelConfiguration:
    return ModelConfiguration.model_validate(
        {
            "providers": {
                "local": {"type": "ollama", "base_url": "http://gpu-box:11434"},
                "openai": {
                    "type": "openai_compatible",
                    "base_url": "https://api.openai.com/v1",
                    "api_key_env": "RIP_TEST_OPENAI_API_KEY",
                },
                "claude": {
                    "type": "anthropic",
                    "api_key_env": "RIP_TEST_ANTHROPIC_API_KEY",
                },
            },
            "primary": {"provider": "claude", "model": "claude-opus-5-5"},
            "capabilities": {
                "chat": {"provider": "local", "model": "qwen3:8b"},
            },
            "embedding": {"provider": "openai", "model": "text-embedding-3-small"},
        },
    )


def test_factory_builds_the_adapter_for_the_resolved_model() -> None:
    configuration = _configuration()

    resolver = ModelResolver(
        configuration,
    )

    chat = build_chat_provider(
        configuration=configuration,
        effective=resolver.for_task(
            Task.CHAT_ANSWER,
        ),
        ollama_settings=OllamaSettings(),
    )

    assert isinstance(
        chat,
        OllamaChatProvider,
    )

    assert chat._model == "qwen3:8b"  # noqa: SLF001


@pytest.mark.parametrize(
    "think",
    [
        False,
        True,
        None,
    ],
)
def test_think_setting_reaches_ollama(
    think: bool | None,
) -> None:
    """None is dropped by the client (exclude_none), so unset sends nothing."""

    configuration = ModelConfiguration.model_validate(
        {
            "providers": {"local": {"type": "ollama"}},
            "primary": {"provider": "local", "model": "qwen3:8b"},
            "tasks": {
                "chat.answer": {"provider": "local", "model": "qwen3:8b", "think": think},
            },
            "embedding": {"provider": "local", "model": "nomic-embed-text"},
        },
    )

    effective = ModelResolver(
        configuration,
    ).for_task(
        Task.CHAT_ANSWER,
    )

    assert effective.think is think

    chat = build_chat_provider(
        configuration=configuration,
        effective=effective,
        ollama_settings=OllamaSettings(),
    )

    client = MagicMock()

    client.chat.return_value = iter([_ollama_part("answer", done=True)])

    chat._client = client  # noqa: SLF001

    chat.generate(
        PROMPT,
    )

    assert client.chat.call_args.kwargs["think"] is think


def test_missing_api_key_names_the_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "RIP_TEST_OPENAI_API_KEY",
        raising=False,
    )

    configuration = _configuration()

    with pytest.raises(
        ModelConfigurationError,
        match="RIP_TEST_OPENAI_API_KEY, which is not set",
    ):
        build_embedding_provider(
            configuration=configuration,
            effective=ModelResolver(configuration).for_embedding(),
            ollama_settings=OllamaSettings(),
        )


def test_key_from_the_environment_reaches_the_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "RIP_TEST_OPENAI_API_KEY",
        "sk-from-env",
    )

    configuration = _configuration()

    provider = build_embedding_provider(
        configuration=configuration,
        effective=ModelResolver(configuration).for_embedding(),
        ollama_settings=OllamaSettings(),
    )

    assert isinstance(
        provider,
        OpenAICompatibleEmbeddingProvider,
    )

    assert provider._client.headers["authorization"] == "Bearer sk-from-env"  # noqa: SLF001


def test_ollama_adapters_keep_their_identity_format() -> None:
    """Indexes stamped before this feature stay compatible."""

    provider = OllamaEmbeddingProvider(
        OllamaSettings(),
        model="nomic-embed-text",
        base_url="http://gpu-box:11434",
    )

    assert provider.identity == "ollama:nomic-embed-text"


def test_lazy_embedding_provider_builds_only_when_used() -> None:
    built: list[bool] = []

    def build() -> Any:
        built.append(True)

        raise ModelConfigurationError(
            "missing key",
        )

    lazy = LazyEmbeddingProvider(
        build,
    )

    # Holding a reference costs nothing and cannot fail.
    assert built == []

    with pytest.raises(
        ModelConfigurationError,
    ):
        lazy.embed(
            [
                "x",
            ],
        )


# --- Ollama unreachable --------------------------------------------------


def _ollama_part(
    content: str,
    done: bool = False,
    done_reason: str | None = None,
) -> SimpleNamespace:
    """One streamed piece of an Ollama chat reply."""

    return SimpleNamespace(
        message=SimpleNamespace(content=content),
        done=done,
        done_reason=done_reason,
    )


def _ollama_chat(
    *parts: SimpleNamespace,
) -> tuple[OllamaChatProvider, MagicMock]:
    provider = OllamaChatProvider(OllamaSettings())

    client = MagicMock()

    client.chat.return_value = iter(parts)

    provider._client = client  # noqa: SLF001

    return provider, client


def test_ollama_chat_caps_the_answer_length() -> None:
    """Regression: a looping model wrote one answer for over an hour."""

    provider, client = _ollama_chat(_ollama_part("answer", done=True, done_reason="stop"))

    provider.generate(PROMPT)

    assert client.chat.call_args.kwargs["options"] == {
        "num_predict": MAX_OUTPUT_TOKENS,
    }


def test_ollama_generate_joins_the_streamed_answer() -> None:
    provider, client = _ollama_chat(
        _ollama_part("Edits are "),
        _ollama_part("applied by the editing service.", done=True, done_reason="stop"),
    )

    response = provider.generate(PROMPT)

    assert response.content == "Edits are applied by the editing service."
    assert client.chat.call_args.kwargs["stream"] is True


def test_ollama_says_when_the_cap_cut_an_answer_short() -> None:
    provider, _ = _ollama_chat(
        _ollama_part("It loops and loops"),
        _ollama_part("", done=True, done_reason="length"),
    )

    content = provider.generate(PROMPT).content

    assert content == "It loops and loops" + TRUNCATION_NOTE
    assert "4,096-token limit" in TRUNCATION_NOTE


def test_ollama_finished_answer_gets_no_note() -> None:
    provider, _ = _ollama_chat(_ollama_part("Done.", done=True, done_reason="stop"))

    assert [c.content for c in provider.stream(PROMPT)] == ["Done."]


def test_ollama_empty_answer_is_an_error() -> None:
    provider, _ = _ollama_chat(_ollama_part("", done=True, done_reason="stop"))

    with pytest.raises(ChatProviderError, match="no content"):
        provider.generate(PROMPT)


def test_ollama_silence_reports_a_timeout_not_a_missing_server() -> None:
    provider, client = _ollama_chat()

    client.chat.side_effect = httpx.ReadTimeout("timed out")

    with pytest.raises(ChatProviderError, match="sent nothing for 120 seconds"):
        provider.generate(PROMPT)


def test_ollama_timeout_comes_from_the_provider_configuration() -> None:
    """Regression: the configured timeout never reached the Ollama client."""

    configuration = ModelConfiguration.model_validate(
        {
            "providers": {"local": {"type": "ollama", "timeout_seconds": 45}},
            "primary": {"provider": "local", "model": "qwen3:8b"},
            "embedding": {"provider": "local", "model": "nomic-embed-text"},
        },
    )

    chat = build_chat_provider(
        configuration=configuration,
        effective=ModelResolver(configuration).for_task(Task.CHAT_ANSWER),
        ollama_settings=OllamaSettings(),
    )

    assert isinstance(chat, OllamaChatProvider)
    assert chat._client._client.timeout.read == 45  # noqa: SLF001


UNREACHABLE = OllamaSettings(
    base_url="http://127.0.0.1:9",
)


def test_ollama_chat_reports_an_unreachable_server_clearly() -> None:
    """Regression: the client's ConnectionError used to escape as HTTP 500."""

    provider = OllamaChatProvider(
        UNREACHABLE,
    )

    for call in (
        lambda: provider.generate(PROMPT),
        lambda: list(provider.stream(PROMPT)),
    ):
        with pytest.raises(
            ChatProviderError,
            match="Could not reach Ollama at http://127.0.0.1:9",
        ):
            call()


def test_ollama_embeddings_report_an_unreachable_server_clearly() -> None:
    with pytest.raises(
        EmbeddingError,
        match="Could not reach Ollama",
    ):
        OllamaEmbeddingProvider(
            UNREACHABLE,
        ).embed(
            [
                "x",
            ],
        )


def test_lazy_embedding_provider_rebuilds_when_the_config_changes() -> None:
    """Long-lived holders (an MCP server's indexer) never keep a stale model."""

    version = {"value": 1}

    builds: list[int] = []

    class Recording(OllamaEmbeddingProvider):
        pass

    def build() -> Any:
        builds.append(version["value"])

        return OllamaEmbeddingProvider(
            OllamaSettings(),
            model=f"model-v{version['value']}",
        )

    lazy = LazyEmbeddingProvider(
        build,
        version=lambda: version["value"],
    )

    assert lazy.identity == "ollama:model-v1"

    assert lazy.identity == "ollama:model-v1"

    version["value"] = 2

    assert lazy.identity == "ollama:model-v2"

    assert builds == [1, 2]
