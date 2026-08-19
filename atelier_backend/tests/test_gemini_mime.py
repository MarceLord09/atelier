from app.core.exceptions import UnprocessableError
from app.infrastructure.gemini_vision import sniff_mime


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
