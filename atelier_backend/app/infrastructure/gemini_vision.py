from __future__ import annotations

import base64
import unicodedata
from collections.abc import Sequence

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.exceptions import UnprocessableError
from app.core.observability import tracer
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
                    "ok": {"type": "boolean"},
                },
                "required": ["n", "title", "detail", "rule", "ok"],
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
    ok: bool = False


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
        with tracer.observation(
            "score-visual",
            as_type="generation",
            model=self.model,
            input={
                "image_name": image_name,
                "brand": brand.name,
                "mime": mime,
                "bytes": len(image),
                "chunk_headings": [chunk.heading for chunk in context],
            },
            metadata={"provider": "gemini", "image_omitted": True},
        ) as generation:
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
                                    "Eres auditor visual de una content suite. "
                                    "ATELIER es la plataforma, NUNCA la marca a contrastar. "
                                    "La única marca válida es el nombre del manual que te pasan. "
                                    "Lees el texto visible. Español. JSON único."
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
            payload = response.json()
            try:
                text = payload["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError) as exc:
                raise UnprocessableError(
                    "Gemini devolvió una respuesta vacía.",
                    code="vision_error",
                ) from exc
            parsed = parse_json_object(text)
            try:
                draft = AuditPayload.model_validate(parsed)
            except ValidationError as exc:
                raise UnprocessableError(
                    "Gemini no devolvió un dictamen usable.",
                    code="vision_schema",
                ) from exc
            findings = tuple(
                _correct_name_finding(
                    Finding(
                        n=index,
                        title=item.title.strip(),
                        detail=item.detail.strip(),
                        rule=item.rule.strip(),
                        ok=item.ok,
                    ),
                    brand,
                )
                for index, item in enumerate(draft.findings, start=1)
            )
            passed = all(item.ok for item in findings) if findings else False
            if not findings:
                findings = (
                    Finding(
                        n=1,
                        title="Sin contraste usable",
                        detail=f"El modelo no desglosó reglas contra {brand.name}.",
                        rule="Regla 01 · DNA",
                        ok=False,
                    ),
                )
                passed = False
            update: dict = {
                "output": {
                    "passed": passed,
                    "findings": [item.title for item in findings],
                }
            }
            usage = _gemini_usage(payload)
            if usage:
                update["usage_details"] = usage
            generation.update(**update)
            return AuditDraft(passed=passed, findings=findings, model=self.model)


def _gemini_usage(payload: object) -> dict[str, int]:
    if not isinstance(payload, dict):
        return {}
    usage = payload.get("usageMetadata")
    if not isinstance(usage, dict):
        return {}
    details: dict[str, int] = {}
    prompt = usage.get("promptTokenCount")
    completion = usage.get("candidatesTokenCount")
    if isinstance(prompt, int):
        details["input_tokens"] = prompt
    if isinstance(completion, int):
        details["output_tokens"] = completion
    return details


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
    forbidden = ", ".join(brand.forbidden) or "promesas médicas o absolutas"
    return (
        f"Audita la imagen «{image_name}» contra el manual de «{brand.name}».\n"
        f"Marca activa (la única que importa): {brand.name}\n"
        "ATELIER es el nombre de la herramienta. No lo uses en el dictamen.\n"
        f"Producto: {brand.product}. Tono: {brand.tone}. Audiencia: {brand.audience}.\n"
        f"Paleta: {', '.join(brand.colors)}.\n"
        f"Prohibido en el copy visible: {forbidden}.\n"
        f"Voz sí: {' / '.join(brand.voice_do)}\n"
        f"Voz no: {' / '.join(brand.voice_dont)}\n"
        f"Manual RAG:\n{manual}\n"
        "Devuelve SIEMPRE 4 findings, en este orden, cada uno con ok true/false:\n"
        "1) Nombre de marca: ok=true si el lockup, logo o título principal es "
        f"«{brand.name}» (mayúsculas, acento u ornamento no invalidan). "
        "ATELIER no es la marca. Otras marcas de props (vasos, cerveza, platos) "
        "no fallan este check si el nombre del manual está presente. "
        f"ok=false solo si el héroe visual nombra OTRA marca en lugar de {brand.name}.\n"
        "2) Paleta (colores dominantes vs hex del manual).\n"
        "3) Claims y voz (promesas médicas, palabras prohibidas, tono).\n"
        "4) Área de respeto del isotipo / jerarquía tipográfica.\n"
        "passed=true SOLO si los 4 tienen ok=true. "
        "rule como 'Regla 01 · Nombre'."
    )


def _fold(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text)
    return "".join(char for char in stripped if not unicodedata.combining(char)).casefold()


def _correct_name_finding(finding: Finding, brand: Brand) -> Finding:
    if "nombre" not in finding.title.casefold() and "nombre" not in finding.rule.casefold():
        return finding
    folded = _fold(finding.detail)
    brand_fold = _fold(brand.name)
    confused = "atelier" in folded and brand_fold != "atelier"
    named = brand_fold in folded
    if confused and named:
        return Finding(
            n=finding.n,
            title=finding.title,
            detail=f"El lockup visible corresponde a {brand.name}. ATELIER es la plataforma, no la marca.",
            rule=finding.rule,
            ok=True,
        )
    if confused:
        rewritten = (
            finding.detail.replace("ATELIER", brand.name)
            .replace("Atelier", brand.name)
            .replace("atelier", brand.name)
        )
        return Finding(
            n=finding.n,
            title=finding.title,
            detail=rewritten,
            rule=finding.rule,
            ok=finding.ok,
        )
    if named and not finding.ok:
        return Finding(
            n=finding.n,
            title=finding.title,
            detail=finding.detail,
            rule=finding.rule,
            ok=True,
        )
    return finding


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
