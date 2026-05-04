import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from echangeur.modele import ProprietesFlUide, GeometriePlaque, ParametresProcess
from echangeur.fluides import get_noms_fluides, get_fluide
from echangeur.calcul import iterer
from echangeur.export import generer_buffer_excel, generer_buffer_pdf, generer_buffer_documentation
from echangeur.catalogue import get_frames, get_spec, MATERIAUX

st.set_page_config(
    page_title="Dimensionnement Échangeur FP22",
    page_icon="🔥",
    layout="wide",
)


# ──────────────────────────── FORMULES (réutilisable) ────────────────────────────

def _afficher_formules():
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### Coefficient global H")
        st.latex(r"\frac{1}{H} = \frac{1}{h_1} + \frac{1}{h_2} + \frac{e}{\lambda_{paroi}} + R_{enc,1} + R_{enc,2}")

        st.markdown("##### Corrélation de Nusselt")
        st.latex(r"Nu = a \cdot Re^{\,b} \cdot Pr^{0{,}33}")
        st.caption("Coefficients a et b selon l'angle β et Re :")
        st.dataframe(pd.DataFrame([
            {"Angle β (°)": "< 30",  "Re"       : "< 10",      "a": 0.718, "b": 0.349},
            {"Angle β (°)": "< 30",  "Re"       : "> 10",      "a": 0.348, "b": 0.663},
            {"Angle β (°)": "45",    "Re"       : "< 10",      "a": 0.718, "b": 0.349},
            {"Angle β (°)": "45",    "Re"       : "10 – 100",  "a": 0.400, "b": 0.598},
            {"Angle β (°)": "45",    "Re"       : "> 100",     "a": 0.300, "b": 0.663},
            {"Angle β (°)": "50",    "Re"       : "< 20",      "a": 0.630, "b": 0.333},
            {"Angle β (°)": "50",    "Re"       : "20 – 300",  "a": 0.291, "b": 0.591},
            {"Angle β (°)": "50",    "Re"       : "> 300",     "a": 0.130, "b": 0.732},
            {"Angle β (°)": "60",    "Re"       : "< 20",      "a": 0.562, "b": 0.326},
            {"Angle β (°)": "60",    "Re"       : "20 – 400",  "a": 0.306, "b": 0.529},
            {"Angle β (°)": "60",    "Re"       : "> 400",     "a": 0.108, "b": 0.703},
            {"Angle β (°)": "> 65",  "Re"       : "< 20",      "a": 0.562, "b": 0.326},
            {"Angle β (°)": "> 65",  "Re"       : "20 – 500",  "a": 0.331, "b": 0.503},
            {"Angle β (°)": "> 65",  "Re"       : "> 500",     "a": 0.087, "b": 0.718},
        ]), hide_index=True, use_container_width=True)

    with c2:
        st.markdown("##### Coefficient d'échange convectif h")
        st.latex(r"h = \frac{Nu \cdot \lambda}{D_h}")

        st.markdown("##### Diamètre hydraulique")
        st.latex(r"D_h = \frac{4 \cdot b \cdot l}{2\,(b + l)}")

        st.markdown("##### Pertes de charge — Darcy-Weisbach")
        st.latex(r"\Delta P = f \cdot \frac{L}{D_h} \cdot \frac{\rho\, v^2}{2}")
        st.caption("Facteur de frottement f = C · Re^n selon la géométrie :")
        st.dataframe(pd.DataFrame([
            {"Géométrie"  : "Lisse",     "Re"         : "< 2 000",       "C": 24.000, "n": -1.000},
            {"Géométrie"  : "Lisse",     "Re"         : "> 2 000",       "C":  0.079, "n": -0.250},
            {"Géométrie"  : "α = 30°",   "Re"         : "40 – 500",      "C": 23.330, "n": -0.809},
            {"Géométrie"  : "α = 30°",   "Re"         : "500 – 17 000",  "C":  0.557, "n": -0.211},
            {"Géométrie"  : "α = 60°",   "Re"         : "20 – 140",      "C": 47.450, "n": -0.680},
            {"Géométrie"  : "α = 60°",   "Re"         : "140 – 4 500",   "C":  3.917, "n": -0.175},
            {"Géométrie"  : "α = 90°",   "Re"         : "40 – 180",      "C": 63.800, "n": -0.809},
            {"Géométrie"  : "α = 90°",   "Re"         : "180 – 700",     "C":  4.820, "n": -0.312},
        ]), hide_index=True, use_container_width=True)

        st.markdown("##### Nombre de canaux par passe")
        st.latex(r"n = \frac{N - 1}{2 \cdot n_p}")
        st.caption("N = nombre de plaques,  nₚ = nombre de passes")

# ──────────────────────────── SESSION STATE ────────────────────────────

if "resultat" not in st.session_state:
    st.session_state.resultat = None

noms = get_noms_fluides()

frames = get_frames()
mats   = list(MATERIAUX.keys())

# Valeurs par défaut (utilisées uniquement à la première visite)
_DEFAULTS = dict(
    P=36551.0, DTLM=8.96, H_init=500.0, seuil=5, nb_passes=1,
    sel_frame="FP 22", sel_mat=mats[0],
    s=0.21, b=0.0023, l=0.31, e=0.0006, lp=16.0, angle=45.0,
    R1=0.001, R2=0.0009,
    sel1=noms[1], sel2=noms[4],
)
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Callbacks ────────────────────────────────────────────────────

def _sync_fluide(prefix, sel_key):
    fl = get_fluide(st.session_state[sel_key])
    st.session_state[f"Q{prefix}"]   = fl.Q
    st.session_state[f"rho{prefix}"] = fl.rho
    st.session_state[f"mu{prefix}"]  = fl.mu
    st.session_state[f"cp{prefix}"]  = float(fl.cp)
    st.session_state[f"lf{prefix}"]  = fl.lambda_

def _sync_echangeur():
    frame = st.session_state.sel_frame
    if frame == "Manuel":
        return
    spec = get_spec(frame)
    st.session_state.s   = spec.s
    st.session_state.b   = round(spec.b, 5)
    st.session_state.l   = spec.l
    st.session_state.e   = spec.e
    st.session_state.lp  = spec.lambda_paroi
    # Sync matériau vers inox par défaut si on change de frame
    st.session_state.sel_mat = mats[0]

def _sync_materiau():
    st.session_state.lp = MATERIAUX[st.session_state.sel_mat]

# Initialiser les champs fluides si pas encore en session state
for prefix, sel_key in [("1", "sel1"), ("2", "sel2")]:
    if f"Q{prefix}" not in st.session_state:
        _sync_fluide(prefix, sel_key)


def _lancer_calcul():
    fluide1 = ProprietesFlUide(
        nom=st.session_state.sel1,
        Q=st.session_state.Q1, rho=st.session_state.rho1,
        mu=st.session_state.mu1, cp=st.session_state.cp1,
        lambda_=st.session_state.lf1,
    )
    fluide2 = ProprietesFlUide(
        nom=st.session_state.sel2,
        Q=st.session_state.Q2, rho=st.session_state.rho2,
        mu=st.session_state.mu2, cp=st.session_state.cp2,
        lambda_=st.session_state.lf2,
    )
    frame = st.session_state.sel_frame
    max_pl = get_spec(frame).max_plaques if frame != "Manuel" else 9999
    geo = GeometriePlaque(
        s=st.session_state.s, b=st.session_state.b,
        l=st.session_state.l, e=st.session_state.e,
        lambda_paroi=st.session_state.lp,
        angle_chevrons=st.session_state.angle,
        max_plaques=max_pl,
    )
    process = ParametresProcess(
        P=st.session_state.P, DTLM=st.session_state.DTLM,
        H_est_initial=st.session_state.H_init,
        seuil_convergence=st.session_state.seuil,
        nombre_passes=st.session_state.nb_passes,
        R_enc_fluide1=st.session_state.R1,
        R_enc_fluide2=st.session_state.R2,
    )
    st.session_state.resultat = iterer(process, geo, fluide1, fluide2)


# ══════════════════════════════════════════════════════════════════
#  MODE A — Formulaire centré (aucun résultat encore)
# ══════════════════════════════════════════════════════════════════

if st.session_state.resultat is None:

    st.title("🔥 Dimensionnement Échangeur à Plaques FP22")
    st.caption("Renseignez les paramètres ci-dessous puis lancez le calcul")
    st.divider()

    _, form_col, _ = st.columns([0.5, 6, 0.5])

    with form_col:

        # ── Process
        st.markdown("#### ① Données process")
        c1, c2, c3 = st.columns(3)
        c1.number_input("Puissance P (W)", min_value=1.0, step=100.0, key="P")
        c2.number_input("DTLM (K)", min_value=0.1, step=0.1, key="DTLM")
        c3.number_input("H estimé initial (W/m²K)", min_value=10.0, step=10.0, key="H_init")
        c1, c2, c3 = st.columns(3)
        c1.slider("Seuil de convergence (%)", min_value=1, max_value=20, key="seuil")
        c2.number_input("Nombre de passes (np)", min_value=1, max_value=10, step=1, key="nb_passes")

        st.divider()

        # ── Géométrie
        st.markdown("#### ② Modèle d'échangeur & Géométrie")
        c1, c2, c3 = st.columns([3, 3, 2])
        c1.selectbox("Modèle catalogue", ["Manuel"] + frames, key="sel_frame",
                     on_change=_sync_echangeur)
        c2.selectbox("Matériau plaque", mats, key="sel_mat",
                     on_change=_sync_materiau)

        # Fiche info catalogue
        if st.session_state.sel_frame != "Manuel":
            sp = get_spec(st.session_state.sel_frame)
            c3.markdown(
                f"<div style='background:#EBF3FB;border-radius:6px;padding:8px 12px;font-size:0.82rem;margin-top:4px'>"
                f"<b>{sp.frame}</b><br>"
                f"s = {sp.s} m² &nbsp;|&nbsp; b = {round(sp.b*1000,2)} mm<br>"
                f"Max {sp.max_plaques} plaques &nbsp;|&nbsp; {sp.max_pression} bar<br>"
                f"Connexions {sp.connexions}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("**Paramètres géométriques** *(pré-remplis depuis le catalogue, modifiables)*")
        c1, c2, c3, c4 = st.columns(4)
        c1.number_input("Surface s (m²)", format="%.4f", key="s")
        c2.number_input("Gap b (m)", format="%.5f", key="b")
        c3.number_input("Largeur l (m)", format="%.4f", key="l")
        c4.number_input("Angle β (°)", min_value=1.0, max_value=89.0, step=1.0, key="angle",
                        help="<30 / 45 / 50 / 60 / >65")
        c1, c2, c3, c4 = st.columns(4)
        c1.number_input("Épais. paroi e (m)", format="%.5f", key="e")
        c2.number_input("λ paroi (W/mK)", key="lp")
        c3.number_input("R_enc fluide 1 (m²K/W)", format="%.4f", key="R1")
        c4.number_input("R_enc fluide 2 (m²K/W)", format="%.4f", key="R2")

        st.divider()

        # ── Fluides côte à côte
        st.markdown("#### ③ & ④ Propriétés des fluides")
        fl1_col, gap, fl2_col = st.columns([5, 0.3, 5])

        with fl1_col:
            st.markdown("**Fluide 1 — côté eau**")
            st.selectbox("Fluide 1", noms, key="sel1",
                         on_change=_sync_fluide, args=("1", "sel1"))
            cc1, cc2 = st.columns(2)
            cc1.number_input("Débit Q (m³/s)", format="%.6f", key="Q1")
            cc2.number_input("Masse vol. ρ (kg/m³)", key="rho1")
            cc1, cc2 = st.columns(2)
            cc1.number_input("Viscosité μ (Pa·s)", format="%.6f", key="mu1")
            cc2.number_input("cp (J/kgK)", key="cp1")
            st.number_input("Conductivité λ (W/mK)", format="%.4f", key="lf1")

        with fl2_col:
            st.markdown("**Fluide 2 — côté huile**")
            st.selectbox("Fluide 2", noms, key="sel2",
                         on_change=_sync_fluide, args=("2", "sel2"))
            cc1, cc2 = st.columns(2)
            cc1.number_input("Débit Q (m³/s)", format="%.6f", key="Q2")
            cc2.number_input("Masse vol. ρ (kg/m³)", key="rho2")
            cc1, cc2 = st.columns(2)
            cc1.number_input("Viscosité μ (Pa·s)", format="%.6f", key="mu2")
            cc2.number_input("cp (J/kgK)", key="cp2")
            st.number_input("Conductivité λ (W/mK)", format="%.4f", key="lf2")

        st.divider()
        with st.expander("📐 Formules & corrélations utilisées", expanded=False):
            _afficher_formules()

        st.divider()
        _, btn_col, _ = st.columns([2, 3, 2])
        with btn_col:
            if st.button("▶ Lancer le calcul", type="primary", use_container_width=True):
                with st.spinner("Calcul en cours..."):
                    _lancer_calcul()
                st.rerun()

    st.stop()


# ══════════════════════════════════════════════════════════════════
#  MODE B — Résultats (sidebar + main)
# ══════════════════════════════════════════════════════════════════

r = st.session_state.resultat

# ──────────────────────────── SIDEBAR ────────────────────────────

with st.sidebar:
    st.header("⚙️ Paramètres")

    with st.expander("① Process", expanded=False):
        st.number_input("Puissance P (W)", min_value=1.0, step=100.0, key="P")
        st.number_input("DTLM (K)", min_value=0.1, step=0.1, key="DTLM")
        st.number_input("H estimé initial (W/m²K)", min_value=10.0, step=10.0, key="H_init")
        st.slider("Seuil (%)", min_value=1, max_value=20, key="seuil")
        st.number_input("Nombre de passes (np)", min_value=1, max_value=10, step=1, key="nb_passes")

    with st.expander("② Modèle & Géométrie", expanded=False):
        st.selectbox("Modèle catalogue", ["Manuel"] + frames, key="sel_frame",
                     on_change=_sync_echangeur)
        st.selectbox("Matériau plaque", mats, key="sel_mat",
                     on_change=_sync_materiau)
        if st.session_state.sel_frame != "Manuel":
            sp = get_spec(st.session_state.sel_frame)
            st.caption(f"Max {sp.max_plaques} plaques · {sp.max_pression} bar · {sp.connexions}")
        st.number_input("Surface s (m²)", format="%.4f", key="s")
        st.number_input("Gap b (m)", format="%.5f", key="b")
        st.number_input("Largeur l (m)", format="%.4f", key="l")
        st.number_input("Épais. paroi e (m)", format="%.5f", key="e")
        st.number_input("λ paroi (W/mK)", key="lp")
        st.number_input("Angle β (°)", min_value=1.0, max_value=89.0, step=1.0, key="angle")
        st.number_input("R_enc fluide 1 (m²K/W)", format="%.4f", key="R1")
        st.number_input("R_enc fluide 2 (m²K/W)", format="%.4f", key="R2")

    with st.expander("③ Fluide 1", expanded=False):
        st.selectbox("Fluide 1", noms, key="sel1",
                     on_change=_sync_fluide, args=("1", "sel1"))
        st.number_input("Débit Q (m³/s)", format="%.6f", key="Q1")
        st.number_input("Masse vol. ρ (kg/m³)", key="rho1")
        st.number_input("Viscosité μ (Pa·s)", format="%.6f", key="mu1")
        st.number_input("cp (J/kgK)", key="cp1")
        st.number_input("Conductivité λ (W/mK)", format="%.4f", key="lf1")

    with st.expander("④ Fluide 2", expanded=False):
        st.selectbox("Fluide 2", noms, key="sel2",
                     on_change=_sync_fluide, args=("2", "sel2"))
        st.number_input("Débit Q (m³/s)", format="%.6f", key="Q2")
        st.number_input("Masse vol. ρ (kg/m³)", key="rho2")
        st.number_input("Viscosité μ (Pa·s)", format="%.6f", key="mu2")
        st.number_input("cp (J/kgK)", key="cp2")
        st.number_input("Conductivité λ (W/mK)", format="%.4f", key="lf2")

    st.divider()
    if st.button("▶ Recalculer", type="primary", use_container_width=True):
        with st.spinner("Calcul en cours..."):
            _lancer_calcul()
        st.rerun()
    if st.button("🔄 Nouvelle saisie", use_container_width=True):
        st.session_state.resultat = None
        st.rerun()


# ──────────────────────────── RÉSULTATS ────────────────────────────

st.title("🔥 Dimensionnement Échangeur à Plaques FP22")

if r.converge:
    st.success(f"✅ Convergé en **{r.n_iterations} itération(s)** — Seuil {st.session_state.seuil}%")
else:
    st.error(f"❌ Non convergé après {r.n_iterations} itérations.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("H global", f"{r.H_global:.1f} W/m²K")
col2.metric("Surface d'échange", f"{r.S_finale:.3f} m²")
col3.metric("Nombre de plaques", str(r.N_plaques))
col4.metric("Nombre d'itérations", str(r.n_iterations))

if r.geometrie and r.N_plaques > r.geometrie.max_plaques:
    st.warning(
        f"⚠️ **{r.N_plaques} plaques** calculées dépassent la limite catalogue "
        f"de **{r.geometrie.max_plaques} plaques** pour ce modèle. "
        f"Envisagez un modèle de plus grande capacité ou plusieurs unités en parallèle."
    )

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📊 Résultats détaillés", "📈 Convergence", "💧 Pertes de charge", "📐 Formules"])

# ── Tab 1
with tab1:
    data = []
    for it in r.iterations:
        data.append({
            "Itér.": it.numero,
            "H est. (W/m²K)": round(it.H_est, 2),
            "S (m²)": round(it.S, 4),
            "N plaques": it.N,
            "n canaux": it.n,
            f"h {r.fluide1.nom[:10]} (W/m²K)": round(it.h1, 1),
            f"h {r.fluide2.nom[:10]} (W/m²K)": round(it.h2, 1),
            "H calc. (W/m²K)": round(it.H_calc, 2),
            "Erreur (%)": round(it.erreur * 100, 2),
            "Convergé": "✅" if it.converge else "❌",
        })
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    st.subheader("Dernière itération — détail")
    dernier = r.iterations[-1]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{r.fluide1.nom}**")
        st.markdown(f"- Vitesse : `{dernier.v1:.4f}` m/s")
        st.markdown(f"- Reynolds : `{dernier.Re1:.1f}`")
        st.markdown(f"- Prandtl : `{dernier.Pr1:.2f}`")
        st.markdown(f"- Nusselt : `{dernier.Nu1:.2f}`")
        st.markdown(f"- h : `{dernier.h1:.1f}` W/m²K")
    with c2:
        st.markdown(f"**{r.fluide2.nom}**")
        st.markdown(f"- Vitesse : `{dernier.v2:.4f}` m/s")
        st.markdown(f"- Reynolds : `{dernier.Re2:.1f}`")
        st.markdown(f"- Prandtl : `{dernier.Pr2:.2f}`")
        st.markdown(f"- Nusselt : `{dernier.Nu2:.2f}`")
        st.markdown(f"- h : `{dernier.h2:.1f}` W/m²K")

# ── Tab 2
with tab2:
    iters = [it.numero for it in r.iterations]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=iters, y=[it.H_est for it in r.iterations], mode="lines+markers",
        name="H estimé", line=dict(color="#2E75B6", width=2), marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=iters, y=[it.H_calc for it in r.iterations], mode="lines+markers",
        name="H calculé", line=dict(color="#C00000", width=2, dash="dash"),
        marker=dict(size=8, symbol="diamond"),
    ))
    if r.converge:
        last = r.iterations[-1]
        fig.add_annotation(x=last.numero, y=last.H_calc,
                           text=f"Convergé\n{last.H_calc:.1f} W/m²K",
                           showarrow=True, arrowhead=2,
                           bgcolor="#C6EFCE", bordercolor="#70AD47")
    fig.update_layout(title="Convergence sur H global", xaxis_title="Itération",
                      yaxis_title="H global (W/m²K)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02),
                      template="plotly_white", height=420)
    st.plotly_chart(fig, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=iters, y=[it.erreur*100 for it in r.iterations],
                          marker_color="#2E75B6"))
    fig2.add_hline(y=st.session_state.seuil, line_dash="dash", line_color="red",
                   annotation_text=f"Seuil {st.session_state.seuil}%")
    fig2.update_layout(title="Erreur relative par itération",
                       xaxis_title="Itération", yaxis_title="Erreur (%)",
                       template="plotly_white", height=280)
    st.plotly_chart(fig2, use_container_width=True)

# ── Tab 3
with tab3:
    dernier = r.iterations[-1]
    c1, c2 = st.columns(2)
    with c1:
        st.metric(f"ΔP — {r.fluide1.nom}", f"{r.delta_P_fluide1:.1f} Pa",
                  f"{r.delta_P_fluide1/1e5:.4f} bar")
        regime1 = "Laminaire (Re < 2300)" if dernier.Re1 < 2300 else "Turbulent (Re ≥ 2300)"
        st.info(f"Régime : **{regime1}** | Re = {dernier.Re1:.1f}")
    with c2:
        st.metric(f"ΔP — {r.fluide2.nom}", f"{r.delta_P_fluide2:.1f} Pa",
                  f"{r.delta_P_fluide2/1e5:.4f} bar")
        regime2 = "Laminaire (Re < 2300)" if dernier.Re2 < 2300 else "Turbulent (Re ≥ 2300)"
        st.info(f"Régime : **{regime2}** | Re = {dernier.Re2:.1f}")

    st.divider()
    df_pdc = pd.DataFrame({
        "Fluide": [r.fluide1.nom, r.fluide2.nom],
        "Débit (m³/s)": [r.fluide1.Q, r.fluide2.Q],
        "Vitesse (m/s)": [round(dernier.v1, 4), round(dernier.v2, 4)],
        "Reynolds": [round(dernier.Re1, 1), round(dernier.Re2, 1)],
        "Prandtl": [round(dernier.Pr1, 2), round(dernier.Pr2, 2)],
        "ΔP (Pa)": [round(r.delta_P_fluide1, 1), round(r.delta_P_fluide2, 1)],
        "ΔP (bar)": [round(r.delta_P_fluide1/1e5, 5), round(r.delta_P_fluide2/1e5, 5)],
    })
    st.dataframe(df_pdc, use_container_width=True, hide_index=True)

# ── Tab 4
with tab4:
    _afficher_formules()

# ──────────────────────────── EXPORT ────────────────────────────

st.divider()
st.subheader("📥 Exporter les résultats")
ec1, ec2, ec3 = st.columns(3)
with ec1:
    st.download_button(
        label="⬇ Résultats Excel (.xlsx)",
        data=generer_buffer_excel(r),
        file_name="dimensionnement_FP22.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
with ec2:
    st.download_button(
        label="⬇ Résultats PDF",
        data=generer_buffer_pdf(r),
        file_name="dimensionnement_FP22.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
with ec3:
    st.download_button(
        label="⬇ Documentation PDF",
        data=generer_buffer_documentation(),
        file_name="documentation_FP22.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
