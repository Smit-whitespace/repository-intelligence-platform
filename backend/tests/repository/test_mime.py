"""Tests for MIME type detection."""

from pathlib import Path

import pytest

from app.repository.mime import detect_mime_type


class TestKnownExtensions:
    """Every text extension should return a non-None MIME type."""

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("main.py", "text/x-python"),
            ("stubs.pyi", "text/x-python"),
            ("app.js", "text/javascript"),
            ("component.jsx", "text/javascript"),
            ("module.mjs", "text/javascript"),
            ("config.cjs", "text/javascript"),
            ("server.ts", "text/typescript"),
            ("component.tsx", "text/typescript"),
            ("Main.java", "text/x-java"),
            ("App.kt", "text/x-kotlin"),
            ("main.go", "text/x-go"),
            ("lib.rs", "text/x-rust"),
            ("readme.md", "text/markdown"),
            ("data.json", "application/json"),
            ("config.yaml", "text/yaml"),
            ("config.yml", "text/yaml"),
            ("page.html", "text/html"),
            ("style.css", "text/css"),
            ("style.scss", "text/x-scss"),
            ("style.sass", "text/x-sass"),
            ("script.sh", "application/x-sh"),
            ("script.ps1", "text/x-powershell"),
            ("main.c", "text/x-c"),
            ("main.cpp", "text/x-c++"),
            ("main.cc", "text/x-c++"),
            ("main.cxx", "text/x-c++"),
            ("header.h", "text/x-c"),
            ("header.hpp", "text/x-c++"),
            ("Program.cs", "text/x-csharp"),
            ("index.php", "text/x-php"),
            ("app.rb", "text/x-ruby"),
            ("main.swift", "text/x-swift"),
            ("App.scala", "text/x-scala"),
            ("query.sql", "text/x-sql"),
            ("data.xml", "text/xml"),
            ("config.toml", "text/toml"),
            ("settings.ini", "text/plain"),
            ("setup.cfg", "text/plain"),
            ("notes.txt", "text/plain"),
        ],
    )
    def test_known_extension_returns_mime(
        self,
        filename: str,
        expected: str,
    ) -> None:
        path = Path(filename)
        result = detect_mime_type(path)
        assert result == expected, f"{filename} should map to {expected!r}, got {result!r}"

    def test_dockerfile_by_name(self) -> None:
        path = Path("dockerfile")
        result = detect_mime_type(path)
        assert result == "text/x-dockerfile"

    def test_dockerfile_uppercase(self) -> None:
        path = Path("Dockerfile")
        result = detect_mime_type(path)
        assert result == "text/x-dockerfile"


class TestWindowsTsOverride:
    """.ts must never resolve to video/vnd.dlna.mpeg-tts on Windows."""

    def test_typescript_ts(self) -> None:
        path = Path("server.ts")
        result = detect_mime_type(path)
        assert result == "text/typescript"

    def test_typescript_tsx(self) -> None:
        path = Path("component.tsx")
        result = detect_mime_type(path)
        assert result == "text/typescript"


class TestFallbackBehaviour:
    """Extensions not in the project map should fall back to mimetypes."""

    def test_fallback_to_mimetypes(self) -> None:
        path = Path("image.png")
        result = detect_mime_type(path)
        assert result == "image/png"

    def test_fallback_with_known_mimetype(self) -> None:
        path = Path("document.pdf")
        result = detect_mime_type(path)
        assert result == "application/pdf"


class TestUnknownExtension:
    """Extensions unknown to both maps should return None."""

    def test_unknown_extension_returns_none(self) -> None:
        path = Path("data.xyz")
        result = detect_mime_type(path)
        assert result is None

    def test_no_extension_returns_none(self) -> None:
        path = Path("Makefile")
        result = detect_mime_type(path)
        assert result is None


class TestAllTextExtensionsCovered:
    """Every extension in _TEXT_EXTENSIONS must have a project MIME mapping.

    This ensures that adding a new extension to filetypes.py is a prompt
    to add a MIME mapping here.
    """

    def test_all_text_extensions_have_mime(
        self,
    ) -> None:
        from app.repository.filetypes import _TEXT_EXTENSIONS
        from app.repository.mime import _EXTENSION_MIME_MAP

        unmapped = _TEXT_EXTENSIONS - set(_EXTENSION_MIME_MAP)
        assert not unmapped, (
            f"Extensions in filetypes.py missing from _EXTENSION_MIME_MAP: {unmapped}"
        )
