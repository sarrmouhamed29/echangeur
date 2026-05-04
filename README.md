# Dimensionnement Échangeur à Plaques FP22

Outil de dimensionnement d'un échangeur à plaques FP22 développé en Python / Streamlit.  
Il reproduit le calcul itératif sur le coefficient global H, avec export PDF et Excel.

---

## Prérequis

- **Python 3.10 ou supérieur** — téléchargeable sur https://www.python.org/downloads/  
  ⚠️ Lors de l'installation, cocher **"Add Python to PATH"**

---

## Installation (à faire une seule fois)

### 1. Télécharger le projet

Copier le dossier `code/` sur votre machine.

### 2. Ouvrir un terminal dans le dossier

- Sous Windows : clic droit dans le dossier → **"Ouvrir dans le terminal"**  
  (ou chercher **PowerShell** dans le menu Démarrer, puis naviguer avec `cd "chemin\vers\code"`)

### 3. Créer l'environnement virtuel

```powershell
python -m venv venv
```

### 4. Activer l'environnement virtuel

```powershell
.\venv\Scripts\Activate.ps1
```

> Si vous obtenez une erreur de politique d'exécution, lancez d'abord :
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> puis relancez la commande d'activation.

### 5. Installer les dépendances

```powershell
pip install -r requirements.txt
```

---

## Lancer l'application

À chaque utilisation, ouvrez un terminal dans le dossier et exécutez :

```powershell
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

L'application s'ouvre automatiquement dans votre navigateur à l'adresse :  
**http://localhost:8501**

---

## Utilisation

1. **Renseigner les paramètres** dans le formulaire central :
   - Données process (puissance, DTLM, nombre de passes…)
   - Géométrie de la plaque FP22 (surface, gap, angle de corrugation…)
   - Propriétés des deux fluides (sélection dans la bibliothèque ou saisie manuelle)

2. **Cliquer sur "Lancer le calcul"**

3. **Consulter les résultats** dans les 3 onglets :
   - Résultats détaillés (tableau des itérations)
   - Courbe de convergence
   - Pertes de charge

4. **Exporter** les résultats en Excel ou PDF via les boutons en bas de page

---

## Structure du projet

```
code/
├── app.py                  # Application principale (interface Streamlit)
├── requirements.txt        # Liste des dépendances Python
├── echangeur/
│   ├── calcul.py           # Moteur de calcul itératif
│   ├── modele.py           # Structures de données
│   ├── fluides.py          # Bibliothèque de fluides prédéfinis
│   └── export.py           # Génération PDF et Excel
└── venv/                   # Environnement virtuel (créé à l'installation)
```

---

## Dépendances

| Package | Rôle |
|---|---|
| streamlit | Interface web |
| plotly | Graphiques interactifs |
| openpyxl | Export Excel |
| fpdf2 | Export PDF |
| pandas | Tableaux de données |
| numpy | Calculs numériques |
