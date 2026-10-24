'''
Rule-based automatic segmentation of CT volumes and lesion measurement.

Labels: 1 body, 2 lungs, 3 bone, 4 lesion (soft-tissue nodule inside the lungs).
This is classical image processing (thresholds, morphology, connected
components), not a trained AI model, and it is not validated for clinical use.
'''

from __future__ import print_function

import numpy as np
import cv2 as cv

BODY, LUNG, BONE, LESION = 1, 2, 3, 4
LABEL_NAMES = {BODY: 'body', LUNG: 'lungs', BONE: 'bone', LESION: 'lesion'}
LABEL_COLORS = {BODY: (90, 160, 220), LUNG: (230, 170, 60), BONE: (235, 235, 235), LESION: (40, 40, 240)}  # BGR

KERNEL = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))


def fill_holes(mask):
    '''Fill the regions of a 2D 0/1 mask that are not connected to the image border.'''
    h, w = mask.shape
    canvas = np.zeros((h + 2, w + 2), np.uint8)
    canvas[1:-1, 1:-1] = mask
    ff_mask = np.zeros((h + 4, w + 4), np.uint8)
    cv.floodFill(canvas, ff_mask, (0, 0), 2)
    return (canvas[1:-1, 1:-1] != 2).astype(np.uint8)


def largest_component(mask):
    n, labels, stats, _ = cv.connectedComponentsWithStats(mask, connectivity=8)
    if n <= 1:
        return np.zeros_like(mask)
    best = 1 + int(np.argmax(stats[1:, cv.CC_STAT_AREA]))
    return (labels == best).astype(np.uint8)


def remove_small(mask, min_area):
    n, labels, stats, _ = cv.connectedComponentsWithStats(mask, connectivity=8)
    keep = np.zeros(n, np.uint8)
    keep[1:] = stats[1:, cv.CC_STAT_AREA] >= min_area
    return keep[labels]


def label_3d(mask):
    '''6/8-connected 3D labelling: 2D components per slice, merged across slices by overlap.'''
    Z = mask.shape[0]
    labels = np.zeros(mask.shape, np.int32)
    offset = 0
    for z in range(Z):
        n, lab = cv.connectedComponents(mask[z], connectivity=8, ltype=cv.CV_32S)
        lab[lab > 0] += offset
        labels[z] = lab
        offset += n - 1
    parent = np.arange(offset + 1)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for z in range(1, Z):
        both = (labels[z] > 0) & (labels[z - 1] > 0)
        if not both.any():
            continue
        for a, b in np.unique(np.stack([labels[z][both], labels[z - 1][both]], 1), axis=0):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    roots = np.array([find(i) for i in range(offset + 1)])
    _, compact = np.unique(roots, return_inverse=True)
    return compact[labels].astype(np.int32), int(compact.max())


def segment(volume, min_lesion_ml=0.03):
    '''Return (label volume uint8, list of lesion measurements).'''
    hu = volume.data
    Z = hu.shape[0]
    dz, dy, dx = volume.spacing
    px_mm2 = dy * dx
    labels = np.zeros(hu.shape, np.uint8)
    lung_region = np.zeros(hu.shape, np.uint8)

    for z in range(Z):
        s = hu[z]
        body = (s > -500).astype(np.uint8)
        body = largest_component(cv.morphologyEx(body, cv.MORPH_OPEN, KERNEL))
        body = fill_holes(body)
        if not body.any():
            continue
        lung = ((s < -400) & (body > 0)).astype(np.uint8)
        lung = remove_small(cv.morphologyEx(lung, cv.MORPH_OPEN, KERNEL), int(25.0 / px_mm2) + 1)
        bone = ((s > 250) & (body > 0)).astype(np.uint8)
        bone = remove_small(cv.morphologyEx(bone, cv.MORPH_CLOSE, KERNEL), 2)

        labels[z][body > 0] = BODY
        labels[z][lung > 0] = LUNG
        labels[z][bone > 0] = BONE
        # soft-tissue structures fully enclosed by lung parenchyma are nodule candidates
        lung_region[z] = (fill_holes(lung) > 0) & (lung == 0) & (s > -300)

    lesions = []
    comp, n = label_3d(lung_region)
    for i in range(1, n + 1):
        m = comp == i
        count = int(m.sum())
        vol_ml = count * volume.voxel_ml
        if vol_ml < min_lesion_ml:
            continue
        labels[m] = LESION
        zz, yy, xx = np.nonzero(m)
        max_axial = 0.0
        for z in np.unique(zz):
            pts = np.stack([xx[zz == z] * dx, yy[zz == z] * dy], 1).astype(np.float32)
            (w, h) = cv.minAreaRect(pts)[1] if len(pts) > 2 else (0, 0)
            max_axial = max(max_axial, max(w, h) + min(dx, dy))
        lesions.append({
            'id': len(lesions) + 1,
            'volume_ml': round(vol_ml, 3),
            'equivalent_diameter_mm': round(2.0 * (3.0 * vol_ml * 1000.0 / (4.0 * np.pi)) ** (1.0 / 3.0), 1),
            'max_axial_diameter_mm': round(max_axial, 1),
            'mean_hu': round(float(hu[m].mean()), 1),
            'centroid_voxel': [int(round(zz.mean())), int(round(yy.mean())), int(round(xx.mean()))],
            'slices': [int(zz.min()), int(zz.max())],
        })
    return labels, lesions


def organ_stats(volume, labels):
    stats = {}
    for lab, name in LABEL_NAMES.items():
        m = labels == lab
        if lab == BODY:
            m = labels > 0
        count = int(m.sum())
        stats[name] = {
            'volume_ml': round(count * volume.voxel_ml, 1),
            'mean_hu': round(float(volume.data[m].mean()), 1) if count else None,
        }
    return stats
