# État du projet — 2026-11-06

Dépôt : `ahralf81m/opencv` (fork d'OpenCV)
Branche de travail : `ccr-7add2bc2-qq3lk8`

> Ce document est un instantané factuel établi à partir du contenu du dépôt et de deux vérifications
> faites dans un conteneur Linux : une configuration CMake et une compilation partielle. Tout ce qui
> n'a pas été vérifié est signalé comme tel.

## 1. Résumé

- Le dépôt est un **fork non modifié d'OpenCV**. `master`, `origin/master` et la branche de travail
  pointent tous trois sur le même commit (`ca8c3dd9`), sans aucun commit propre au fork.
- Le code est **figé au 2021-03-22**, soit environ 5 ans et 7 mois avant la date de ce rapport. La
  version déclarée est **4.5.2-pre**, un développement antérieur à la release 4.5.2.
- Aucune synchronisation avec le dépôt amont n'est configurée : `origin` est le seul remote, il n'y a
  pas de remote `upstream`.
- Les modules `core` et `imgproc` **se configurent et se compilent** avec une chaîne d'outils actuelle
  (voir §5). Les autres modules n'ont pas été testés.

## 2. Identité du dépôt

| Élément | Valeur |
|---|---|
| Version (`version.hpp`) | 4.5.2, statut `-pre` |
| Dernier commit | `ca8c3dd9` — « Merge remote-tracking branch 'upstream/3.4' into merge-3.4 » |
| Date du dernier commit | 2021-03-22 (Alexander Alekhin) |
| Historique | 1 400 commits |
| Fichiers suivis | 6 759 |
| Taille | `.git` ≈ 93 Mo, copie de travail ≈ 195 Mo |
| Branches | `master`, `ccr-7add2bc2-qq3lk8` (locale et distante) |
| Commits en avance sur `master` | 0 (avant ce fichier) |
| Tags | aucun |
| Licence | fichiers `LICENSE` et `COPYRIGHT` présents à la racine |

## 3. Contenu du dépôt

### 3.1 Modules (`modules/`)

21 répertoires de modules. Nombre de fichiers suivis par module (sources et en-têtes / tests / tests de
performance) :

| Module | Src + include | Tests | Perf |
|---|---:|---:|---:|
| core | 315 | 43 | 33 |
| dnn | 312 | 25 | 9 |
| highgui | 280 | 3 | 0 |
| gapi | 207 | 98 | 24 |
| imgproc | 147 | 56 | 40 |
| videoio | 74 | 9 | 5 |
| calib3d | 65 | 35 | 8 |
| imgcodecs | 53 | 11 | 2 |
| features2d | 47 | 26 | 7 |
| video | 41 | 16 | 16 |
| flann | 40 | 3 | 0 |
| stitching | 32 | 10 | 7 |
| photo | 29 | 11 | 5 |
| ml | 20 | 14 | 0 |
| ts | 20 | 0 | 0 |
| objdetect | 13 | 5 | 5 |
| js | 5 | 13 | 36 |
| world | 3 | 0 | 0 |
| java, objc, python | 0 | 20 / 3 / 29 | 0 |

Remarques :
- `highgui`, `flann` et `ml` ont très peu de tests par rapport à leur volume de code.
- `dnn` compte 25 fichiers de test pour 312 fichiers de sources.
- `java`, `objc` et `python` sont des modules de bindings : aucun fichier n'est suivi sous `src/` ni
  `include/` (leur code vit ailleurs dans le module), seuls leurs tests sont comptés ici.

### 3.2 Autres répertoires

- `3rdparty/` : 20 sous-répertoires, parmi lesquels `ffmpeg`, `ippicv`, `libjpeg-turbo`, `libpng`,
  `libtiff`, `libwebp`, `openexr`, `openjpeg`, `protobuf`, `tbb`, `zlib`.
- `samples/` : exemples en C++ (234 fichiers), Python (135), `data` (113), WinRT (110), WP8 (102),
  Android (100), Java (87), `dnn` (70), Swift (65).
- `doc/`, `apps/`, `cmake/`, `platforms/`, `include/`, `data/` (39 fichiers suivis).

### 3.3 Langages (fichiers suivis par extension)

C++ : 1 524 `.cpp`, 755 `.hpp`. C : 366 `.c`, 716 `.h`. Python : 306. Java : 199. OpenCL : 109 `.cl`.
CMake : 140. Documentation : 287 `.markdown`.

## 4. Activité

- Les commits dont la date de commit est postérieure au 2021-01-01 ont des dates d'auteur allant du
  2020-12-08 au 2021-03-22.
- 97 commits depuis le 2021-03-01, dont 63 par un même auteur (Alexander Alekhin). Cette activité vient
  de l'amont, pas du fork.
- Aucune activité propre au fork : pas de commit local, pas de branche de fonctionnalité, pas de tag.
- Nature des derniers changements : fusions de pull requests de l'amont (dont #19757, support de
  `setLogLevel()` / `getLogLevel()` en JavaScript, et #19632, cible ARM pour l'inférence).

## 5. Vérifications effectuées

Environnement : Linux, CMake 3.28.3, Ninja, GCC / G++ 13.3.0, Python 3 présent, 4 cœurs.

| Vérification | Résultat |
|---|---|
| Configuration CMake (`core` et `imgproc` seuls, sans tests, sans IPP ni OpenCL ni Java ni Python) | Réussie en 23,6 s |
| Compilation de `core` + `imgproc` (224 étapes Ninja, `-j4`) | Réussie en 1 min 54 s, 0 avertissement relevé |
| Compilation des autres modules (`dnn`, `gapi`, `videoio`, `highgui`, etc.) | **Non testée** |
| Compilation des tests et tests de performance | **Non testée** |
| Exécution des tests | **Non testée** |
| Bindings Python et Java | **Non testés** |
| Options optionnelles (IPP, OpenCL, CUDA, FFmpeg système, GUI) | **Non testées** |

Lecture prudente du résultat : une base de 2021 compile sur GCC 13 pour deux modules, ce qui est
encourageant, mais cela ne dit rien des modules plus exposés aux changements de compilateur et de
bibliothèques (notamment `dnn`, `gapi` et les bindings).

## 6. Intégration continue

Un seul workflow GitHub Actions : `.github/workflows/arm64-build-checks.yml`.
- Déclenchement : manuel uniquement (`workflow_dispatch`).
- Exécuteur : `ubuntu-18.04`, une image que GitHub a retirée. Le workflow ne peut donc plus s'exécuter
  tel quel.
- Il cible Python 2.7 et Python 3.6 et clone `opencv_contrib` en `--depth 1`, donc sans le figer sur une
  version cohérente avec ce dépôt.

Il n'y a aucune CI automatique (push ou pull request) active sur ce fork.

## 7. Risques et points d'attention

1. **Âge du code.** Plus de cinq ans de correctifs, notamment de sécurité, d'évolutions de dépendances
   et de compatibilité avec les compilateurs et systèmes récents, ne sont pas présents. Consulter
   `SECURITY.md` et les avis publiés par l'amont avant tout usage en production.
2. **Dépendances embarquées figées.** Les bibliothèques de `3rdparty/` (images, zlib, protobuf 3.5.1,
   FFmpeg, etc.) sont celles de mars 2021. Il faut les considérer comme potentiellement vulnérables
   tant qu'elles ne sont pas auditées.
3. **Pas de lien avec l'amont.** Sans remote `upstream`, aucune mise à jour n'est possible sans
   configuration préalable.
4. **CI inutilisable** (§6) : rien ne détecte aujourd'hui une régression.
5. **Contenu de `opencv_contrib` absent.** Le dépôt ne contient que le noyau ; tout ce qui vient de
   `opencv_contrib` est à récupérer séparément, avec une version cohérente.
6. **Objectif du fork non documenté.** Le `README.md` est celui de l'amont et aucun fichier ne dit
   pourquoi ce fork existe ni ce qu'on attend de lui.

## 8. Décisions à prendre

| Question | Options |
|---|---|
| Quel est le but du fork ? | Travailler à partir de ce snapshot, ou repartir d'une version récente de l'amont |
| Faut-il rattraper l'amont ? | Ajouter un remote `upstream`, puis fusionner ou rebaser vers une release récente |
| Quel périmètre de build ? | Définir la liste des modules et options réellement utilisés, puis les valider tous |
| Quelle CI ? | Remplacer le workflow ARM64 obsolète par un workflow Linux sur un exécuteur actuel |

## 9. Prochaines étapes proposées

1. Confirmer l'objectif du fork et l'ajouter au `README.md`.
2. Ajouter le remote `upstream` (`https://github.com/opencv/opencv`) et mesurer l'écart avec l'amont.
3. Compiler l'ensemble des modules visés et lancer les tests de base (`opencv_test_core`,
   `opencv_test_imgproc`), puis consigner les résultats ici.
4. Remettre en place une CI minimale (configuration et compilation sur un exécuteur supporté).
5. Auditer ou mettre à jour les dépendances de `3rdparty/` selon les besoins du projet.

## 10. Limites de ce rapport

- Le dépôt ne contient aucun journal de décisions, ticket ou feuille de route : l'objectif du fork et
  son avancement ne sont pas lisibles, et ce rapport ne s'appuie que sur le code et l'historique git.
- L'écart exact avec l'amont actuel n'a pas été mesuré : le conteneur n'avait pas de remote `upstream`
  configuré.
- Les chiffres du §3 sont des comptages de fichiers suivis par git (`git ls-files`), pas des lignes de
  code.
