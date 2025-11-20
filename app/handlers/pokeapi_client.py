from typing import Any

import requests

from app.handlers.logger import logger


class PokeAPIError(Exception):
    """Base exception for PokeAPI client errors."""


class PokemonNotFoundError(PokeAPIError):
    """Error raised when a Pokemon resource is not found (HTTP 404)."""


class PokeAPIClient:
    """
    Simple HTTP client for PokeAPI v2 endpoints that resolves known lowercase
    alias inputs to canonical PokeAPI slugs before requesting.
    """

    def __init__(self, base_url: str, timeout_s: float = 10.0) -> None:
        """
        Initialize the client with a base URL and timeout.

        :param base_url: Base URL for PokeAPI
        :param timeout_s: Request timeout in seconds

        :return: None
        """
        self.base_url = base_url.rstrip("/")
        self.timeout_s = float(timeout_s)

    # Known aliases mapping from user-required normalized input (lowercase, no
    # spaces/hyphens/punctuation) to the canonical PokeAPI slug (may include
    # hyphens and mixed-case when required by upstream).
    POKEMON_ALIASES: dict[str, str] = {
        "nidoranf": "nidoran-f",
        "nidoranm": "nidoran-m",
        "drowzee": "Drowzee",
        "mrmime": "mr-mime",
        "mewtwo": "MewTwo",
        "hooh": "ho-oh",
        "deoxysnormal": "deoxys-normal",
        "wormadamplant": "wormadam-plant",
        "drifloon": "Drifloon",
        "mimejr": "mime-jr",
        "porygonz": "porygon-z",
        "giratinaaltered": "giratina-altered",
        "shayminland": "shaymin-land",
        "basculinredstriped": "basculin-red-striped",
        "darmanitanstandard": "darmanitan-standard",
        "tornadusincarnate": "tornadus-incarnate",
        "thundurusincarnate": "thundurus-incarnate",
        "landorusincarnate": "landorus-incarnate",
        "keldeoordinary": "keldeo-ordinary",
        "meloettaaria": "meloetta-aria",
        "meowsticmale": "meowstic-male",
        "aegislashshield": "aegislash-shield",
        "pumpkabooaverage": "pumpkaboo-average",
        "gourgeistaverage": "gourgeist-average",
        "zygarde50": "zygarde-50",
        "oricoriobaile": "oricorio-baile",
        "lycanrocmidday": "lycanroc-midday",
        "wishiwashisolo": "wishiwashi-solo",
        "typenull": "type-null",
        "miniorredmeteor": "minior-red-meteor",
        "mimikyudisguised": "mimikyu-disguised",
        "jangmoo": "jangmo-o",
        "hakamoo": "hakamo-o",
        "kommoo": "kommo-o",
        "tapukoko": "tapu-koko",
        "tapulele": "tapu-lele",
        "tapubulu": "tapu-bulu",
        "tapufini": "tapu-fini",
        "toxtricityamped": "toxtricity-amped",
        "mrrime": "mr-rime",
        "eiscueice": "eiscue-ice",
        "indeedeemale": "indeedee-male",
        "morpekofullbelly": "morpeko-full-belly",
        "urshifusinglestrike": "urshifu-single-strike",
        "basculegionmale": "basculegion-male",
        "enamorusincarnate": "enamorus-incarnate",
        "oinkolognemale": "oinkologne-male",
        "mausholdfamilyoffour": "maushold-family-of-four",
        "squawkabillygreenplumage": "squawkabilly-green-plumage",
        "palafinzero": "palafin-zero",
        "tatsugiricurly": "tatsugiri-curly",
        "dudunsparcetwosegment": "dudunsparce-two-segment",
        "greattusk": "great-tusk",
        "screamtail": "scream-tail",
        "brutebonnet": "brute-bonnet",
        "fluttermane": "flutter-mane",
        "slitherwing": "slither-wing",
        "sandyshocks": "sandy-shocks",
        "irontreads": "iron-treads",
        "ironbundle": "iron-bundle",
        "ironhands": "iron-hands",
        "ironjugulis": "iron-jugulis",
        "ironmoth": "iron-moth",
        "ironthorns": "iron-thorns",
        "wochian": "wo-chien",
        "chienpao": "chien-pao",
        "tinglu": "ting-lu",
        "chiyu": "chi-yu",
        "roaringmoon": "roaring-moon",
        "ironvaliant": "iron-valiant",
        "walkingwake": "walking-wake",
        "ironleaves": "iron-leaves",
        "gougingfire": "gouging-fire",
        "ragingbolt": "raging-bolt",
        "ironboulder": "iron-boulder",
        "ironcrown": "iron-crown",
    }

    def get_pokemon_by_name(self, name: str) -> dict[str, Any]:
        """
        Fetch a Pokemon resource by its name using alias mapping only.

        The user input must be lowercase without spaces/hyphens/punctuation.
        If the normalized input matches an alias key, it is replaced by the
        canonical PokeAPI slug before the request. Otherwise, the input is
        used as provided.

        :param name: Pokemon name as provided by the user

        :return: Raw JSON payload as a dictionary
        :raises: PokemonNotFoundError if not found; PokeAPIError for other errors
        """
        raw = str(name or "").strip()

        normalized = "".join(ch for ch in raw.lower() if ch.isalnum())
        slug = self.POKEMON_ALIASES.get(normalized, raw)
        data = self._try_fetch(slug)
        if data is None:
            raise PokemonNotFoundError(
                f"Pokemon not found for input '{name}'. If you provided a raw lowercase name, "
                f"please verify it against PokeAPI's canonical slug."
            )
        return data

    def _try_fetch(self, slug: str) -> dict[str, Any] | None:
        """
        Try to fetch a Pokemon by a given slug. Returns None on 404.

        :param slug: A candidate slug to append to /pokemon/

        :return: JSON dict on success, or None if the response was 404
        :raises: PokeAPIError for non-404 HTTP errors or request failures
        """
        url = f"{self.base_url}/pokemon/{slug}"
        try:
            resp = requests.get(url, timeout=self.timeout_s)
        except requests.RequestException as e:
            logger.error(f"request error: {e}")
            raise PokeAPIError(f"network error: {e}") from e

        if resp.status_code == 404:
            return None
        if not resp.ok:
            raise PokeAPIError(f"status {resp.status_code}: {resp.text}")
        return resp.json()
