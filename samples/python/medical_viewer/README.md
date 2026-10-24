# Prototype de visionneuse médicale (inspirée de syngo.via / AI-Rad Companion)

> **Avertissement** : prototype de recherche et de démonstration.
> Ce n'est **pas** un dispositif médical, il n'est ni validé ni certifié (CE / FDA)
> et ne doit pas servir au diagnostic.

Ce prototype open source reprend les grandes fonctions présentées par
Siemens Healthineers pour syngo.via et AI-Rad Companion. Il est écrit avec
OpenCV et NumPy et ne contient aucun code ni aucune ressource de Siemens.

| Fonction | syngo.via / AI-Rad Companion | Ce prototype |
|---|---|---|
| Lecture d'examens | DICOM, PACS | Série DICOM (dossier), `.npy` / `.npz` |
| Reconstruction MPR | Axial, coronal, sagittal | Les trois plans, avec correction de l'espacement des voxels et fenêtres soft / lung / bone |
| Rendu 3D | VRT, MIP | VRT (composition front-to-back, fonction de transfert, ombrage) et MIP, préréglages bone / soft / lung |
| Rotation | Auto-rotation, contrôle des angles de vue | Auto-rotation, azimut et élévation au clavier, export vidéo de la rotation |
| Segmentation automatique | Organes et os (IA) | Corps, poumons, os et lésions pulmonaires, par règles classiques (seuils HU, morphologie, composantes connexes 3D). Pas de réseau entraîné |
| Analyse des anomalies | Détection et mesure | Nodules dans le parenchyme pulmonaire : volume (mL), diamètre axial max., diamètre équivalent, densité moyenne (HU) |
| Rapport | Rapport structuré | `report.json` et `report.txt` |

## Installation

```bash
pip install numpy opencv-python pydicom   # opencv-python-headless suffit pour --export
```

## Utilisation

```bash
cd samples/python/medical_viewer

# Démo sur un fantôme thoracique synthétique (aucune donnée patient nécessaire)
python viewer.py

# Série DICOM (un dossier, sous-dossiers compris)
python viewer.py /chemin/vers/serie_ct/

# Volume NumPy en HU, axes (z, y, x), avec espacement en mm
python viewer.py volume.npy --spacing 2.5 0.8 0.8

# Sans écran (serveur, CI) : images, vidéo de rotation et rapport
python viewer.py /chemin/vers/serie_ct/ --export sortie/ --frames 36
```

### Commandes clavier

| Touche | Action |
|---|---|
| `Espace` | Activer ou désactiver l'auto-rotation |
| `a` / `d` | Tourner à gauche / à droite |
| `w` / `x` | Incliner vers le haut / vers le bas |
| `1` `2` `3` | VRT bone / soft / lung |
| `m` | MIP |
| `g` | Surfaces de la segmentation (poumons, os, lésions) |
| `j` / `k`, molette | Coupe axiale précédente / suivante |
| `l` | Fenêtre suivante (soft → lung → bone) |
| `o` | Afficher ou masquer la segmentation sur les coupes |
| `s` | Capture d'écran |
| `q` / `Échap` | Quitter |

## Architecture

```
volume.py        chargement DICOM / NumPy, fenêtrage, fantôme synthétique
segmentation.py  segmentation par règles, étiquetage 3D, mesures des lésions
rendering.py     MPR, ré-échantillonnage isotrope, rotation, VRT, MIP, surfaces
viewer.py        interface (OpenCV highgui), mode --export, rapport
test_medical_viewer.py  tests sur le fantôme (vérité terrain connue)
```

Pipeline :
1. Chargement de la série en unités Hounsfield (`RescaleSlope` / `RescaleIntercept`).
2. Tri des coupes selon la normale au plan d'image.
3. Segmentation coupe par coupe :
   - corps = plus grande composante > -500 HU, trous remplis ;
   - poumons = < -400 HU dans le corps ;
   - os = > 250 HU.
4. Détection des lésions : tissu mou entouré de parenchyme pulmonaire, puis fusion 3D des composantes et mesures.
5. Rendu 3D :
   - ré-échantillonnage isotrope ;
   - rotation par `cv.warpAffine` coupe par coupe ;
   - lancer de rayons parallèles avec fonction de transfert, opacité modulée par le gradient et éclairage diffus.

Sur le fantôme (lésion de rayon 8 mm, soit 2,14 mL), le prototype mesure 2,17 mL
et un diamètre équivalent de 16,1 mm.

```bash
python test_medical_viewer.py
```

## Limites et suite possible

- La segmentation par règles ne remplace pas un modèle entraîné et validé.
  Étape suivante : un modèle de segmentation (par ex. TotalSegmentator,
  MONAI) chargé via `cv.dnn` ou ONNX Runtime.
- Le rendu se fait sur le CPU avec NumPy (environ 0,2 s par image pour 160³ voxels).
  Pour l'interactif en haute résolution, il faut passer au GPU (VTK, OpenGL).
- Le prototype ne gère ni PACS / DICOMweb, ni l'anonymisation, ni la traçabilité.
- Un usage clinique demande un système qualité (ISO 13485, IEC 62304),
  une gestion des risques (ISO 14971) et un marquage CE (MDR) ou une autorisation FDA.
