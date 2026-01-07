# TABLICE/ParametryBetonu.py

from dataclasses import dataclass

@dataclass(frozen=True)
class ConcreteParams:
    """
    Parametry betonu wg PN-EN 1992-1-1, Tablica 3.1.

    Jednostki:
    - Wytrzymałości i moduły: MPa (N/mm²)
    - Odkształcenia (eps): promile (‰)
    """
    fck: float        # Charakterystyczna wytrzymałość walcowa
    fck_cube: float   # Charakterystyczna wytrzymałość kostkowa
    fcm: float        # Średnia wytrzymałość na ściskanie
    fctm: float       # Średnia wytrzymałość na rozciąganie
    fctk_0_05: float  # 5% kwantyl wytrzymałości na rozciąganie
    fctk_0_95: float  # 95% kwantyl wytrzymałości na rozciąganie
    Ecm: float        # Moduł sprężystości (sieczny)

    # Odkształcenia graniczne i parametry wykresów
    eps_c1: float     # Odkształcenie przy max naprężeniu (wykres nieliniowy)
    eps_cu1: float    # Odkształcenie graniczne (wykres nieliniowy)
    eps_c2: float     # Odkształcenie przy max naprężeniu (parabola-prostokąt)
    eps_cu2: float    # Odkształcenie graniczne (parabola-prostokąt)
    n: float          # Wykładnik potęgi (parabola-prostokąt)
    eps_c3: float     # Odkształcenie przy max naprężeniu (dwuliniowy)
    eps_cu3: float    # Odkształcenie graniczne (dwuliniowy)


# Tablica 3.1 wg PN-EN 1992-1-1
# Ecm podane w normie w GPa, tutaj przeliczone na MPa (*1000)
CONCRETE_TABLE: dict[str, ConcreteParams] = {
    "C12/15": ConcreteParams(
        fck=12.0, fck_cube=15.0, fcm=20.0, fctm=1.6, fctk_0_05=1.1, fctk_0_95=2.0, Ecm=27000.0,
        eps_c1=1.8, eps_cu1=3.5, eps_c2=2.0, eps_cu2=3.5, n=2.0, eps_c3=1.75, eps_cu3=3.5
    ),
    "C16/20": ConcreteParams(
        fck=16.0, fck_cube=20.0, fcm=24.0, fctm=1.9, fctk_0_05=1.3, fctk_0_95=2.5, Ecm=29000.0,
        eps_c1=1.9, eps_cu1=3.5, eps_c2=2.0, eps_cu2=3.5, n=2.0, eps_c3=1.75, eps_cu3=3.5
    ),
    "C20/25": ConcreteParams(
        fck=20.0, fck_cube=25.0, fcm=28.0, fctm=2.2, fctk_0_05=1.5, fctk_0_95=2.9, Ecm=30000.0,
        eps_c1=2.0, eps_cu1=3.5, eps_c2=2.0, eps_cu2=3.5, n=2.0, eps_c3=1.75, eps_cu3=3.5
    ),
    "C25/30": ConcreteParams(
        fck=25.0, fck_cube=30.0, fcm=33.0, fctm=2.6, fctk_0_05=1.8, fctk_0_95=3.3, Ecm=31000.0,
        eps_c1=2.1, eps_cu1=3.5, eps_c2=2.0, eps_cu2=3.5, n=2.0, eps_c3=1.75, eps_cu3=3.5
    ),
    "C30/37": ConcreteParams(
        fck=30.0, fck_cube=37.0, fcm=38.0, fctm=2.9, fctk_0_05=2.0, fctk_0_95=3.8, Ecm=32000.0,
        eps_c1=2.2, eps_cu1=3.5, eps_c2=2.0, eps_cu2=3.5, n=2.0, eps_c3=1.75, eps_cu3=3.5
    ),
    "C35/45": ConcreteParams(
        fck=35.0, fck_cube=45.0, fcm=43.0, fctm=3.2, fctk_0_05=2.2, fctk_0_95=4.2, Ecm=34000.0,
        eps_c1=2.25, eps_cu1=3.5, eps_c2=2.0, eps_cu2=3.5, n=2.0, eps_c3=1.75, eps_cu3=3.5
    ),
    "C40/50": ConcreteParams(
        fck=40.0, fck_cube=50.0, fcm=48.0, fctm=3.5, fctk_0_05=2.5, fctk_0_95=4.6, Ecm=35000.0,
        eps_c1=2.3, eps_cu1=3.5, eps_c2=2.0, eps_cu2=3.5, n=2.0, eps_c3=1.75, eps_cu3=3.5
    ),
    "C45/55": ConcreteParams(
        fck=45.0, fck_cube=55.0, fcm=53.0, fctm=3.8, fctk_0_05=2.7, fctk_0_95=4.9, Ecm=36000.0,
        eps_c1=2.4, eps_cu1=3.5, eps_c2=2.0, eps_cu2=3.5, n=2.0, eps_c3=1.75, eps_cu3=3.5
    ),
    "C50/60": ConcreteParams(
        fck=50.0, fck_cube=60.0, fcm=58.0, fctm=4.1, fctk_0_05=2.9, fctk_0_95=5.3, Ecm=37000.0,
        eps_c1=2.45, eps_cu1=3.5, eps_c2=2.0, eps_cu2=3.5, n=2.0, eps_c3=1.75, eps_cu3=3.5
    ),
    # --- Betony wysokiej wytrzymałości ---
    "C55/67": ConcreteParams(
        fck=55.0, fck_cube=67.0, fcm=63.0, fctm=4.2, fctk_0_05=3.0, fctk_0_95=5.5, Ecm=38000.0,
        eps_c1=2.5, eps_cu1=3.2, eps_c2=2.2, eps_cu2=3.1, n=1.75, eps_c3=1.8, eps_cu3=3.1
    ),
    "C60/75": ConcreteParams(
        fck=60.0, fck_cube=75.0, fcm=68.0, fctm=4.4, fctk_0_05=3.1, fctk_0_95=5.7, Ecm=39000.0,
        eps_c1=2.6, eps_cu1=3.0, eps_c2=2.3, eps_cu2=2.9, n=1.6, eps_c3=1.9, eps_cu3=2.9
    ),
    "C70/85": ConcreteParams(
        fck=70.0, fck_cube=85.0, fcm=78.0, fctm=4.6, fctk_0_05=3.2, fctk_0_95=6.0, Ecm=41000.0,
        eps_c1=2.7, eps_cu1=2.8, eps_c2=2.4, eps_cu2=2.7, n=1.45, eps_c3=2.0, eps_cu3=2.7
    ),
    "C80/95": ConcreteParams(
        fck=80.0, fck_cube=95.0, fcm=88.0, fctm=4.8, fctk_0_05=3.4, fctk_0_95=6.3, Ecm=42000.0,
        eps_c1=2.8, eps_cu1=2.8, eps_c2=2.5, eps_cu2=2.6, n=1.4, eps_c3=2.2, eps_cu3=2.6
    ),
    "C90/105": ConcreteParams(
        fck=90.0, fck_cube=105.0, fcm=98.0, fctm=5.0, fctk_0_05=3.5, fctk_0_95=6.6, Ecm=44000.0,
        eps_c1=2.8, eps_cu1=2.8, eps_c2=2.6, eps_cu2=2.6, n=1.4, eps_c3=2.3, eps_cu3=2.6
    ),
}


def get_concrete_params(klasa_betonu: str) -> ConcreteParams:
    """
    Zwraca parametry betonu dla podanej klasy, np. "C20/25".
    """
    try:
        return CONCRETE_TABLE[klasa_betonu]
    except KeyError as exc:
        raise KeyError(
            f"Nieznana klasa betonu: {klasa_betonu!r}. "
            f"Dostępne: {', '.join(CONCRETE_TABLE.keys())}"
        ) from exc


def list_concrete_classes() -> list[str]:
    """Zwraca listę dostępnych klas betonu (do selectboxów w UI)."""
    return list(CONCRETE_TABLE.keys())
