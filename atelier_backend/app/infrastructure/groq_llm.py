from __future__ import annotations

import json
import re
from collections.abc import Sequence

import httpx
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.exceptions import UnprocessableError
from app.domain.entities import Brand, BrandBook, BrandBrief, Chunk, GeneratedCopy
from app.domain.enums import AssetKind
from app.infrastructure.adapters import DEFAULT_COLORS, TemplateBrandComposer, _title_from

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class GroqClient:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.model = model
        self._api_key = api_key
        self._http = httpx.AsyncClient(timeout=45.0)

    async def complete_json(self, *, system: str, user: str) -> dict:
        payload = await self._chat(system=system, user=user, json_mode=True)
        if payload is None:
            payload = await self._chat(system=system, user=user, json_mode=False)
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise UnprocessableError("Groq devolvió una respuesta vacía.", code="llm_error") from exc
        if not content:
            raise UnprocessableError("Groq devolvió una respuesta vacía.", code="llm_error")
        return parse_json_object(content)

    async def _chat(self, *, system: str, user: str, json_mode: bool) -> dict | None:
        body: dict = {
            "model": self.model,
            "temperature": 0.35,
            "reasoning_effort": "none",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        response = await self._http.post(
            GROQ_CHAT_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        if response.status_code == 401:
            raise UnprocessableError(
                "Groq rechazó la API key. Revisa GROQ_API_KEY.",
                code="llm_auth",
            )
        if response.status_code == 429:
            raise UnprocessableError(
                "Groq alcanzó el límite de uso. Espera un momento e intenta de nuevo.",
                code="llm_rate_limit",
            )
        if response.status_code >= 400:
            if json_mode and _is_json_validate_error(response):
                return None
            raise UnprocessableError(
                "Groq no pudo generar el texto. Intenta de nuevo.",
                code="llm_error",
            )
        return response.json()


def _is_json_validate_error(response: httpx.Response) -> bool:
    try:
        payload = response.json()
    except ValueError:
        return False
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        return False
    return error.get("code") == "json_validate_failed"


def _clip(value: object, max_len: int) -> object:
    if isinstance(value, str):
        return value.strip()[:max_len]
    return value


class ChunkDraft(BaseModel):
    heading: str = Field(min_length=2, max_length=80)
    content: str = Field(min_length=8, max_length=800)

    @field_validator("heading", mode="before")
    @classmethod
    def _clip_heading(cls, value: object) -> object:
        return _clip(value, 80)

    @field_validator("content", mode="before")
    @classmethod
    def _clip_content(cls, value: object) -> object:
        return _clip(value, 800)


class BookDraft(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    manifesto: str = Field(min_length=8, max_length=400)
    tone: str = Field(min_length=2, max_length=40)
    colors: list[str] = Field(default_factory=list)
    voice_do: list[str] = Field(default_factory=list)
    voice_dont: list[str] = Field(default_factory=list)
    chunks: list[ChunkDraft] = Field(min_length=3, max_length=8)

    @field_validator("colors", "voice_do", "voice_dont", mode="before")
    @classmethod
    def _ensure_list(cls, value: object) -> object:
        return value if isinstance(value, list) else []

    @field_validator("name", mode="before")
    @classmethod
    def _clip_name(cls, value: object) -> object:
        return _clip(value, 80)

    @field_validator("manifesto", mode="before")
    @classmethod
    def _clip_manifesto(cls, value: object) -> object:
        return _clip(value, 400)

    @field_validator("tone", mode="before")
    @classmethod
    def _clip_tone(cls, value: object) -> object:
        return _clip(value, 40)


class CopyDraft(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=12, max_length=1200)

    @field_validator("title", mode="before")
    @classmethod
    def _clip_title(cls, value: object) -> object:
        return _clip(value, 120)

    @field_validator("body", mode="before")
    @classmethod
    def _clip_body(cls, value: object) -> object:
        return _clip(value, 1200)


class GroqBrandComposer:
    def __init__(self, client: GroqClient) -> None:
        self._client = client
        self._fallback = TemplateBrandComposer()

    async def compose(self, brief: BrandBrief) -> BrandBook:
        payload = await self._client.complete_json(
            system=(
                "Eres director de marca de ATELIER. Devuelves SOLO JSON válido. "
                "Escribes en español, tono cercano, sin promesas médicas ni absolutas."
            ),
            user=_compose_prompt(brief),
        )
        try:
            draft = BookDraft.model_validate(payload)
        except ValidationError as exc:
            raise UnprocessableError(
                "El modelo no devolvió un manual usable. Vuelve a componer.",
                code="llm_schema",
            ) from exc
        forbidden_rules = tuple(f'Evitar la palabra “{word}”.' for word in brief.forbidden)
        voice_dont = tuple(dict.fromkeys([*draft.voice_dont, *forbidden_rules]))[:6]
        colors = _normalize_colors(draft.colors)
        chunks = tuple(Chunk(item.heading.strip(), item.content.strip()) for item in draft.chunks)
        required = {"Esencia", "Voz", "Límites", "Producto"}
        headings = {chunk.heading for chunk in chunks}
        if not required.issubset(headings):
            fallback = await self._fallback.compose(brief)
            merged = {chunk.heading: chunk for chunk in fallback.chunks}
            merged.update({chunk.heading: chunk for chunk in chunks})
            chunks = tuple(merged.values())
        return BrandBook(
            name=draft.name.strip() or brief.name or _title_from(brief.product),
            manifesto=draft.manifesto.strip() or brief.promise,
            tone=draft.tone.strip() or brief.tone,
            colors=colors,
            voice_do=tuple(draft.voice_do[:4])
            or ("Hablar claro, sin tecnicismos.", f"Tono {brief.tone}, directo y cercano."),
            voice_dont=voice_dont
            or ("No promesas médicas ni absolutas.", *forbidden_rules),
            chunks=chunks,
        )


class GroqCopyGenerator:
    def __init__(self, client: GroqClient) -> None:
        self._client = client

    async def generate(
        self,
        *,
        kind: AssetKind,
        brand: Brand,
        context: Sequence[Chunk],
        prompt: str,
    ) -> GeneratedCopy:
        last_error: UnprocessableError | None = None
        for attempt in range(3):
            extra = (
                "\nEl intento anterior violó los límites de voz. Reescribe title y body "
                "desde cero. No copies ni nombres los términos de esa lista."
                if attempt
                else ""
            )
            payload = await self._client.complete_json(
                system=(
                    "Eres copywriter de ATELIER. Usas SOLO el manual recuperado. "
                    "No inventes beneficios. Nunca escribas palabras de la lista de "
                    "límites, ni siquiera para prohibirlas. JSON único."
                ),
                user=_generate_prompt(kind=kind, brand=brand, context=context, prompt=prompt)
                + extra,
            )
            try:
                draft = CopyDraft.model_validate(payload)
            except ValidationError as exc:
                last_error = UnprocessableError(
                    "El modelo no devolvió una pieza usable. Intenta de nuevo.",
                    code="llm_schema",
                )
                last_error.__cause__ = exc
                continue
            banned = _forbidden_hits(f"{draft.title} {draft.body}", brand.forbidden)
            if banned:
                last_error = UnprocessableError(
                    f"El copy usó palabras prohibidas: {', '.join(banned)}. Vuelve a generar.",
                    code="brand_violation",
                )
                continue
            citations = _citations(context, f"{draft.title}\n{draft.body}")
            return GeneratedCopy(
                title=draft.title.strip(),
                body=draft.body.strip(),
                model=self._client.model,
                citations=citations,
            )
        raise last_error or UnprocessableError(
            "El modelo no devolvió una pieza usable. Intenta de nuevo.",
            code="llm_schema",
        )


def parse_json_object(raw: str) -> dict:
    text = raw.strip()
    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise UnprocessableError("Groq no devolvió JSON válido.", code="llm_schema") from exc
    if not isinstance(data, dict):
        raise UnprocessableError("Groq no devolvió un objeto JSON.", code="llm_schema")
    return data


def _compose_prompt(brief: BrandBrief) -> str:
    forbidden = ", ".join(brief.forbidden) or "ninguna"
    name = brief.name or "(propón un nombre corto)"
    return (
        "Arma el manual de marca (Brand DNA) a partir de este brief.\n"
        f"Nombre sugerido: {name}\n"
        f"Producto: {brief.product}\n"
        f"Audiencia: {brief.audience}\n"
        f"Tono: {brief.tone}\n"
        f"Promesa: {brief.promise}\n"
        f"Palabras prohibidas: {forbidden}\n"
        "JSON con claves: name, manifesto, tone, colors (hex), voice_do (3), "
        "voice_dont (incluye las prohibidas), chunks.\n"
        'chunks: lista de 5 objetos {heading, content} con headings '
        'exactos: "Esencia", "Voz", "Límites", "Sistema visual", "Producto".'
    )


def _generate_prompt(
    *,
    kind: AssetKind,
    brand: Brand,
    context: Sequence[Chunk],
    prompt: str,
) -> str:
    piece = {
        AssetKind.PRODUCT_SHEET: "ficha de producto",
        AssetKind.VIDEO_SCRIPT: "guion corto de video (15-25s)",
        AssetKind.IMAGE_PROMPT: (
            "prompt de imagen publicitaria listo para un modelo de imagen "
            "(packshot, paleta del manual, área de respeto del logo)"
        ),
    }.get(kind, "ficha de producto")
    manual = "\n\n".join(
        f"[{chunk.heading}]\n{_redact_forbidden(chunk.content, brand.forbidden)}"
        for chunk in context
    )
    json_hint = (
        "JSON: {title, body}. body es el prompt de imagen, un párrafo, paleta y clearspace del manual."
        if kind is AssetKind.IMAGE_PROMPT
        else "JSON: {title, body}. body en español, 2-4 frases, citando la esencia del manual."
    )
    return (
        f"Escribe una {piece} para {brand.name}.\n"
        f"Pedido del creador: {_redact_forbidden(prompt.strip() or brand.product, brand.forbidden)}\n"
        f"Tono: {brand.tone}. Audiencia: {brand.audience}.\n"
        "No copies los términos tachados del manual ([omitido]); no los escribas ni para prohibirlos.\n"
        f"Manual recuperado (RAG):\n{manual}\n"
        f"{json_hint}"
    )


def _forbidden_hits(text: str, forbidden: Sequence[str]) -> list[str]:
    hits: list[str] = []
    for word in forbidden:
        token = word.strip()
        if not token:
            continue
        if re.search(rf"(?i)(?<!\w){re.escape(token)}(?!\w)", text):
            hits.append(token)
    return hits


def _redact_forbidden(text: str, forbidden: Sequence[str]) -> str:
    redacted = text
    for word in forbidden:
        token = word.strip()
        if not token:
            continue
        redacted = re.sub(rf"(?i)(?<!\w){re.escape(token)}(?!\w)", "[omitido]", redacted)
    return redacted


def _normalize_colors(colors: Sequence[str]) -> tuple[str, ...]:
    cleaned: list[str] = []
    for color in colors:
        value = color.strip().upper()
        if re.fullmatch(r"#[0-9A-F]{6}", value) and value not in cleaned:
            cleaned.append(value)
        if len(cleaned) == 4:
            break
    return tuple(cleaned or DEFAULT_COLORS)


def _citations(context: Sequence[Chunk], text: str) -> tuple[str, ...]:
    lowered = text.casefold()
    used = tuple(chunk.heading for chunk in context if chunk.heading.casefold() in lowered)
    return used or tuple(chunk.heading for chunk in context)
