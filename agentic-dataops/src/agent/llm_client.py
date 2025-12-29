"""Provider-agnostic LLM client with OpenAI and Google Vertex (Gemini) support.

The client auto-selects a backend by environment variables. Use `LLMClient(
backend='vertex')` or set `LLM_BACKEND=vertex` and provide `GOOGLE_APPLICATION_CREDENTIALS`,
`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` (optional), and `VERTEX_MODEL`.

Fallback is OpenAI when `OPENAI_API_KEY` is available or `LLM_BACKEND=openai`.
"""
from __future__ import annotations

import os
from typing import Any, Optional

try:
    import openai
except Exception:  # pragma: no cover - optional runtime dependency
    openai = None

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
except ImportError:  # pragma: no cover - optional runtime dependency
    vertexai = None
    GenerativeModel = None


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        backend: Optional[str] = None,
    ) -> None:
        # backend selection: explicit > env LLM_BACKEND > auto-detect
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        env_backend = os.environ.get("LLM_BACKEND")
        autodetect = "vertex" if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") else "openai"
        self.backend = (backend or env_backend or autodetect).lower()

        # model selection
        self.model = model or os.environ.get("VERTEX_MODEL") or os.environ.get("OPENAI_MODEL")

        if self.backend == "openai":
            if openai is None:
                raise RuntimeError("openai package not installed. Install via `pip install openai` or set LLM_BACKEND=vertex")
            if not self.api_key:
                raise RuntimeError("OPENAI_API_KEY not set. Export your key in OPENAI_API_KEY")
            openai.api_key = self.api_key

        elif self.backend == "vertex":
            if vertexai is None:
                raise RuntimeError("google-cloud-aiplatform is not installed. Install via `pip install google-cloud-aiplatform>=1.38`")
            # basic required envs
            self.project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")
            self.location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
            if not self.project:
                raise RuntimeError("Set GOOGLE_CLOUD_PROJECT (or PROJECT_ID) to your GCP project")
            if not self.model:
                raise RuntimeError("Set VERTEX_MODEL to the model id (e.g. 'gemini-1.5-pro')")
            
            # Initialize Vertex AI
            vertexai.init(project=self.project, location=self.location)
            self.client = GenerativeModel(self.model)

        else:
            raise ValueError("Unsupported LLM backend: %s" % self.backend)

    def generate(self, prompt: str, max_tokens: int = 4096, temperature: float = 0.0) -> str:
        """Generate text for `prompt` using the selected backend.

        Returns the model's text. Errors are raised with actionable guidance.
        """
        if self.backend == "openai":
            resp = openai.ChatCompletion.create(
                model=self.model or "gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            choices = resp.get("choices") or []
            if not choices:
                return ""
            msg = choices[0].get("message") or {}
            return msg.get("content", "")

        # Vertex / Gemini path
        try:
            response = self.client.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Vertex AI generation failed: {e}") from e


__all__ = ["LLMClient"]
