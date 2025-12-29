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
    from google.api_core.client_options import ClientOptions
    from google.cloud.aiplatform.gapic import PredictionServiceClient
except Exception:  # pragma: no cover - optional runtime dependency
    PredictionServiceClient = None
    ClientOptions = None


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
            if PredictionServiceClient is None:
                raise RuntimeError("google-cloud-aiplatform is not installed. Install via `pip install google-cloud-aiplatform`")
            # basic required envs
            self.project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")
            self.location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
            if not self.project:
                raise RuntimeError("Set GOOGLE_CLOUD_PROJECT (or PROJECT_ID) to your GCP project")
            if not self.model:
                raise RuntimeError("Set VERTEX_MODEL to the model id (e.g. 'gemini-1.5') or full resource name")
            # create prediction client; allow overriding endpoint via GOOGLE_CLOUD_LOCATION
            api_endpoint = f"{self.location}-aiplatform.googleapis.com"
            client_options = ClientOptions(api_endpoint=api_endpoint)
            self.client = PredictionServiceClient(client_options=client_options)
            # Endpoint/id used for online prediction (deployed endpoint).
            # Accept either a numeric endpoint id or a full resource name.
            self.endpoint_id = os.environ.get("VERTEX_ENDPOINT") or os.environ.get("VERTEX_ENDPOINT_ID")

        else:
            raise ValueError("Unsupported LLM backend: %s" % self.backend)

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> str:
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
        # Use PredictionServiceClient.predict against model resource
        # Endpoint format: projects/{project}/locations/{location}/models/{model}
        if not getattr(self, "endpoint_id", None):
            raise RuntimeError(
                "VERTEX_ENDPOINT (deployed endpoint id or full resource name) is required for Vertex predict. "
                "Set VERTEX_ENDPOINT to the endpoint id (e.g. '123456789') or "
                "the full resource 'projects/PROJECT/locations/LOCATION/endpoints/ENDPOINT'."
            )
        if "/" in self.endpoint_id:
            endpoint = self.endpoint_id
        else:
            endpoint = f"projects/{self.project}/locations/{self.location}/endpoints/{self.endpoint_id}"


        endpoint = f"projects/{self.project}/locations/{self.location}/models/{self.model}"
        instances = [{"content": prompt}]
        parameters: dict[str, Any] = {"temperature": temperature, "maxOutputTokens": max_tokens}

        resp = self.client.predict(endpoint=endpoint, instances=instances, parameters=parameters)
        preds = list(resp.predictions) if getattr(resp, "predictions", None) is not None else []
        if not preds:
            return ""
        # predictions may be dict-like; attempt safe extraction
        first = preds[0]
        if isinstance(first, dict):
            if "content" in first:
                return first.get("content", "")
            if "candidates" in first and first["candidates"]:
                c = first["candidates"][0]
                return c.get("content") or c.get("text") or ""
        # fallback: return string representation
        return str(first)


__all__ = ["LLMClient"]
