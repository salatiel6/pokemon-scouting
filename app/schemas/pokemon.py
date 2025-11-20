from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PokemonIngestRequest(BaseModel):
    """Request body schema for ingesting Pokemon names."""

    names: list[str] = Field(default_factory=list, description="list of Pokemon names")

    @field_validator("names")
    @classmethod
    def _normalize(cls, v: list[str]) -> list[str]:
        """
        Normalize names to the required input rule: lowercase and no symbols.

        All non-alphanumeric characters are removed and the string is lowercased.

        :param v: a list of strings

        :return: Normalized list (lowercase, alphanumeric only), empty entries removed
        """
        norm: list[str] = []
        for x in v:
            s = str(x).strip().lower()
            # Map gender symbols before stripping non-alphanumerics
            s = s.replace("♀", "f").replace("♂", "m")
            s = "".join(ch for ch in s if ch.isalnum())
            if s:
                norm.append(s)
        return norm


class PokemonSummary(BaseModel):
    """Summary representation for listing Pokemon."""

    id: str
    name: str
    pokedex_number: int
    types: list[str] = Field(default_factory=list)


class PokemonDetail(BaseModel):
    """Detailed representation of a Pokemon resource."""

    id: str
    name: str
    pokedex_number: int
    height_m: float
    weight_kg: float
    base_experience: Optional[int] = None
    stats: dict[str, int]
    types: list[str]
    abilities: list[str]

    model_config = ConfigDict(from_attributes=True)


class IngestResult(BaseModel):
    """Result summary for an ingestion run."""

    ok: list[str] = Field(default_factory=list)
    not_found: list[str] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)


class TypesFilterRequest(BaseModel):
    """
    Request body schema for filtering Pokemon by types (union semantics).

    :return: None
    :raises: None
    """

    types: list[str] = Field(default_factory=list, description="list of type names to match (union)")

    @field_validator("types")
    @classmethod
    def _normalize_types(cls, v: list[str]) -> list[str]:
        """
        Normalize type names by trimming and lowercasing; remove empty entries and duplicates preserving order.

        :param v: a list of strings

        :return: Normalized list of unique, lowercased type names
        :raises: None
        """
        seen: set[str] = set()
        out: list[str] = []
        for x in v:
            s = str(x).strip().lower()
            if not s:
                continue
            if s in seen:
                continue
            seen.add(s)
            out.append(s)
        return out


STAT_KEYS = {
    "hp",
    "attack",
    "defense",
    "special-attack",
    "special-defense",
    "speed",
}

# Known aliases mapping from user-required normalized input
# (lowercase, no spaces/hyphens/punctuation) to the canonical PokeAPI
# (may include hyphens and mixed-case when required by upstream).
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
