from dataclasses import dataclass

@dataclass(frozen=True)
class SteelParams:
    """
    Podstawowe parametry stali zbrojeniowej.
    """
    grade: str   # np. "B500B"
    fyk: float   # granica plastyczności [MPa]
    Es: float    # moduł sprężystości [MPa]
    ftk: float | None = None  # wytrzymałość na rozciąganie (opcjonalnie)

STEEL_TABLE: dict[str, SteelParams] = {
    "B400": SteelParams(
        grade="B400",
        fyk=400.0,
        Es=200_000.0,
    ),
    "B500": SteelParams(
        grade="B500",
        fyk=500.0,
        Es=200_000.0,
    ),
    "B550": SteelParams(
        grade="B550",
        fyk=550.0,
        Es=200_000.0,
    ),
    "B600": SteelParams(
        grade="B600",
        fyk=600.0,
        Es=200_000.0,
    ),
    "B700": SteelParams(
        grade="B700",
        fyk=700.0,
        Es=200_000.0,
    ),
}

def get_steel_params(grade: str) -> SteelParams:
    """
    Zwraca parametry stali dla danego gatunku, np. "B500".
    """
    try:
        return STEEL_TABLE[grade]
    except KeyError as exc:
        # Domyślny fallback na B500 w razie błędu, żeby nie wywalić apki
        return STEEL_TABLE["B500"]

def list_steel_grades() -> list[str]:
    """Lista dostępnych gatunków stali (do selectboxów w UI)."""
    return list(STEEL_TABLE.keys())