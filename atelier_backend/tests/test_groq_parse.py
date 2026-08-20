from app.core.exceptions import UnprocessableError
from app.domain.entities import Chunk
from app.infrastructure.groq_llm import (
    parse_json_object,
    _citations,
    _forbidden_hits,
    _redact_forbidden,
)


def test_parse_json_object_accepts_fenced_payload():
    payload = parse_json_object('```json\n{"title": "Kiwicha", "body": "Pausa con cacao."}\n```')
    assert payload["title"] == "Kiwicha"


def test_parse_json_object_rejects_array():
    try:
        parse_json_object("[1, 2]")
    except UnprocessableError as exc:
        assert exc.code == "llm_schema"
    else:
        raise AssertionError("expected UnprocessableError")


def test_citations_prefer_headings_mentioned_in_copy():
    context = (
        Chunk("Esencia", "Origen andino."),
        Chunk("Límites", "Nada de milagroso."),
        Chunk("Producto", "Crocante de cacao."),
    )
    used = _citations(context, "El crocante sigue la Esencia del origen.")
    assert used == ("Esencia",)


def test_forbidden_hits_match_whole_words_only():
    text = "Es un superalimento andino, no un super."
    assert _forbidden_hits(text, ["superalimento", "milagroso"]) == ["superalimento"]
    assert _forbidden_hits("Pausa cotidiana con cacao.", ["superalimento"]) == []


def test_redact_forbidden_hides_banned_tokens():
    source = 'Evitar la palabra “superalimento”. Nada de milagroso.'
    redacted = _redact_forbidden(source, ["superalimento", "milagroso"])
    assert "superalimento" not in redacted.casefold()
    assert "milagroso" not in redacted.casefold()
    assert "[omitido]" in redacted
