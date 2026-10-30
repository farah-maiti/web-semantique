# PharmaOnto · Version 3.0.0

Projet Web Sémantique, ESPRIT, 5 TWIN, année universitaire 2026–2027.

**Équipe : Ahmed Saidani, Fedi Ben Khalifa, Farah Maiti.**

Le projet relie six spécialités françaises, leurs substances actives, des indications, des effets possibles et des contre-indications à cinq patients fictifs. Il comprend une ontologie OWL, une extension SWRL, un import RDFLib, des contrôles HermiT et SHACL, un serveur Fuseki et une application Django avec TALN spaCy.

## Nouveautés de la version 3

- **105 classes**, **9 racines**, **7 niveaux au maximum**, **34 classes définies**.
- **19 propriétés objet**, **8 propriétés de données**, **42 individus**.
- Familles pharmacologiques détaillées, formes et voie, états cliniques, effets et profils patients calculés.
- Explorateur de hiérarchie avec recherche, définitions et distinction entre appartenance déclarée et inférée.
- Dossiers des médicaments, navigation vers les classes et exports CSV.
- **16 requêtes SELECT** et **81 tests réussis**, avec Fuseki réel.

Exemple de branche : PrincipeActif → AntiInfectieux → Antibacterien → Antibiotique → BetaLactamine → Penicilline → PenicillineLargeSpectre. La profondeur compte la racine du domaine, sans owl:Thing. Amoxicilline est un individu de la dernière classe. Les deux spécialités contenant cet actif sont classées par HermiT dans la famille de médicaments correspondante.

La hiérarchie complète est dans `docs/HIERARCHIE_COMPLETE.txt`. Le dictionnaire des classes, avec parents, définitions et sources, est dans `data/taxonomy.json`. Les neuf racines sont disjointes ; les axes thérapeutique, réglementaire et pharmaceutique peuvent se recouvrir. Les seuils d’âge et le profil « plusieurs médicaments » sont des conventions pédagogiques documentées, pas des critères de décision médicale.

## Démarrage sous Windows

1. Extraire le ZIP dans un dossier accessible en écriture. Ne pas lancer les fichiers depuis WinRAR.
2. Vérifier que **Python 3.11** et un **JDK 17 ou plus récent** sont disponibles. `python --version`, `java -version` et `javac -version` doivent fonctionner. Protégé est nécessaire pour la démonstration graphique de l’ontologie.
3. Lancer `INSTALLER.cmd` une fois avec Internet. L’environnement Python est créé dans `.venv`. Fuseki 5.5.0 est inclus dans `vendor` et son empreinte est vérifiée. Sous Windows/Python 3.11, l’installation utilise les versions exactes de `requirements-lock-windows-py311.txt`.
4. Lancer `DEMARRER.cmd`. Le lanceur ouvre `http://127.0.0.1:8000`. Conserver sa console ouverte. Le fonctionnement de la démo ne nécessite plus Internet, sauf pour ouvrir les liens vers les fiches officielles.
5. Vérifier l’indicateur **Fuseki connecté**. `Ctrl+C` dans la console arrête les deux services.

Sur la machine où ce dossier a été préparé, `.venv` est déjà installé. Il est volontairement exclu du ZIP, car un environnement Python ne doit pas être déplacé tel quel entre machines.

Les ports 8000 et 3030 doivent être libres. Le lanceur refuse de reprendre un service inconnu qui les utilise. Il écoute uniquement sur la machine locale. Le serveur Django de développement convient à la soutenance locale, pas à un déploiement public.

## Fichiers à présenter

| Élément | Emplacement |
| --- | --- |
| Ontologie OWL 2 DL à ouvrir dans Protégé | `ontology/pharmaonto.owl` |
| Même modèle avec la règle SWRL | `ontology/pharmaonto-swrl.owl` |
| Format Turtle lisible | `ontology/pharmaonto.ttl` |
| Graphe utilisé par Fuseki | `ontology/pharmaonto-materialized.ttl` |
| Contraintes de complétude | `ontology/shapes.ttl` |
| Corpus et sources | `data/corpus.json` |
| Hiérarchie et définitions | `data/taxonomy.json` et `docs/HIERARCHIE_COMPLETE.txt` |
| 16 requêtes SELECT et 2 règles CONSTRUCT | `queries/` |
| Présentation avec notes de prise de parole | `docs/PharmaOnto_Presentation_Pro_v3.pptx` |
| Présentation PDF | `docs/PharmaOnto_Presentation_Pro_v3.pdf` |
| Rapport, installation et guide de soutenance | `docs/PharmaOnto_Rapport_Pro_v3.pdf` |
| Résultats et preuves | `validation/` |

Ouvrir **un seul des deux fichiers OWL à la fois** pour la démonstration. Les deux utilisent volontairement la même IRI d’ontologie et la version SWRL est autonome. Ne pas les importer l’un dans l’autre. Le graphe matérialisé sert à la recherche, pas à montrer quelles assertions étaient présentes avant raisonnement.

## Démonstration recommandée

1. Dans Protégé : ouvrir `pharmaonto.owl`, choisir HermiT dans le menu Reasoner, puis Start reasoner. Montrer `MedicamentAntiInflammatoire`, son équivalence, et l’individu `Advil_400` classé par inférence. Montrer l’inverse `DiabeteType2 estTraitePar Glucophage_850`.
2. Dans une autre ouverture : charger `pharmaonto-swrl.owl`, lancer HermiT et montrer `Advil_400 estContreIndiquePour Patient_P002` parmi les relations inférées. L’affichage de l’onglet SWRL dépend des extensions installées dans Protégé. La règle reste lisible dans le RDF/XML et dans le rapport.
3. Dans l’application : cliquer **Alertes du patient P002**. Résultat attendu : ADVIL 400 mg, avec le motif ulcère gastroduodénal en évolution et une source officielle.
4. Cliquer **Interactions du patient P004**. Résultat attendu : ADVIL 400 mg et COUMADINE 5 mg.
5. Consulter les génériques de Clamoxyl : AMOXICILLINE BGR 1 g. Afficher le SPARQL produit.
6. Explorer le graphe d’un patient et montrer les relations déduites en couleur.
7. Ouvrir **Ontologie et hiérarchie**, rechercher « pénicilline », puis afficher la définition de MedicamentPenicillineLargeSpectre et ses deux individus inférés. Ouvrir le dossier GLUCOPHAGE et naviguer vers ses classes.
8. Présenter les logs HermiT, SHACL et les tests. Expliquer pourquoi une référence manquante peut être cohérente en OWL mais invalide en SHACL.

L’équipe de trois membres est approuvée par l’encadrant, selon la confirmation reçue le 29 octobre 2026. Chacun doit pouvoir expliquer le modèle, ses requêtes et les choix de validation.

## Questions prises en charge

- Quels médicaments sont contre-indiqués pour le patient P002 ?
- Quelles interactions concernent le patient P004 ?
- Quels sont les effets secondaires du Glucophage ?
- Quels médicaments traitent le diabète de type 2 ?
- Quels sont les génériques de Clamoxyl ?
- Quels médicaments contiennent de la metformine ?
- Quels médicaments sont anti-inflammatoires ?
- Combien de médicaments par principe actif ?
- Avec quoi interagit la warfarine ?
- Liste des médicaments

Le TALN est **local, à règles et vocabulaire contrôlé**, avec `spaCy EntityRuler` et `Matcher`. Il ne s’agit pas d’un LLM ni d’un accès à une API générative. Il reconnaît des variantes lexicales, normalise les accents et construit des requêtes prédéfinies. Il refuse les négations non prévues, les demandes de posologie, les termes inconnus et plusieurs entités du même type. Aucune clé API n’est nécessaire.

## Validation et reconstruction

Les commandes suivantes se lancent depuis la racine du projet, avec l’environnement Python installé.

```powershell
.\.venv\Scripts\python.exe -m scripts.build_ontology
.\.venv\Scripts\python.exe -m scripts.reason
.\.venv\Scripts\python.exe -m webapp.queries
.\.venv\Scripts\python.exe -m pytest -q --disable-warnings --basetemp runtime\test-temp
```

`VALIDER.cmd` enchaîne ces commandes. La reconstruction remplace les exports générés. Modifier `data/corpus.json` pour les individus, `data/taxonomy.json` pour les classes et `scripts/build_ontology.py` pour les axiomes formels avant de reconstruire. Une modification manuelle de l’OWL ne sera pas conservée lors de la prochaine reconstruction.

Pour tester aussi le serveur Fuseki réel, le démarrer avec le graphe courant, puis dans une autre console PowerShell :

```powershell
$env:RUN_FUSEKI_TESTS = '1'
.\.venv\Scripts\python.exe -m pytest -q --disable-warnings --basetemp runtime\test-fuseki --junitxml=validation\tests.xml
```

Sans cette variable, le test d’intégration Fuseki est explicitement ignoré. La campagne livrée a exécuté ce test. Après toute reconstruction, redémarrer l’application et Fuseki pour recharger le graphe matérialisé et les caches du schéma.

HermiT est appelé via les classes Java incluses dans Owlready2. Le programme Java contrôle le profil OWL 2 DL, la cohérence et les classes insatisfiables, puis extrait les types et relations entre individus nommés. Le fichier SWRL est également exécuté par HermiT et ses alertes sont comparées avec la règle CONSTRUCT. Les tests automatisés ne commandent pas l’interface graphique de Protégé.

## Mode de secours

`DEMARRER_LOCAL.cmd` utilise RDFLib et le même fichier matérialisé sans démarrer Fuseki. L’interface indique **Mode local RDFLib**. Ce mode sert au diagnostic et au secours. Pour démontrer l’architecture complète du sujet, utiliser `DEMARRER.cmd`.

Sous Linux ou macOS : `python3 scripts/setup.py`, puis `.venv/bin/python -m scripts.serve`. Ces systèmes ne font pas partie de la campagne de test livrée. Les paquets non Windows sont résolus depuis `requirements.txt`.

## Portée des données

Les fiches officielles françaises ont été consultées le 29 octobre 2026. Les classifications complémentaires ont été revues le 30 octobre 2026 à partir des RCP et de l’index ATC du Centre collaborateur OMS. Les sources ATC justifient des familles de substances ; aucun import OWL externe ni code ATC de produit n’est ajouté automatiquement. Le JSON conserve la source de chaque spécialité, condition, contre-indication et association médicament-effet. Les champs conservés sont une sélection structurée, pas une copie complète des RCP. Les masses correspondent à la substance précisée, notamment les sels. Les données de remboursement et les codes CIM-10 du brouillon n’ont pas été reconduits sans cadrage documentaire suffisant.

Tous les patients sont fictifs. L’absence d’un résultat ou d’une alerte signifie seulement qu’aucun fait ou règle du corpus ne répond à la requête. Elle ne démontre pas qu’un traitement est sûr. Le projet ne calcule pas de posologie, ne prescrit aucun traitement et ne prétend pas à une validation clinique.

## Architecture du code

- `scripts/build_ontology.py` : schéma, import JSON, exports source et SWRL.
- `scripts/ValidateOntology.java` et `scripts/reason.py` : HermiT, matérialisation et comparaison des règles.
- `webapp/queries.py` : requêtes contrôlées et export des fichiers `.rq`.
- `webapp/nlp.py` : reconnaissance française, contrôle du vocabulaire et construction SPARQL.
- `webapp/semantic.py` : exécution Fuseki ou RDFLib explicitement choisie.
- `webapp/views.py` : API Django, validation des entrées et protection CSRF.
- `webapp/explorer.py` : hiérarchie issue de l’OWL, appartenances matérialisées et dossiers médicament.
- `webapp/static/` : interface accessible, tableaux, sources et graphe SVG.
- `tests/test_project.py` et `tests/test_ontology_upgrade.py` : tests positifs, négatifs, frontières d’âge, hiérarchie, API et intégration.

## Dépendances et licences

Fuseki 5.5.0 a été choisi pour sa compatibilité Java 17. L’archive officielle et son empreinte SHA-512 sont incluses dans `vendor`. Les fichiers LICENSE et NOTICE d’Apache sont conservés dans cette archive et lors de l’extraction. Les bibliothèques Python conservent leurs propres licences dans l’environnement installé. Aucun logiciel tiers n’est présenté comme une création de l’équipe.
