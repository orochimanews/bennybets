# Guide et Spécifications pour l'Agent de Développement - BennyBets

Ce document consigne l'ensemble des règles, décisions architecturales, stack technique, conventions et historique des tâches du projet **BennyBets**.
Tout agent intervenant sur ce projet doit respecter les directives décrites ici.

---

## 1. Objectif du Projet
**BennyBets** est une application desktop Windows autonome (avec exécutable final dans `dist/` conservé dans Git) permettant de :
1. **Comparer les cotes en direct** entre plusieurs bookmakers français agréés ANJ (**Winamax, Betclic, Unibet**).
2. **Couvrir principalement le Football**, mais avec une conception extensible à d'autres sports (Tennis, Basketball...).
3. **Identifier automatiquement les meilleures cotes** parmi tous les sites surveillés.
4. **Détecter les anomalies de cotes et décalages importants** :
   - **Surebets** (arbitrage avec profit mathématiquement garanti, somme des inverses < 1.0).
   - **Value bets / décalages majeurs** (écarts anormaux par rapport au consensus marché / médiane).
5. **Support du temps réel (Live match)** et de la pré-rencontre.
6. **Sources de données 100% réelles (zéro simulation)** : scraping d'APIs publiques / endpoints JSON internes des bookmakers sans clé payante requise.
7. **Liens directs cliquables** : ouverture du navigateur vers l'événement exact sur le site du bookmaker pour vérification et pari immédiat.
8. **Personnalisation utilisateur** :
   - Paramètres sauvegardés (`settings.json`).
   - Thèmes (Sombre moderne, Bleu nuit, Clair).
   - Taille de police configurable pour accessibilité.
   - Seuils d'alerte d'anomalies et activation/désactivation de sources.
   - Possibilité d'ajouter des sources et URLs personnalisées.

---

## 2. Stack Technique & Environnement
- **OS cible** : Windows.
- **Gestionnaire d'environnement & paquets** : `uv` (ultra-rapide, commandes `uv run`, `uv add`).
- **Python** : 3.11 / 3.12.
- **GUI Framework** : `PyQt6` (haute performance, styles QSS réactifs, tables de cotes denses, dialogue de paramètres modal, gestion de threads asynchrones `QThread`/`pyqtSignal`).
- **Réseau / Scraping** : `curl_cffi` (contournement transparent TLS/CloudFront impersonating `chrome120`), `httpx`, `urllib.request`.
- **Packaging** : `pyinstaller` via `build.bat` produisant `dist/BennyBets.exe` autonome.
- **Tests** : `pytest` pour les algorithmes financiers (ROI, calcul de mises, surebet, consensus de cotes, normalisation de noms d'équipes).
- **Scripts d'exécution** :
  - `dev.bat` : lance l'application en mode développement (`uv run python -m bennybets.main`).
  - `build.bat` : package l'exécutable autonome dans `dist/` (`uv run pyinstaller ...`).

---

## 3. Fournisseurs de Cotes Actifs (100% Réels)
1. **Winamax** (`bennybets/providers/winamax.py`) :
   - Extraction de `PRELOADED_STATE` via `curl_cffi` (impersonate chrome120) pour contourner les protections WAF CloudFront.
   - Fournit > 600 matchs réels avec cotes 1N2 et liens profonds.
2. **Betclic** (`bennybets/providers/betclic.py`) :
   - Parsing gRPC dans le script `ng-state` Angular Universal.
   - Cotes réelles, statut live, scores et liens de match.
3. **Unibet** (`bennybets/providers/unibet.py`) :
   - Interrogation directe de l'API Kambi d'Unibet (`eu-offering-api.kambicdn.com/offering/v2018/ub/listView/football.json`).
   - Fournit > 700 matchs réels avec cotes 1N2 décimales.
4. **CustomJsonProvider** (`bennybets/providers/custom_url.py`) :
   - Permet d'injecter n'importe quel flux JSON ou webhook d'adresses personnalisé via les paramètres.

---

## 4. Conventions & Règles de Développement
1. **Zéro simulation de cotes** : Les cotes proviennent des flux réels des bookmakers.
2. **Agnostique et Remplaçable** : Tout provider peut être activé/désactivé ou remplacé sans casser le reste.
3. **UI Compacte et Epurée** :
   - Pas de grands espaces vides inutiles ni de headers gigantesques.
   - Icônes et boutons compacts.
   - Menu sticky en haut toujours accessible.
   - Popups fermables en cliquant en dehors pour les détails et réglages.
4. **Liens cliquables** : Clic sur une cote ou sur l'icône bookmaker ouvre l'URL dans le navigateur par défaut de l'utilisateur (`QDesktopServices.openUrl`).
5. **Gestion Git** : Le dossier `dist/` **ne doit pas** être ignoré par Git afin de pouvoir partager le `.exe` directement.