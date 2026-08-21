from datetime import UTC, datetime
from uuid import uuid4

from app.core.exceptions import UnprocessableError
from app.domain.entities import Brand, Finding
from app.infrastructure.gemini_vision import _correct_name_finding, sniff_mime


def test_sniff_mime_jpeg_png_webp():
    assert sniff_mime(b"\xff\xd8\xff" + b"\x00" * 8) == "image/jpeg"
    assert sniff_mime(b"\x89PNG\r\n\x1a\n" + b"\x00") == "image/png"
    assert sniff_mime(b"RIFF" + b"\x00" * 4 + b"WEBP") == "image/webp"


def test_sniff_mime_rejects_other_bytes():
    try:
        sniff_mime(b"GIF89a")
    except UnprocessableError:
        return
    raise AssertionError("expected UnprocessableError")


def test_name_check_does_not_confuse_atelier_with_brand():
    brand = Brand(
        id=uuid4(),
        name="Primitivo",
        product="Alitas",
        audience="Bar",
        tone="cercano",
        promise="Sabor",
        manifesto="Sabor",
        forbidden=(),
        colors=("#000000",),
        voice_do=(),
        voice_dont=(),
        created_by=uuid4(),
        indexed_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    finding = Finding(
        n=1,
        title="Nombre de marca",
        detail="El texto visible presenta Primitivo y Cusqueña, no coincide con la marca ATELIER.",
        rule="Regla 01 · Nombre",
        ok=False,
    )
    fixed = _correct_name_finding(finding, brand)
    assert fixed.ok is True
    assert "ATELIER" not in fixed.detail or "plataforma" in fixed.detail.casefold()
    assert "Primitivo" in fixed.detail


def test_name_check_keeps_fail_when_other_brand_is_the_hero():
    brand = Brand(
        id=uuid4(),
        name="Primitivo",
        product="Alitas",
        audience="Bar",
        tone="cercano",
        promise="Sabor",
        manifesto="Sabor",
        forbidden=(),
        colors=("#000000",),
        voice_do=(),
        voice_dont=(),
        created_by=uuid4(),
        indexed_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    finding = Finding(
        n=1,
        title="Nombre de marca",
        detail="La imagen incluye el logotipo de Blanca Flor en lugar de mostrar la marca activa Primitivo.",
        rule="Regla 01 · Nombre",
        ok=False,
    )
    fixed = _correct_name_finding(finding, brand)
    assert fixed.ok is False


def test_pin_xy_uses_model_coords_and_falls_back_by_title():
    from app.infrastructure.gemini_vision import _pin_xy

    placed = _pin_xy(82, 14, title="Nombre de marca", rule="Regla 01 · Nombre", n=1)
    assert placed == (82.0, 14.0)
    fallback = _pin_xy(None, None, title="Nombre de marca", rule="Regla 01 · Nombre", n=1)
    assert fallback == (84.0, 16.0)
    scaled = _pin_xy(0.8, 0.2, title="Nombre de marca", rule="Regla 01 · Nombre", n=1)
    assert scaled == (80.0, 20.0)
