# ⚡ BennyBets — Comparateur de Cotes & Détecteur d'Arbitrage (Surebets)

**BennyBets** est une application desktop Windows moderne et autonome permettant de surveiller et comparer en temps réel les cotes des bookmakers (notamment les principaux opérateurs français tels que **Winamax** et **Betclic**), d'identifier instantanément les meilleures cotes, et de détecter automatiquement les opportunités de profit garanti (**Surebets / Arbitrage**) et les anomalies de marché (**Value bets / Décalages de cotes**).

---

## 🌟 Fonctionnalités Clés

- **Données 100% Réelles (Zéro Simulation)** :
  - Scraping direct des flux réels et des états préchargés des bookmakers.
  - Couverture des matchs en direct (**Live**) et à venir (**Pré-match**).
- **Détecteur d'Arbitrage (Surebets)** :
  - Calcul mathématique strict de la somme des inverses des cotes ($\sum 1 / \text{odd}_i < 1.0$).
  - Calculateur interactif de répartition optimale des mises selon votre budget (ex: 100 €) pour garantir un bénéfice net quelle que soit l'issue de la rencontre.
- **Détecteur d'Anomalies & Value Bets** :
  - Identification des cotes qui s'écartent anormalement de la médiane du marché (ex: $+8\%$ ou $+15\%$ d'écart).
- **Liens Cliquables Directs** :
  - Chaque cote et chaque match dispose de liens directs ouvrant votre navigateur par défaut pour vérifier et placer votre pari immédiatement sans chercher manuellement.
- **Design Épuré, Compact & Ergonomique** :
  - Menu haut *sticky* toujours accessible avec filtres rapides (*Tous*, *Live*, *Surebets*, *Décalages*).
  - Barre de recherche instantanée par club, joueur ou compétition.
  - Fiche détaillée de match et calculateur de gains interactif.
- **Paramètres Personnalisables & Persistants (`settings.json`)** :
  - Choix de la taille de police (9 px à 18 px) pour un confort de lecture optimal.
  - Choix du thème graphique (**Dark Moderne**, **Midnight Blue**, **Light Épuré**).
  - Intervalle de rafraîchissement automatique paramétrable (10s, 30s, 60s ou manuel).
  - Possibilité d'ajouter vos propres **sources d'adresses de sites et flux JSON**.

---

## 🚀 Installation & Démarrage

### Prérequis
- Système d'exploitation : **Windows** (10 ou 11).
- Outil recommandé : [**uv**](https://astral.sh/uv) (gestionnaire Python ultra-rapide).

---

### Option 1 : Utilisation de l'Exécutable Autonome (Recommandé)
Vous n'avez pas besoin d'installer Python si vous utilisez l'exécutable autonome généré dans le dossier `dist/` :
1. Rendez-vous dans le dossier `dist/`.
2. Double-cliquez sur **`BennyBets.exe`**.
3. L'application se lance instantanément.

> **Note Git** : Conformément à la configuration du projet, le dossier `dist/` est inclus dans le suivi Git et peut être directement partagé ou distribué.

---

### Option 2 : Lancement en Mode Développement
Pour les développeurs souhaitant modifier le code ou exécuter l'application avec rechargement :

1. Ouvrez un terminal dans le répertoire du projet.
2. Double-cliquez sur **`dev.bat`** (ou tapez `.\dev.bat` dans PowerShell / CMD).
   - Ce script synchronise automatiquement les dépendances via `uv sync`.
   - Il lance ensuite l'application via `uv run python -m bennybets`.

---

## 🛠️ Compilation de l'Exécutable (.exe)

Pour régénérer l'exécutable autonome Windows :
1. Double-cliquez sur **`build.bat`**.
2. Le script exécute `PyInstaller` via `uv` et produit l'exécutable unique dans `dist\BennyBets.exe`.

---

## 📖 Guide d'Utilisation

### 1. Navigation & Filtrage
- **Sélecteur de Sport** : Choisissez entre Football ⚽, Tennis 🎾, ou Basketball 🏀.
- **Bouton ⚡ Live** : Isole uniquement les matchs en direct avec affichage des scores en temps réel.
- **Bouton 🔥 Surebets** : Filtre les rencontres offrant une opportunité d'arbitrage avec profit garanti.
- **Bouton 💎 Décalages** : Affiche les matchs présentant des écarts de cotes anormaux.
- **Recherche** : Tapez le nom d'un club (ex: `Real`, `PSG`, `Marseille`) pour filtrer instantanément la liste.

### 2. Parier et Vérifier les Cotes
- Cliquez directement sur n'importe quel bouton de cote dans le tableau pour ouvrir la page officielle du bookmaker.
- Cliquez sur le bouton **`📊 Détails`** pour afficher le comparatif détaillé et le **Calculateur de Surebet** :
  - Saisissez votre mise totale (ex: `100.00 €`).
  - L'application calcule automatiquement les mises à placer sur chaque issue pour garantir un gain net identique.
  - Des boutons directs **`Parier (Winamax) ↗`** ou **`Parier (Betclic) ↗`** vous redirigent sur le site exact.

### 3. Personnalisation (Bouton ⚙️)
Cliquez sur l'icône **⚙️** dans la barre supérieure pour :
- Modifier la taille de texte et le thème de couleur.
- Régler la fréquence d'actualisation en arrière-plan.
- Ajuster les seuils de détection des Value bets.
- Activer / désactiver des bookmakers ou ajouter vos propres URLs d'événements.
- Les préférences sont sauvegardées dans `settings.json` et rechargées à chaque ouverture.

---

## 🧪 Tests Automatisés

Le projet intègre une suite de tests unitaires couvrant les calculs financiers et la réconciliation des données :
```bash
uv run pytest
```

---

## ⚖️ Avertissement Légal
BennyBets est un outil d'analyse mathématique et d'information. Les paris sportifs comportent des risques financiers et d'addiction. Jouez de manière responsable.