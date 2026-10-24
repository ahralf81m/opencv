'''
Multi-planar reformatting (MPR) and 3D rendering: volume rendering technique
(VRT, front-to-back alpha compositing with a transfer function and shading)
and maximum intensity projection (MIP), from any azimuth / elevation.
'''

from __future__ import print_function

import numpy as np
import cv2 as cv

from volume import AIR_HU, apply_window

HU_MIN, HU_MAX = -1024, 3071

# Transfer functions: control points (HU, opacity per mm, BGR color)
PRESETS = {
    'bone': [(-1024, 0.0, (0, 0, 0)), (150, 0.0, (60, 90, 160)), (300, 0.25, (150, 200, 235)),
             (700, 0.6, (225, 240, 250)), (3071, 0.8, (255, 255, 255))],
    # used with gradient-modulated opacity: only tissue boundaries are visible
    'soft': [(-1024, 0.0, (0, 0, 0)), (-500, 0.0, (60, 90, 170)), (-200, 0.05, (90, 140, 220)),
             (20, 0.15, (90, 100, 220)), (100, 0.2, (120, 150, 235)), (300, 0.5, (210, 235, 250)),
             (3071, 0.8, (255, 255, 255))],
    # used on the lung / lesion / bone segmentation only
    'lung': [(-1024, 0.0, (0, 0, 0)), (-950, 0.0, (180, 150, 100)), (-850, 0.004, (230, 200, 150)),
             (-500, 0.01, (240, 220, 180)), (-300, 0.0, (0, 0, 0)), (-200, 0.3, (60, 60, 230)),
             (150, 0.6, (40, 40, 240)), (250, 0.0, (0, 0, 0)), (300, 0.02, (220, 220, 220)),
             (3071, 0.05, (255, 255, 255))],
}
GRADIENT_OPACITY = {'soft': (15.0, 80.0)}  # HU per voxel: (no opacity below, full opacity above)
LUNG_VIEW_LABELS = (2, 3, 4)  # lungs, bone, lesion


def build_lut(points):
    hu = np.arange(HU_MIN, HU_MAX + 1, dtype=np.float32)
    xs = [p[0] for p in points]
    opacity = np.interp(hu, xs, [p[1] for p in points]).astype(np.float32)
    color = np.stack([np.interp(hu, xs, [p[2][c] for p in points]) for c in range(3)], 1)
    return opacity, (color / 255.0).astype(np.float32)


def resample_isotropic(data, spacing, max_dim=160, nearest=False):
    '''Resample to cubic voxels (and at most max_dim voxels per axis) for rendering.'''
    Z, Y, X = data.shape
    dz, dy, dx = spacing
    extent = np.array([Z * dz, Y * dy, X * dx])
    iso = max(min(spacing), extent.max() / max_dim)
    nz, ny, nx = (int(n) for n in np.maximum(1, np.round(extent / iso)))
    if nearest:
        interp_xy = interp_z = cv.INTER_NEAREST
    else:
        interp_xy = cv.INTER_AREA if iso > min(dx, dy) else cv.INTER_LINEAR
        interp_z = cv.INTER_LINEAR
    xy = np.stack([cv.resize(data[z], (nx, ny), interpolation=interp_xy) for z in range(Z)])
    out = np.stack([cv.resize(np.ascontiguousarray(xy[:, y, :]), (nx, nz), interpolation=interp_z)
                    for y in range(ny)], 1)
    return np.ascontiguousarray(out), iso


def rotate(vol, azimuth, elevation, fill, interpolation=cv.INTER_LINEAR):
    '''Rotate a (Z, Y, X) volume about the vertical axis, then tilt it about the X axis.'''
    Z, Y, X = vol.shape
    out = np.empty_like(vol)
    M = cv.getRotationMatrix2D((X / 2.0, Y / 2.0), azimuth, 1.0)
    for z in range(Z):
        out[z] = cv.warpAffine(vol[z], M, (X, Y), flags=interpolation,
                               borderMode=cv.BORDER_CONSTANT, borderValue=fill)
    if elevation:
        M = cv.getRotationMatrix2D((Y / 2.0, Z / 2.0), -elevation, 1.0)
        for x in range(X):
            out[:, :, x] = cv.warpAffine(np.ascontiguousarray(out[:, :, x]), M, (Y, Z), flags=interpolation,
                                         borderMode=cv.BORDER_CONSTANT, borderValue=fill)
    return out


class Renderer(object):
    '''Renders an anterior view (looking along +Y) of the rotated volume.'''

    def __init__(self, volume, labels=None, max_dim=160):
        self.hu, self.voxel_mm = resample_isotropic(volume.data, volume.spacing, max_dim)
        self.labels = None
        if labels is not None:
            self.labels = resample_isotropic(labels, volume.spacing, max_dim, nearest=True)[0]
        self.luts = dict((k, build_lut(v)) for k, v in PRESETS.items())

    def mip(self, azimuth=0.0, elevation=0.0, window=(400, 1800)):
        rot = rotate(self.hu, azimuth, elevation, AIR_HU)
        img = apply_window(np.flipud(rot.max(axis=1)), *window)
        return cv.cvtColor(img, cv.COLOR_GRAY2BGR)

    def vrt(self, azimuth=0.0, elevation=0.0, preset='bone'):
        hu = self.hu
        if preset == 'lung' and self.labels is not None:
            hu = np.where(np.isin(self.labels, LUNG_VIEW_LABELS), hu, AIR_HU).astype(np.float32)
        rot = rotate(hu, azimuth, elevation, AIR_HU)
        idx = (np.clip(rot, HU_MIN, HU_MAX) - HU_MIN).astype(np.int32)
        opacity, color = self.luts[preset]
        alpha = 1.0 - np.power(1.0 - np.minimum(opacity, 0.999), self.voxel_mm)  # per-sample opacity
        grad = GRADIENT_OPACITY.get(preset)

        def sample(y, gradmag):
            a = alpha[idx[:, y, :]]
            if grad:
                a = a * np.clip((gradmag[:, y, :] - grad[0]) / (grad[1] - grad[0]), 0, 1)
            return a, color[idx[:, y, :]]
        return self._composite(rot, sample)

    def surfaces(self, azimuth=0.0, elevation=0.0, colors=None, hidden=(1,)):
        '''Shaded rendering of the segmentation labels (e.g. organs and lesions).'''
        if self.labels is None:
            raise ValueError('renderer was created without labels')
        rot_lab = rotate(self.labels, azimuth, elevation, 0, cv.INTER_NEAREST)
        lut_a = np.zeros(256, np.float32)
        lut_c = np.zeros((256, 3), np.float32)
        for lab, bgr in (colors or {}).items():
            if lab not in hidden:
                lut_a[lab] = 0.03 if lab == 2 else 0.95  # translucent lungs
                lut_c[lab] = np.array(bgr, np.float32) / 255.0
        shape_vol = (lut_a[rot_lab] > 0).astype(np.float32)
        return self._composite(shape_vol * 1000.0, lambda y, _: (lut_a[rot_lab[:, y, :]], lut_c[rot_lab[:, y, :]]))

    def _composite(self, field, sample):
        Z, Y, X = field.shape
        gz, gy, gx = np.gradient(cv.GaussianBlur(field.reshape(Z * Y, X), (3, 3), 0).reshape(Z, Y, X))
        gradmag = np.sqrt(gz * gz + gy * gy + gx * gx)
        light = np.array([0.35, -0.75, -0.55])  # from viewer side, slightly above and to the right
        light /= np.linalg.norm(light)
        diffuse = np.abs(gz * light[0] + gy * light[1] + gx * light[2]) / (gradmag + 1e-6)
        # homogeneous regions (small gradient, mostly noise) get unshaded color
        weight = np.clip(gradmag / 50.0, 0, 1)
        shade = 1.0 - weight * (0.7 - 0.7 * diffuse)
        acc_c = np.zeros((Z, X, 3), np.float32)
        acc_a = np.zeros((Z, X), np.float32)
        for y in range(Y):
            a, c = sample(y, gradmag)
            w = (1.0 - acc_a) * a
            acc_c += (w * shade[:, y, :])[..., None] * c
            acc_a += w
            if acc_a.min() > 0.98:
                break
        img = np.flipud(np.clip(acc_c * 255.0, 0, 255).astype(np.uint8))
        return np.ascontiguousarray(img)


def mpr(volume, axis, index, window, labels=None, label_colors=None, alpha=0.35):
    '''Axial (0), coronal (1) or sagittal (2) slice, aspect-corrected, with optional label overlay.'''
    dz, dy, dx = volume.spacing
    if axis == 0:
        img, sx, sy = volume.data[index], dx, dy
        lab = labels[index] if labels is not None else None
    elif axis == 1:
        img, sx, sy = np.flipud(volume.data[:, index, :]), dx, dz
        lab = np.flipud(labels[:, index, :]) if labels is not None else None
    else:
        img, sx, sy = np.flipud(volume.data[:, :, index]), dy, dz
        lab = np.flipud(labels[:, :, index]) if labels is not None else None
    out = cv.cvtColor(apply_window(img, *window), cv.COLOR_GRAY2BGR)
    if lab is not None and label_colors:
        overlay = out.copy()
        for value, bgr in label_colors.items():
            if value == 1:
                continue
            m = (lab == value).astype(np.uint8)
            if m.any():
                overlay[m > 0] = bgr
                contours, _ = cv.findContours(m, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
                cv.drawContours(out, contours, -1, bgr, 1)
        out = cv.addWeighted(overlay, alpha, out, 1.0 - alpha, 0)
    s = min(sx, sy)
    h, w = img.shape
    return cv.resize(out, (int(round(w * sx / s)), int(round(h * sy / s))), interpolation=cv.INTER_NEAREST)
