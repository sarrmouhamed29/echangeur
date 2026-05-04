from dataclasses import dataclass
from copy import copy


@dataclass
class EchangeurSpec:
    frame: str
    s: float          # Surface unitaire plaque [m²]
    l: float          # Largeur utile (B) [m]
    e: float          # Épaisseur paroi [m]
    pp: float         # Pas plaque (pitch) [mm]
    lambda_paroi: float  # Conductivité paroi [W/mK]
    max_plaques: int
    max_pression: float  # [bar]
    connexions: str

    @property
    def b(self) -> float:
        """Gap entre plaques : b = PP - e  [m]"""
        return (self.pp - self.e * 1000) / 1000


# ── Matériaux disponibles ────────────────────────────────────────

MATERIAUX = {
    "Acier inox 304/316L": 16.0,
    "Titane":              21.0,
    "Hastelloy C-276":     12.0,
    "Incoloy 825":         11.0,
    "Cupronickel 70/30":   29.0,
}


# ── Catalogue complet ────────────────────────────────────────────
# Colonnes : frame, s(m²), B(m)→l, ep(mm)→e, PP(mm), λ(W/mK), max_pl, max_P(bar), connexions

def _e(nom, s, B, ep, pp, lam, max_pl, max_p, conn):
    return EchangeurSpec(
        frame=nom, s=s, l=B/1000, e=ep/1000, pp=pp,
        lambda_paroi=lam, max_plaques=max_pl, max_pression=max_p, connexions=conn,
    )


CATALOGUE: dict[str, EchangeurSpec] = {e.frame: e for e in [
    # ── 1" — 16 bar
    _e("FP 04",    0.04, 160, 0.5, 2.4, 16.0, 125, 16, '1"'),
    _e("FP 08",    0.08, 160, 0.5, 2.4, 16.0, 150, 16, '1"'),
    _e("FP 14",    0.14, 310, 0.6, 2.4, 16.0, 200, 16, '1"'),
    _e("FP 20",    0.20, 310, 0.6, 2.4, 16.0, 200, 16, '1"'),
    # ── 1" — 25 bar
    _e("FP 05",    0.04, 200, 0.5, 2.7, 16.0, 150, 25, '1"'),
    _e("FP 09",    0.08, 200, 0.5, 2.7, 16.0, 150, 25, '1"'),
    _e("FPDW 05",  0.04, 200, 0.5, 2.9, 16.0, 150, 16, '1"'),
    # ── 2" — 25 bar
    _e("FP 10",    0.10, 310, 0.6, 2.9, 16.0, 200, 25, '2"'),
    _e("FP 16",    0.16, 310, 0.6, 2.9, 16.0, 200, 25, '2"'),
    _e("FP 22",    0.21, 310, 0.6, 2.9, 16.0, 200, 25, '2"'),
    _e("FPDW 16",  0.16, 310, 0.6, 3.1, 16.0, 200, 25, '2"'),
    # ── DN 80 — 16 bar
    _e("FP 19",    0.19, 440, 0.6, 3.1, 16.0, 500, 16, "DN 80"),
    _e("FPDW 19",  0.19, 440, 0.6, 3.1, 16.0, 500, 16, "DN 80"),
    # ── DN 100 — 25 bar
    _e("FP 205",   0.21, 480, 0.6, 3.1, 16.0, 500, 25, "DN 100"),
    _e("FP 31",    0.30, 480, 0.6, 3.1, 16.0, 500, 25, "DN 100"),
    _e("FP 40",    0.40, 480, 0.6, 3.1, 16.0, 500, 25, "DN 100"),
    _e("FP 50",    0.50, 480, 0.6, 3.1, 16.0, 500, 25, "DN 100"),
    _e("FP 71",    0.70, 480, 0.6, 3.1, 16.0, 500, 25, "DN 100"),
    _e("FPDW 205", 0.21, 480, 0.6, 3.3, 16.0, 500, 16, "DN 100"),
    _e("FPDW 31",  0.30, 480, 0.6, 3.3, 16.0, 500, 16, "DN 100"),
    _e("FPDW 50",  0.50, 480, 0.6, 3.3, 16.0, 500, 16, "DN 100"),
    # ── DN 150 — 700 plaques
    _e("FP 41",    0.40, 620, 0.7, 3.5, 16.0, 700, 25, "DN 150"),
    _e("FP 60",    0.60, 620, 0.7, 3.5, 16.0, 700, 25, "DN 150"),
    _e("FP 80",    0.80, 620, 0.7, 3.5, 16.0, 700, 25, "DN 150"),
    _e("FPDW 80",  0.80, 620, 0.7, 3.7, 16.0, 700, 16, "DN 150"),
    # ── DN 150 — 750 plaques
    _e("FP 42",    0.40, 620, 0.7, 3.1, 16.0, 750, 25, "DN 150"),
    _e("FP 62",    0.60, 620, 0.7, 3.1, 16.0, 750, 25, "DN 150"),
    _e("FP 82",    0.80, 620, 0.7, 3.1, 16.0, 750, 25, "DN 150"),
    _e("FP 112",   1.15, 620, 0.7, 3.1, 16.0, 750, 25, "DN 150"),
    # ── DN 200
    _e("FP 405",   0.41, 760, 0.7, 3.1, 16.0, 700, 25, "DN 200"),
    _e("FP 70",    0.70, 760, 0.7, 3.1, 16.0, 700, 25, "DN 200"),
    _e("FP 100",   1.00, 760, 0.7, 3.1, 16.0, 700, 25, "DN 200"),
    _e("FP 130",   1.30, 760, 0.7, 3.1, 16.0, 700, 25, "DN 200"),
    _e("FPDW 100", 1.00, 760, 0.7, 3.3, 16.0, 700, 16, "DN 200"),
    # ── DN 300
    _e("FP 81",    0.80,  980, 0.8, 3.8, 16.0, 800, 25, "DN 300"),
    _e("FP 120",   1.20,  980, 0.8, 3.8, 16.0, 800, 25, "DN 300"),
    _e("FP 160",   1.60,  980, 0.8, 3.8, 16.0, 800, 25, "DN 300"),
    _e("FP 190",   1.90,  980, 0.8, 3.8, 16.0, 800, 25, "DN 300"),
    # ── DN 500
    _e("FP 150",   1.50, 1370, 1.0, 4.1, 16.0, 800, 25, "DN 500"),
    _e("FP 200",   2.00, 1370, 1.0, 4.1, 16.0, 800, 25, "DN 500"),
    _e("FP 250",   2.50, 1370, 1.0, 4.1, 16.0, 800, 25, "DN 500"),
    _e("FP 300",   3.00, 1370, 1.0, 4.1, 16.0, 800, 25, "DN 500"),
]}


def get_frames() -> list[str]:
    return list(CATALOGUE.keys())


def get_spec(frame: str) -> EchangeurSpec:
    return copy(CATALOGUE[frame])
