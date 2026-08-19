import asyncio

from app.infrastructure.embeddings import EMBEDDING_DIM, HashingEmbedder, cosine


def test_hashing_embedder_ranks_related_spanish_copy_higher():
    embedder = HashingEmbedder()
    vectors = asyncio.run(
        embedder.embed(
            [
                "Sistema visual. Paleta de tierra, crema y cacao. Área de respeto alrededor del isotipo.",
                "Límites fiscales y plazos de declaración tributaria para empresas.",
                "cacao crocante de kiwicha y paleta de tierra",
            ]
        )
    )
    assert all(len(vector) == EMBEDDING_DIM for vector in vectors)
    related = cosine(vectors[2], vectors[0])
    unrelated = cosine(vectors[2], vectors[1])
    assert related > unrelated
