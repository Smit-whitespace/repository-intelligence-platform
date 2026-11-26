"""Held-out search questions: never used to tune ranking.

``BENCHMARKS`` is the tuning set: ranking ideas are tried against it.
These questions were written before any tuning and cover areas the
tuning set does not, so a ranking change counts as an improvement only
if it does not make these worse. Do not edit them to fit a result.

    python -m eval --root <indexed project> --set holdout
"""

from eval.models import RetrievalTestCase

HOLDOUT: list[RetrievalTestCase] = [
    RetrievalTestCase(
        query="Where does the app keep the API token after signing in?",
        expected_file_paths=["frontend/src/stores/authStore.ts"],
        expected_concepts=["token storage", "sign-in"],
    ),
    RetrievalTestCase(
        query="How does the chat page stream an answer from the backend?",
        expected_file_paths=[
            "frontend/src/lib/sse/sseClient.ts",
            "frontend/src/features/chat/ChatPage.tsx",
        ],
        expected_concepts=["streaming", "server-sent events"],
    ),
    RetrievalTestCase(
        query="What does the screen look like when the app is not signed in?",
        expected_file_paths=["frontend/src/components/common/SignIn.tsx"],
        expected_concepts=["sign-in screen"],
    ),
    RetrievalTestCase(
        query="How does the Editing page show a proposal's diff and its apply button?",
        expected_file_paths=["frontend/src/features/editing/EditingPage.tsx"],
        expected_concepts=["diff view", "apply"],
    ),
    RetrievalTestCase(
        query="Which browser origins and Host headers is the API willing to accept?",
        expected_file_paths=["backend/app/main.py"],
        expected_concepts=["CORS", "trusted hosts"],
    ),
    RetrievalTestCase(
        query="How is the thinking of reasoning models turned off for Ollama?",
        expected_file_paths=[
            "backend/app/chat/ollama_provider.py",
            "backend/app/llm/config.py",
        ],
        expected_concepts=["think", "Ollama"],
    ),
    RetrievalTestCase(
        query="What stops two processes from indexing the same project at once?",
        expected_file_paths=["backend/app/indexing/lock.py"],
        expected_concepts=["file lock", "concurrent indexing"],
    ),
    RetrievalTestCase(
        query="How are files restored when an applied edit is rolled back?",
        expected_file_paths=["backend/app/editing/change_applier.py"],
        expected_concepts=["rollback", "restore", "snapshot"],
    ),
    RetrievalTestCase(
        query="Why does text search sometimes say its results were cut off?",
        expected_file_paths=["backend/app/workspace/service.py"],
        expected_concepts=["truncation", "time budget", "long lines"],
    ),
    RetrievalTestCase(
        query="How does a running MCP server notice that the model configuration changed?",
        expected_file_paths=[
            "backend/app/dependencies/providers.py",
            "backend/app/mcp_server/__main__.py",
        ],
        expected_concepts=["configuration refresh", "file stamp"],
    ),
    RetrievalTestCase(
        query="How does the index record which embedding model built it?",
        expected_file_paths=[
            "backend/app/indexing/indexer.py",
            "backend/app/indexing/chroma_store.py",
        ],
        expected_concepts=["embedding stamp", "compatibility"],
    ),
    RetrievalTestCase(
        query="How are Python files split into chunks by function and class?",
        expected_file_paths=["backend/app/repository/python_ast_algorithm.py"],
        expected_concepts=["AST", "decorators", "module statements"],
    ),
    RetrievalTestCase(
        query="What keeps a project's creation date when it is opened again?",
        expected_file_paths=["backend/app/projects/service.py"],
        expected_concepts=["created_at", "reopen"],
    ),
    RetrievalTestCase(
        query="How is an edit rejected if the file changed after it was proposed?",
        expected_file_paths=[
            "backend/app/editing/change_applier.py",
            "backend/app/editing/proposal_service.py",
        ],
        expected_concepts=["conflict", "stale edit"],
    ),
    RetrievalTestCase(
        query="How does the backend print a sign-in link at startup?",
        expected_file_paths=[
            "backend/app/main.py",
            "backend/app/core/security/api_token.py",
        ],
        expected_concepts=["sign-in link", "startup"],
    ),
]

__all__ = [
    "HOLDOUT",
]
