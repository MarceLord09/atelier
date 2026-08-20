from collections.abc import Sequence

from app.domain.entities import (
    AuditDraft,
    Brand,
    BrandBook,
    BrandBrief,
    Chunk,
    Finding,
    GeneratedCopy,
)
from app.domain.enums import AssetKind

DEFAULT_COLORS = ("#B8843F", "#F3EEE4", "#51372A", "#2F5D50")


class TemplateBrandComposer:
    async def compose(self, brief: BrandBrief) -> BrandBook:
        name = brief.name or _title_from(brief.product)
        voice_do = (
            "Hablar claro, sin tecnicismos.",
            f"Tono {brief.tone}, directo y cercano.",
            "Anclar el origen y lo cotidiano.",
        )
        voice_dont = (
            "No promesas médicas ni absolutas.",
            *tuple(f'Evitar la palabra “{word}”.' for word in brief.forbidden),
        )
        chunks = (
            Chunk("Esencia", f"{name}. {brief.promise} Pensado para {brief.audience}."),
            Chunk("Voz", " ".join(voice_do)),
            Chunk("Límites", " ".join(voice_dont)),
            Chunk("Sistema visual", "Paleta de tierra, crema y cacao. Área de respeto alrededor del isotipo."),
            Chunk("Producto", brief.product),
        )
        return BrandBook(
            name=name,
            manifesto=brief.promise,
            tone=brief.tone,
            colors=DEFAULT_COLORS,
            voice_do=voice_do,
            voice_dont=voice_dont,
            chunks=chunks,
        )


class TemplateCopyGenerator:
    async def generate(
        self,
        *,
        kind: AssetKind,
        brand: Brand,
        context: Sequence[Chunk],
        prompt: str,
    ) -> GeneratedCopy:
        citations = tuple(chunk.heading for chunk in context)
        if kind is AssetKind.VIDEO_SCRIPT:
            title = prompt.strip() or f"La pausa de {brand.name}"
            body = (
                f"Una pausa breve. {brand.manifesto} "
                f"Hecho para {brand.audience}, con el tono {brand.tone}."
            )
        elif kind is AssetKind.IMAGE_PROMPT:
            title = prompt.strip() or f"Packshot {brand.name}"
            body = (
                f"Photographed pack of {brand.product}, palette {', '.join(brand.colors)}, "
                f"natural light, generous clearspace around the mark, everyday pause for "
                f"{brand.audience}, tone {brand.tone}, no medical claims, no forbidden words."
            )
        else:
            title = prompt.strip() or brand.product
            body = (
                f"{brand.product}. {brand.manifesto} "
                f"Sin {', '.join(brand.forbidden) or 'promesas vacías'}."
            )
        return GeneratedCopy(title=title, body=body, model="template", citations=citations)


class TemplateVisionAuditor:
    async def audit(
        self,
        *,
        brand: Brand,
        image_name: str,
        image: bytes,
        context: Sequence[Chunk] = (),
    ) -> AuditDraft:
        _ = context
        findings = (
            Finding(
                n=1,
                title="Color fuera de paleta",
                detail=(
                    f"Contraste inicial de {image_name} ({len(image)} bytes) contra {brand.name}. "
                    f"La paleta activa es {', '.join(brand.colors)}."
                ),
                rule="Regla 03 · Paleta",
                ok=False,
            ),
            Finding(
                n=2,
                title="Texto demasiado agresivo",
                detail=(
                    f"El tono del manual es {brand.tone}. "
                    f"No usar: {', '.join(brand.forbidden) or 'promesas absolutas'}."
                ),
                rule="Regla 02 · Voz",
                ok=False,
            ),
        )
        passed = False
        return AuditDraft(passed=passed, findings=findings, model="template")


def _title_from(product: str) -> str:
    parts = [part for part in product.replace(" de ", " ").split() if part]
    if len(parts) >= 2:
        return f"{parts[0].title()} {parts[1].title()}"
    return product[:40].title() or "Marca"
