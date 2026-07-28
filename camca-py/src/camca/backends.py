"""VLM backend abstractions for Claude, Gemini, and Ollama.

Each backend implements the same `VLMBackend` interface so the pipeline
treats them interchangeably. Backend dependencies are optional — install
only the SDK for the providers you use:

    pip install camca[claude]    # for Claude
    pip install camca[gemini]    # for Gemini
    pip install camca[all]       # both
    # Ollama backend uses requests (always installed)
"""
from __future__ import annotations

import base64
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BackendError(Exception):
    """Raised when a backend call fails."""


# ---------- Helpers ----------

def _encode_image_b64(path: Path) -> tuple[str, str]:
    """Return (base64_string, media_type) for an image file."""
    suffix = Path(path).suffix.lower()
    media_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
    }.get(suffix, "image/jpeg")
    with open(path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("ascii")
    return b64, media_type


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def _try_parse_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return json.loads(_strip_json_fence(text))
        except json.JSONDecodeError as e:
            raise BackendError(f"Failed to parse JSON response: {e}\n---\n{text[:500]}")


# ---------- Base ----------

class VLMBackend(ABC):
    """Abstract VLM backend."""

    name: str = "abstract"

    @abstractmethod
    def analyze_frames(
        self,
        prompt: str,
        frames: list[Path],
        expect_json: bool = True,
        max_tokens: int = 4096,
        response_schema: Any = None,
    ) -> dict[str, Any] | str:
        """Analyze frames + prompt.

        Args:
            response_schema: Pydantic model class for schema-enforced output.
                            Used by Gemini's response_schema; ignored by others.
        """
        ...

    @abstractmethod
    def model_id(self) -> str:
        ...

    def cost_estimate_per_call(self, n_frames: int = 5) -> str:
        return "varies"

    def analyze_video(
        self,
        prompt: str,
        video_path: Path,
        expect_json: bool = True,
        max_tokens: int = 4096,
        response_schema: Any = None,
    ) -> dict[str, Any] | str:
        """Optional: analyze a whole video file (Gemini Native Video API).

        Backends without native video support fall back to extracting frames
        externally (handled by the pipeline).
        """
        raise NotImplementedError(
            f"{self.name} backend does not support native video; use analyze_frames."
        )


# ---------- Claude ----------

class ClaudeBackend(VLMBackend):
    """Anthropic Claude API backend."""

    name = "claude"
    DEFAULT_MODELS = {
        "opus": "claude-opus-4-7",
        "sonnet": "claude-sonnet-4-6",
        "haiku": "claude-haiku-4-5-20251001",
    }

    def __init__(self, model: str = "sonnet", api_key: str | None = None):
        try:
            import anthropic
        except ImportError:
            raise BackendError(
                "anthropic SDK not installed. Install with: pip install camca[claude]"
            )
        self._anthropic = anthropic
        self._model = self.DEFAULT_MODELS.get(model, model)
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise BackendError("ANTHROPIC_API_KEY not set; pass api_key= or set env var")
        self._client = anthropic.Anthropic(api_key=key)

    def model_id(self) -> str:
        return self._model

    def analyze_frames(self, prompt, frames, expect_json=True, max_tokens=4096, response_schema=None):
        content_blocks: list[dict[str, Any]] = []
        for f in frames:
            b64, media_type = _encode_image_b64(f)
            content_blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": b64},
            })
        content_blocks.append({"type": "text", "text": prompt})

        kwargs = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": content_blocks}],
        }
        # Schema enforcement via Claude tool_use if schema provided
        if response_schema is not None and hasattr(response_schema, "model_json_schema"):
            schema_json = response_schema.model_json_schema()
            kwargs["tools"] = [{
                "name": "emit_evaluation",
                "description": "Emit the structured evaluation result.",
                "input_schema": schema_json,
            }]
            kwargs["tool_choice"] = {"type": "tool", "name": "emit_evaluation"}

        try:
            response = self._client.messages.create(**kwargs)
        except Exception as e:
            raise BackendError(f"Claude API error: {e}") from e

        # If tool_use was forced, extract tool input
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                return block.input  # already a dict
        # Else fallback to text
        text = "".join(b.text for b in response.content if b.type == "text")
        return _try_parse_json(text) if expect_json else text

    def cost_estimate_per_call(self, n_frames: int = 5) -> str:
        if "opus" in self._model:
            return f"~${0.30 + n_frames*0.05:.2f}/call (Opus)"
        return f"~${0.05 + n_frames*0.01:.2f}/call (Sonnet)"


# ---------- Gemini ----------

class GeminiBackend(VLMBackend):
    """Google Gemini API backend."""

    name = "gemini"
    DEFAULT_MODELS = {
        "pro": "gemini-2.5-pro",
        "flash": "gemini-2.5-flash",
        "1.5-pro": "gemini-1.5-pro-latest",
    }

    def __init__(self, model: str = "pro", api_key: str | None = None,
                 use_native_video: bool = False):
        """Args:
            use_native_video: If True, analyze_video uploads the full video file
                              to Gemini (preserves sub-second timing). Default False.
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise BackendError(
                "google-generativeai SDK not installed. Install with: pip install camca[gemini]"
            )
        self._genai = genai
        key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise BackendError("GOOGLE_API_KEY or GEMINI_API_KEY not set")
        genai.configure(api_key=key)
        self._model = self.DEFAULT_MODELS.get(model, model)
        self._client = genai.GenerativeModel(self._model)
        self.use_native_video = use_native_video

    def model_id(self) -> str:
        suffix = "+native-video" if self.use_native_video else ""
        return self._model + suffix

    def _build_gen_config(self, expect_json, max_tokens, response_schema):
        gen_config: dict[str, Any] = {
            "max_output_tokens": max_tokens,
            "temperature": 0.2,
        }
        if expect_json:
            gen_config["response_mime_type"] = "application/json"
        if response_schema is not None:
            gen_config["response_schema"] = response_schema
        return gen_config

    def analyze_frames(self, prompt, frames, expect_json=True, max_tokens=4096, response_schema=None):
        import PIL.Image
        parts: list[Any] = []
        for f in frames:
            try:
                parts.append(PIL.Image.open(f))
            except Exception as e:
                raise BackendError(f"Failed to open image {f}: {e}")
        parts.append(prompt)
        try:
            response = self._client.generate_content(
                parts,
                generation_config=self._build_gen_config(expect_json, max_tokens, response_schema),
            )
        except Exception as e:
            raise BackendError(f"Gemini API error: {e}") from e
        text = response.text if hasattr(response, "text") else str(response)
        return _try_parse_json(text) if expect_json else text

    def analyze_video(self, prompt, video_path, expect_json=True, max_tokens=4096, response_schema=None):
        """Native Video API — upload the entire video to Gemini.

        Bypasses ffmpeg frame extraction; preserves sub-second timing for the VLM.
        """
        import time
        try:
            video_file = self._genai.upload_file(path=str(video_path))
        except Exception as e:
            raise BackendError(f"Gemini upload failed: {e}")

        # Block until processing complete
        for _ in range(60):  # max ~3 min
            video_file = self._genai.get_file(video_file.name)
            if video_file.state.name != "PROCESSING":
                break
            time.sleep(3)

        if video_file.state.name != "ACTIVE":
            raise BackendError(f"Gemini video upload failed: state={video_file.state.name}")

        try:
            response = self._client.generate_content(
                [video_file, prompt],
                generation_config=self._build_gen_config(expect_json, max_tokens, response_schema),
            )
        except Exception as e:
            raise BackendError(f"Gemini native-video API error: {e}") from e

        text = response.text if hasattr(response, "text") else str(response)
        return _try_parse_json(text) if expect_json else text

    def cost_estimate_per_call(self, n_frames: int = 5) -> str:
        if "flash" in self._model:
            return f"~${0.01 + n_frames*0.002:.3f}/call (Flash)"
        return f"~${0.05 + n_frames*0.008:.2f}/call (Pro)"


# ---------- Ollama ----------

class OllamaBackend(VLMBackend):
    """Local Ollama backend. Requires Ollama server with a vision model pulled."""

    name = "ollama"

    def __init__(
        self,
        model: str = "gemma3:12b",
        host: str | None = None,
        timeout: int = 300,
    ):
        import requests
        self._requests = requests
        self._model = model
        self._host = (host or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self._timeout = timeout

        try:
            r = requests.get(f"{self._host}/api/tags", timeout=5)
            r.raise_for_status()
            available = [m.get("name", "") for m in r.json().get("models", [])]
            if model not in available and not any(model in a for a in available):
                print(
                    f"WARNING: Model '{model}' not in Ollama tags: {available[:5]}... "
                    f"Run `ollama pull {model}` if call fails."
                )
        except Exception as e:
            raise BackendError(f"Cannot reach Ollama at {self._host}: {e}")

    def model_id(self) -> str:
        return f"ollama/{self._model}"

    def analyze_frames(self, prompt, frames, expect_json=True, max_tokens=4096, response_schema=None):
        images_b64 = []
        for f in frames:
            with open(f, "rb") as fp:
                images_b64.append(base64.standard_b64encode(fp.read()).decode("ascii"))

        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "images": images_b64,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": max_tokens},
        }
        # Ollama supports JSON format hint; if a Pydantic schema given, embed in prompt
        if response_schema is not None and hasattr(response_schema, "model_json_schema"):
            schema_hint = (
                f"\n\nRESPONSE_SCHEMA (must conform to this JSON Schema):\n"
                f"{response_schema.model_json_schema()}"
            )
            payload["prompt"] = prompt + schema_hint
        if expect_json:
            payload["format"] = "json"

        try:
            r = self._requests.post(
                f"{self._host}/api/generate", json=payload, timeout=self._timeout,
            )
            r.raise_for_status()
        except Exception as e:
            raise BackendError(f"Ollama call failed: {e}")

        text = r.json().get("response", "")
        return _try_parse_json(text) if expect_json else text

    def cost_estimate_per_call(self, n_frames: int = 5) -> str:
        return "free (local) — but requires GPU + ~10-30 sec per call"


# ---------- Factory ----------

def create_backend(spec: str, **kwargs) -> VLMBackend:
    """Create a backend from a 'provider:model' string.

    Examples:
        create_backend("claude:opus")
        create_backend("claude:sonnet")
        create_backend("gemini:pro")
        create_backend("ollama:gemma3:12b")
        create_backend("ollama:llava:13b")
    """
    if ":" not in spec:
        raise ValueError(f"Spec must be 'provider:model' (got '{spec}')")
    provider, _, model = spec.partition(":")
    provider = provider.lower()

    if provider == "claude":
        return ClaudeBackend(model=model, **kwargs)
    elif provider == "gemini":
        return GeminiBackend(model=model, **kwargs)
    elif provider == "ollama":
        return OllamaBackend(model=model, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider} (supported: claude, gemini, ollama)")
