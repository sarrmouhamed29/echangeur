from copy import copy
from .modele import ProprietesFlUide

BIBLIOTHEQUE_FLUIDES: dict[str, ProprietesFlUide] = {
    "Eau (20°C)": ProprietesFlUide(
        nom="Eau (20°C)", Q=0.0, rho=998.2, mu=0.001002, cp=4182, lambda_=0.598
    ),
    "Eau (33°C)": ProprietesFlUide(
        nom="Eau (33°C)", Q=0.002194, rho=994.7, mu=0.000749, cp=4178, lambda_=0.62
    ),
    "Eau (40°C)": ProprietesFlUide(
        nom="Eau (40°C)", Q=0.0, rho=992.2, mu=0.000653, cp=4179, lambda_=0.631
    ),
    "Eau (60°C)": ProprietesFlUide(
        nom="Eau (60°C)", Q=0.0, rho=983.2, mu=0.000467, cp=4185, lambda_=0.654
    ),
    "Huile Azolla ZS46 (40°C)": ProprietesFlUide(
        nom="Huile Azolla ZS46 (40°C)", Q=0.00968, rho=858.0, mu=0.0395, cp=2200, lambda_=0.136
    ),
    "Huile hydraulique ISO 46 (40°C)": ProprietesFlUide(
        nom="Huile hydraulique ISO 46 (40°C)", Q=0.0, rho=872.0, mu=0.0414, cp=1980, lambda_=0.130
    ),
    "Glycol 30% (20°C)": ProprietesFlUide(
        nom="Glycol 30% (20°C)", Q=0.0, rho=1041.0, mu=0.00230, cp=3800, lambda_=0.46
    ),
    "Personnalisé": ProprietesFlUide(
        nom="Personnalisé", Q=0.0, rho=1000.0, mu=0.001, cp=4180, lambda_=0.6
    ),
}


def get_noms_fluides() -> list:
    return list(BIBLIOTHEQUE_FLUIDES.keys())


def get_fluide(nom: str) -> ProprietesFlUide:
    return copy(BIBLIOTHEQUE_FLUIDES[nom])
