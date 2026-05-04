from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProprietesFlUide:
    nom: str
    Q: float          # Débit volumique [m³/s]
    rho: float        # Masse volumique [kg/m³]
    mu: float         # Viscosité dynamique [Pa·s]
    cp: float         # Chaleur massique [J/kgK]
    lambda_: float    # Conductivité thermique [W/mK]


@dataclass
class GeometriePlaque:
    s: float = 0.21              # Surface unitaire [m²]
    b: float = 0.0025            # Gap entre plaques [m]
    l: float = 0.31              # Largeur utile [m]
    e: float = 0.0006            # Épaisseur paroi [m]
    lambda_paroi: float = 15.0   # Conductivité paroi [W/mK]
    angle_chevrons: float = 45.0 # Angle de corrugation [°]
    max_plaques: int = 200       # Limite catalogue [—]


@dataclass
class ParametresProcess:
    P: float                          # Puissance à échanger [W]
    DTLM: float                       # Différence de température log. moyenne [K]
    H_est_initial: float = 500.0      # H global estimé initial [W/m²K]
    seuil_convergence: float = 5.0    # Seuil de convergence [%]
    nombre_passes: int = 1            # Nombre de passes
    R_enc_fluide1: float = 0.001      # Résistance encrassement fluide 1 [m²K/W]
    R_enc_fluide2: float = 0.0009     # Résistance encrassement fluide 2 [m²K/W]


@dataclass
class ResultatIteration:
    numero: int
    H_est: float
    S: float           # Surface d'échange [m²]
    N: int             # Nombre de plaques
    n: int             # Nombre de canaux
    A: float           # Section canal [m²]
    Dh: float          # Diamètre hydraulique [m]
    v1: float          # Vitesse fluide 1 [m/s]
    Re1: float
    Pr1: float
    Nu1: float
    h1: float          # Coeff. échange fluide 1 [W/m²K]
    v2: float          # Vitesse fluide 2 [m/s]
    Re2: float
    Pr2: float
    Nu2: float
    h2: float          # Coeff. échange fluide 2 [W/m²K]
    H_calc: float      # H global calculé [W/m²K]
    erreur: float      # Erreur relative [fraction]
    converge: bool


@dataclass
class ResultatFinal:
    iterations: List[ResultatIteration] = field(default_factory=list)
    converge: bool = False
    n_iterations: int = 0
    H_global: float = 0.0
    S_finale: float = 0.0
    N_plaques: int = 0
    n_canaux: int = 0
    delta_P_fluide1: float = 0.0   # Perte de charge fluide 1 [Pa]
    delta_P_fluide2: float = 0.0   # Perte de charge fluide 2 [Pa]
    process: Optional[ParametresProcess] = None
    geometrie: Optional[GeometriePlaque] = None
    fluide1: Optional[ProprietesFlUide] = None
    fluide2: Optional[ProprietesFlUide] = None
