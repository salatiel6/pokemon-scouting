from app.schemas.pokemon import PokemonIngestRequest


def test_ingest_request_normalizes_names() -> None:
    """
    Ensure names are normalized to lowercase and symbols removed.

    :return: None
    :raises: None
    """
    body = {
        "names": [
            " Pikachu ",
            "Mr. Mime",
            "NIDORAN♀",
            "Farfetch’d",
            "tapu-koko",
            "mewtwo",
            "",
            "   ",
        ]
    }
    req = PokemonIngestRequest(**body)
    # empty/blank entries removed; symbols stripped; lowercase applied
    assert req.names == [
        "pikachu",
        "mrmime",
        "nidoranf",
        "farfetchd",
        "tapukoko",
        "mewtwo",
    ]
