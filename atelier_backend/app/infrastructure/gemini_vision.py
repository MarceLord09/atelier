from __future__ import annotations

import base64
from collections.abc import Sequence

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.exceptions import UnprocessableError
from app.domain.entities import AuditDraft, Brand, Chunk, Finding
from app.infrastructure.groq_llm import parse_json_object

MAX_IMAGE_BYTES = 8 * 1024 * 1024
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "passed": {"type": "boolean"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "n": {"type": "integer"},
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "rule": {"type": "string"},
                },
                "required": ["n", "title", "detail", "rule"],
            },
        },
    },
    "required": ["passed", "findings"],
}


class FindingDraft(BaseModel):
    n: int
    title: str = Field(min_length=3, max_length=80)
    detail: str = Field(min_length=8, max_length=500)
    rule: str = Field(min_length=3, max_length=80)


class AuditPayload(BaseModel):
    passed: bool
    findings: list[FindingDraft] = Field(default_factory=list, max_length=5)


class GeminiVisionAuditor:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.model = model
        self._api_key = api_key
        self._http = httpx.AsyncClient(timeout=60.0)

    async def audit(
        self,
        *,
        brand: Brand,
        image_name: str,
        image: bytes,
        context: Sequence[Chunk] = (),
    ) -> AuditDraft:
        if len(image) > MAX_IMAGE_BYTES:
            raise UnprocessableError("La imagen supera 8 MB.")
        mime = sniff_mime(image)
        encoded = base64.standard_b64encode(image).decode("ascii")
        response = await self._http.post(
            GEMINI_URL.format(model=self.model),
            headers={
                "x-goog-api-key": self._api_key,
                "Content-Type": "application/json",
            },
            json={
                "systemInstruction": {
                    "parts": [
                        {
                            "text": (
                                "Eres auditor visual de marca de ATELIER. "
                                "Contrasta la pieza contra el manual. Español. "
                                "No inventes textos que no se vean. JSON único."
                            )
                        }
                    ]
                },
                "contents": [
                    {
                        "parts": [
                            {"inline_data": {"mime_type": mime, "data": encoded}},
                            {"text": _audit_prompt(brand, image_name, context)},
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                    "responseSchema": RESPONSE_SCHEMA,
                },
            },
        )
        if response.status_code >= 400:
            raise _gemini_error(response)
        try:
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise UnprocessableError("Gemini devolvió una respuesta vacía.", code="vision_error") from exc
        payload = parse_json_object(text)
        try:
            draft = AuditPayload.model_validate(payload)
        except ValidationError as exc:
            raise UnprocessableError("Gemini no devolvió un dictamen usable.", code="vision_schema") from exc
        findings = tuple(
            Finding(n=index, title=item.title.strip(), detail=item.detail.strip(), rule=item.rule.strip())
            for index, item in enumerate(draft.findings, start=1)
        )
        if not draft.passed and not findings:
            findings = (
                Finding(
                    n=1,
                    title="Fuera de manual",
                    detail=f"La pieza {image_name} no cumple el contraste contra {brand.name}.",
                    rule="Regla 01 · DNA",
                ),
            )
        return AuditDraft(passed=draft.passed, findings=findings, model=self.model)


def sniff_mime(image: bytes) -> str:
    if image.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(image) >= 12 and image[:4] == b"RIFF" and image[8:12] == b"WEBP":
        return "image/webp"
    raise UnprocessableError("Solo se aceptan JPG, PNG o WEBP.")


def _audit_prompt(brand: Brand, image_name: str, context: Sequence[Chunk]) -> str:
    manual = "\n".join(f"[{chunk.heading}] {chunk.content}" for chunk in context) or brand.manifesto
    return (
        f"Audita la imagen «{image_name}» contra el manual de {brand.name}.\n"
        f"Producto: {brand.product}. Tono: {brand.tone}. Audiencia: {brand.audience}.\n"
        f"Paleta: {', '.join(brand.colors)}.\n"
        f"Prohibido: {', '.join(brand.forbidden) or 'promesas médicas o absolutas'}.\n"
        f"Voz sí: {' / '.join(brand.voice_do)}\n"
        f"Voz no: {' / '.join(brand.voice_dont)}\n"
        f"Manual RAG:\n{manual}\n"
        "Evalúa paleta, tipografía/jerarquía, claims y respeto del isotipo. "
        "passed=true solo si la pieza es coherente. "
        "findings: 0 a 4. rule como 'Regla 03 · Paleta'."
    )


def _gemini_error(response: httpx.Response) -> UnprocessableError:
    status = ""
    try:
        error = response.json().get("error") or {}
        if isinstance(error, dict):
            status = str(error.get("status") or "")
    except Exception:
        status = ""
    if response.status_code == 400:
        return UnprocessableError("Gemini no pudo leer esa imagen.", code="vision_bad_image")
    if response.status_code == 403 or status == "PERMISSION_DENIED":
        return UnprocessableError(
            "Google denegó generateContent en este proyecto. Crea otra API key en un proyecto nuevo de AI Studio.",
            code="vision_auth",
        )
    if response.status_code == 429 or status == "RESOURCE_EXHAUSTED":
        return UnprocessableError(
            "Gemini alcanzó el límite de uso. Espera un momento e intenta de nuevo.",
            code="vision_rate",
        )
    return UnprocessableError("Gemini no pudo auditar la imagen.", code="vision_error")
