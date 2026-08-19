from app.core.exceptions import UnprocessableError
from app.domain.entities import Chunk
from app.infrastructure.groq_llm import parse_json_object, _citations


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
