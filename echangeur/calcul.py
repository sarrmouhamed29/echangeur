import math
from .modele import (
    ProprietesFlUide, GeometriePlaque, ParametresProcess,
    ResultatIteration, ResultatFinal,
)


# Table des coefficients a et b selon l'angle de corrugation et Re
# Format : (angle_min, angle_max, Re_min, Re_max, a, b)
# Les bornes sont inclusives côté min, exclusives côté max
_TABLE_AB = [
    # angle < 30
    (  0,  30,    0,   10, 0.718, 0.349),
    (  0,  30,   10, None, 0.348, 0.663),
    # angle 30–47 → 45°
    ( 30,  48,    0,   10, 0.718, 0.349),
    ( 30,  48,   10,  100, 0.400, 0.598),
    ( 30,  48,  100, None, 0.300, 0.663),
    # angle 48–55 → 50°
    ( 48,  55,    0,   20, 0.630, 0.333),
    ( 48,  55,   20,  300, 0.291, 0.591),
    ( 48,  55,  300, None, 0.130, 0.732),
    # angle 55–63 → 60°
    ( 55,  63,    0,   20, 0.562, 0.326),
    ( 55,  63,   20,  400, 0.306, 0.529),
    ( 55,  63,  400, None, 0.108, 0.703),
    # angle > 63 → >65°
    ( 63, None,   0,   20, 0.562, 0.326),
    ( 63, None,  20,  500, 0.331, 0.503),
    ( 63, None, 500, None, 0.087, 0.718),
]


def _get_ab(angle: float, Re: float) -> tuple:
    for a_min, a_max, re_min, re_max, a, b in _TABLE_AB:
        angle_ok = angle >= a_min and (a_max is None or angle < a_max)
        re_ok = Re >= re_min and (re_max is None or Re < re_max)
        if angle_ok and re_ok:
            return a, b
    # fallback : dernière ligne
    return 0.087, 0.718


def _nusselt(Re: float, Pr: float, angle: float) -> float:
    a, b = _get_ab(angle, Re)
    return a * (Re ** b) * (Pr ** 0.33)


def _h(Nu: float, lambda_fluide: float, Dh: float) -> float:
    return Nu * lambda_fluide / Dh


def _H_global(
    h1: float, h2: float,
    e: float, lambda_paroi: float,
    R_enc1: float, R_enc2: float,
) -> float:
    return 1.0 / (1.0/h1 + 1.0/h2 + e/lambda_paroi + R_enc1 + R_enc2)


# Table des corrélations de facteur de frottement f = C * Re^n
# (angle_min, angle_max, Re_min, Re_max, C, n)
# angle_max=None → pas de borne supérieure ; Re_max=None → idem
_TABLE_F = [
    # Lisse (β < 15°)
    ( 0,  15,     0,  2000,  24.000, -1.000),   # f = 24/Re
    ( 0,  15,  2000,  None,   0.079, -0.250),   # f = 0.079 Re^-0.25
    # α = 30° (15° ≤ β < 45°)
    (15,  45,    40,   500,  23.330, -0.809),
    (15,  45,   500, 17000,   0.557, -0.211),
    # α = 60° (45° ≤ β < 75°)
    (45,  75,    20,   140,  47.450, -0.680),
    (45,  75,   140,  4500,   3.917, -0.175),
    # α = 90° (β ≥ 75°)
    (75, None,   40,   180,  63.800, -0.809),
    (75, None,  180,   700,   4.820, -0.312),
]


def _facteur_frottement(angle: float, Re: float) -> float:
    """Sélectionne C et n selon l'angle et Re, retourne f = C * Re^n."""
    # Filtrer les lignes correspondant à l'angle
    lignes_angle = [
        row for row in _TABLE_F
        if Re >= 0  # toujours vrai, filtre réel sur l'angle ci-dessous
        and row[0] <= angle < (row[1] if row[1] is not None else float("inf"))
    ]
    if not lignes_angle:
        # fallback : lisse
        lignes_angle = _TABLE_F[:2]

    # Trouver la ligne dont la plage Re correspond
    for _, _, re_min, re_max, C, n in lignes_angle:
        if Re >= re_min and (re_max is None or Re < re_max):
            return C * (Re ** n)

    # Re hors plage : utiliser la corrélation la plus proche (borne basse ou haute)
    if Re < lignes_angle[0][2]:          # Re en-dessous de la borne basse
        C, n = lignes_angle[0][4], lignes_angle[0][5]
    else:                                 # Re au-dessus de la borne haute
        C, n = lignes_angle[-1][4], lignes_angle[-1][5]
    return C * (Re ** n)


def _perte_charge(
    fluide: ProprietesFlUide,
    geo: GeometriePlaque,
    Re: float,
    v: float,
) -> float:
    L = geo.s / geo.l  # longueur de plaque [m]
    Dh = 4 * geo.b * geo.l / (2 * (geo.b + geo.l))
    f = _facteur_frottement(geo.angle_chevrons, Re)
    return f * (L / Dh) * (fluide.rho * v**2 / 2.0)


def _une_iteration(
    H_est: float,
    process: ParametresProcess,
    geo: GeometriePlaque,
    fluide1: ProprietesFlUide,
    fluide2: ProprietesFlUide,
    numero: int,
) -> ResultatIteration:
    # Surface et nombre de plaques
    S = process.P / (H_est * process.DTLM)
    N = math.ceil(S / geo.s)
    n = (N - 1) // (2 * process.nombre_passes)  # canaux en parallèle par passe et par fluide

    A = geo.b * geo.l
    Dh = 4 * geo.b * geo.l / (2 * (geo.b + geo.l))

    angle = geo.angle_chevrons

    # Fluide 1
    v1 = fluide1.Q / (n * A)
    Re1 = fluide1.rho * v1 * Dh / fluide1.mu
    Pr1 = fluide1.mu * fluide1.cp / fluide1.lambda_
    Nu1 = _nusselt(Re1, Pr1, angle)
    h1 = _h(Nu1, fluide1.lambda_, Dh)

    # Fluide 2
    v2 = fluide2.Q / (n * A)
    Re2 = fluide2.rho * v2 * Dh / fluide2.mu
    Pr2 = fluide2.mu * fluide2.cp / fluide2.lambda_
    Nu2 = _nusselt(Re2, Pr2, angle)
    h2 = _h(Nu2, fluide2.lambda_, Dh)

    H_calc = _H_global(h1, h2, geo.e, geo.lambda_paroi, process.R_enc_fluide1, process.R_enc_fluide2)
    erreur = abs(H_est - H_calc) / H_est
    converge = (erreur * 100) < process.seuil_convergence

    return ResultatIteration(
        numero=numero, H_est=H_est, S=S, N=N, n=n, A=A, Dh=Dh,
        v1=v1, Re1=Re1, Pr1=Pr1, Nu1=Nu1, h1=h1,
        v2=v2, Re2=Re2, Pr2=Pr2, Nu2=Nu2, h2=h2,
        H_calc=H_calc, erreur=erreur, converge=converge,
    )


def iterer(
    process: ParametresProcess,
    geo: GeometriePlaque,
    fluide1: ProprietesFlUide,
    fluide2: ProprietesFlUide,
    max_iterations: int = 50,
) -> ResultatFinal:
    resultat = ResultatFinal(process=process, geometrie=geo, fluide1=fluide1, fluide2=fluide2)
    H_est = process.H_est_initial

    for i in range(1, max_iterations + 1):
        res = _une_iteration(H_est, process, geo, fluide1, fluide2, i)
        resultat.iterations.append(res)
        if res.converge:
            resultat.converge = True
            break
        H_est = res.H_calc

    dernier = resultat.iterations[-1]
    resultat.n_iterations = len(resultat.iterations)
    resultat.H_global = dernier.H_calc
    resultat.S_finale = dernier.S
    resultat.N_plaques = dernier.N
    resultat.n_canaux = dernier.n

    resultat.delta_P_fluide1 = _perte_charge(fluide1, geo, dernier.Re1, dernier.v1)
    resultat.delta_P_fluide2 = _perte_charge(fluide2, geo, dernier.Re2, dernier.v2)

    return resultat
