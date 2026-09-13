# Guide et Spécifications pour l\'Agent de Développement - BennyBets

Ce document consigne l\'ensemble des règles, décisions architecturales, stack technique, conventions et historique des tâches du projet **BennyBets**.
Tout agent intervenant sur ce projet doit respecter les directives décrites ici.

---

## 1. Objectif du Projet
**BennyBets** est une application desktop Windows autonome (avec exécutable final dans dist/ conservé dans Git) permettant de :
1. **Comparer les cotes en direct** entre plusieurs bookmakers (focus bookmakers français agréés ANJ : Winamax, Betclic, etc.).
2. **Couvrir principalement le Football**, mais avec une conception extensible à d\'autres sports (Tennis, Basketball...).
3. **Identifier automatiquement les meilleures cotes** parmi tous les sites surveillés.
4. **Détecter les anomalies de cotes et décalages importants** :
   - Surebets (arbitrage avec profit mathématiquement garanti, somme des inverses < 1.0).
   - Value bets / décalages majeurs (écarts anormaux par rapport au consensus marché / médiane).
5. **Support du temps réel (Live match)** et de la pré-rencontre.
6. **Sources de données réelles (zéro simulation)** : scraping d\'APIs publiques / endpoints JSON internes des bookmakers sans clé payante requise.
7. **Liens directs cliquables** : ouverture du navigateur vers l\'événement exact sur le site du bookmaker pour vérification et pari immédiat.
8. **Personnalisation utilisateur** :
   - Paramètres sauvegardés (settings.json).
   - Thèmes (Sombre moderne, Bleu nuit, Clair).
   - Taille de police configurable pour accessibilité.
   - Seuils d\'alerte d\'anomalies et activation/désactivation de sources.
   - Possibilité d\'ajouter des sources et URLs personnalisées.

---

## 2. Stack Technique & Environnement
- **OS cible** : Windows.
- **Gestionnaire d\'environnement & paquets** : uv (ultra-rapide, commandes uv run, uv add).
- **Python** : 3.11 / 3.12.
- **GUI Framework** : PyQt6 (haute performance, styles QSS réactifs, tables de cotes denses, dialogue de paramètres modal, gestion de threads asynchrones QThread/pyqtSignal).
- **Réseau / Scraping** : httpx (requêtes rapides avec gestion des en-têtes réalistes et sessions).
- **Packaging** : pyinstaller via uild.bat produisant dist/BennyBets.exe autonome.
- **Tests** : pytest pour les algorithmes financiers (ROI, calcul de mises, surebet, consensus de cotes, normalisation de noms d\'équipes).
- **Scripts d\'exécution** :
  - dev.bat : lance l\'application en mode développement (uv run python -m bennybets.main).
  - uild.bat : package l\'exécutable autonome dans dist/ (uv run pyinstaller ...).

---

## 3. Architecture Modulaire
L\'application suit une architecture hautement découplée et agnostique :
`
bennybets/
│
├── core/                   # Logique métier pure, sans dépendance GUI
│   ├── models.py           # Dataclasses (Sport, Event, Market, Odd, Opportunity, OpportunityType)
│   ├── normalizer.py       # Normalisation & fuzzy matching des noms d\'équipes (ex: PSG = Paris SG)
│   ├── analyzer.py         # Moteur de détection de Surebets (Arbitrage), Meilleures Cotes & Anomalies / Value Bets
│   └── settings.py         # Gestionnaire de configuration persistant (settings.json)
│
├── providers/              # Fournisseurs de données (Scrapers / APIs)
│   ├── base.py             # Classe abstraite BaseProvider (interface standardisée)
│   ├── winamax.py          # Provider Winamax (scraping state JSON temps réel, live & prematch)
│   ├── betclic.py          # Provider Betclic (scraping ng-state JSON temps réel)
│   ├── custom_url.py       # Provider pour sources personnalisées définies par l\'utilisateur
│   └── registry.py         # Gestionnaire dynamique des providers actifs
│
├── ui/                     # Interface Graphique PyQt6
│   ├── main_window.py      # Fenêtre principale (Header sticky, barre d\'outils, filtres, table)
│   ├── odds_table.py       # Tableau compact de comparaison des cotes, liens cliquables et badges
│   ├── detail_dialog.py    # Modale détaillée par match avec calculateur de mise Surebet
│   ├── settings_dialog.py  # Modale des paramètres (police, thèmes, seuils, sources)
│   ├── theme.py            # Styles QSS (Thème sombre moderne épuré, Midnight, Clair)
│   └── worker.py           # Thread d\'arrière-plan pour le scraping sans bloquer l\'UI
│
├── tests/                  # Tests unitaires automatisés
│   ├── test_normalizer.py  # Tests de réconciliation des équipes
│   ├── test_analyzer.py    # Tests mathématiques arbitrage & détection d\'anomalies
│   └── test_providers.py   # Tests des structures de données des providers
│
├── main.py                 # Point d\'entrée de l\'application
├── settings.json           # Fichier de configuration utilisateur par défaut
├── dev.bat                 # Script batch pour lancer en dev
├── build.bat               # Script batch pour générer le .exe autonome
├── .gitignore              # Ignore venv/build mais conserve EXPLICITEMENT dist/
├── README.md               # Guide utilisateur complet
└── AGENTS.md               # Ce document
`

---

## 4. Conventions & Règles de Développement
1. **Zéro simulation de cotes** : Les cotes proviennent des flux réels des bookmakers.
2. **Agnostique et Remplaçable** : Tout provider peut être activé/désactivé ou remplacé sans casser le reste.
3. **UI Compacte et Epurée** :
   - Pas de grands espaces vides inutiles ni de headers gigantesques.
   - Icônes et boutons compacts.
   - Menu sticky en haut toujours accessible.
   - Popups fermables en cliquant en dehors pour les détails et réglages.
4. **Liens cliquables** : Clic sur une cote ou sur l\'icône bookmaker ouvre l\'URL dans le navigateur par défaut de l\'utilisateur (QDesktopServices.openUrl).
5. **Gestion Git** : Le dossier dist/ **ne doit pas** être ignoré par Git afin de pouvoir partager le .exe directement.