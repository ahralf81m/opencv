'''
Volume loading: DICOM series, NumPy arrays and a synthetic chest CT phantom.

All volumes are stored as float32 Hounsfield units with shape (Z, Y, X):
Z goes from inferior to superior, Y from anterior to posterior and X from
patient right to patient left (standard axial display orientation).
'''

from __future__ import print_function

import os

import numpy as np
import cv2 as cv

AIR_HU = -1024.0

# (center, width) in HU
WINDOWS = {
    'soft': (40, 400),
    'lung': (-600, 1500),
    'bone': (400, 1800),
}


class Volume(object):
    def __init__(self, data, spacing, name=''):
        self.data = np.ascontiguousarray(data, dtype=np.float32)
        self.spacing = tuple(float(s) for s in spacing)  # (dz, dy, dx) in mm
        self.name = name

    @property
    def shape(self):
        return self.data.shape

    @property
    def voxel_ml(self):
        return float(np.prod(self.spacing)) / 1000.0


def apply_window(img, center, width):
    lo = center - width / 2.0
    out = (img.astype(np.float32) - lo) * (255.0 / width)
    return np.clip(out, 0, 255).astype(np.uint8)


def load_dicom_series(path):
    import pydicom
    from pydicom.errors import InvalidDicomError

    series = {}
    for root, _, names in os.walk(path):
        for name in sorted(names):
            try:
                ds = pydicom.dcmread(os.path.join(root, name))
            except (InvalidDicomError, IsADirectoryError, PermissionError):
                continue
            if 'PixelData' not in ds:
                continue
            series.setdefault(str(ds.get('SeriesInstanceUID', '')), []).append(ds)
    if not series:
        raise ValueError('no DICOM images found in %s' % path)

    # keep the series with the most slices
    slices = max(series.values(), key=len)
    first = slices[0]
    if 'ImageOrientationPatient' in first and 'ImagePositionPatient' in first:
        iop = np.array(first.ImageOrientationPatient, dtype=np.float64)
        normal = np.cross(iop[:3], iop[3:])

        def key(s):
            return float(np.dot(normal, np.array(s.ImagePositionPatient, dtype=np.float64)))
    else:
        def key(s):
            return float(s.get('InstanceNumber', 0))
    slices.sort(key=key)

    data = np.stack([
        s.pixel_array.astype(np.float32) * float(s.get('RescaleSlope', 1)) + float(s.get('RescaleIntercept', 0))
        for s in slices])

    dy, dx = (float(v) for v in first.get('PixelSpacing', (1.0, 1.0)))
    positions = [key(s) for s in slices]
    if len(slices) > 1 and 'ImagePositionPatient' in first:
        dz = float(np.median(np.abs(np.diff(positions)))) or 1.0
    else:
        dz = float(first.get('SliceThickness', 1.0))
    name = str(first.get('SeriesDescription', '')) or os.path.basename(os.path.normpath(path))
    return Volume(data, (dz, dy, dx), name)


def load_volume(path, spacing=(1.0, 1.0, 1.0)):
    if path is None:
        return make_phantom()
    if os.path.isdir(path):
        return load_dicom_series(path)
    if path.endswith('.npy'):
        return Volume(np.load(path), spacing, os.path.basename(path))
    if path.endswith('.npz'):
        f = np.load(path)
        return Volume(f['data'], f['spacing'] if 'spacing' in f else spacing, os.path.basename(path))
    raise ValueError('unsupported input: %s (expected DICOM directory, .npy or .npz)' % path)


# Ground truth of the phantom lesion, used by the tests and the demo report
PHANTOM_LESION = {'center_mm': (20.0, -20.0, -65.0), 'radius_mm': 8.0}


def make_phantom(shape=(96, 128, 128), spacing=(2.5, 2.5, 2.5), noise=15.0, seed=0):
    '''Synthetic chest CT: body, fat layer, lungs, heart, spine, ribs and one lung nodule.'''
    Z, Y, X = shape
    dz, dy, dx = spacing
    z, y, x = np.meshgrid((np.arange(Z) - Z / 2.0) * dz,
                          (np.arange(Y) - Y / 2.0) * dy,
                          (np.arange(X) - X / 2.0) * dx, indexing='ij')
    hu = np.full(shape, AIR_HU, np.float32)

    def ellipsoid(cz, cy, cx, rz, ry, rx):
        return ((z - cz) / rz) ** 2 + ((y - cy) / ry) ** 2 + ((x - cx) / rx) ** 2 <= 1.0

    def ellipse(cy, cx, ry, rx):
        return ((y - cy) / ry) ** 2 + ((x - cx) / rx) ** 2 <= 1.0

    hu[ellipse(0, 0, 112, 152)] = -100                      # subcutaneous fat
    hu[ellipse(0, 0, 104, 144)] = 30                        # muscle / soft tissue
    hu[ellipsoid(0, -5, -65, 100, 60, 45)] = -850           # right lung
    hu[ellipsoid(0, -5, 65, 100, 60, 45)] = -850            # left lung
    hu[ellipsoid(-10, -15, 10, 45, 40, 30)] = 45            # heart
    hu[ellipse(75, 0, 15, 15)] = 700                        # vertebral column
    ring = ellipse(0, 0, 100, 140) & ~ellipse(0, 0, 94, 134) & (y > -60)
    for cz in np.arange(-100, 101, 25):                     # ribs
        hu[ring & (np.abs(z - cz) <= 4)] = 600
    c = PHANTOM_LESION['center_mm']
    r = PHANTOM_LESION['radius_mm']
    hu[ellipsoid(c[0], c[1], c[2], r, r, r)] = 30           # lung nodule

    rng = np.random.RandomState(seed)
    hu += rng.normal(0, noise, shape).astype(np.float32)
    hu = cv.GaussianBlur(hu.reshape(Z * Y, X), (3, 1), 0).reshape(shape)  # mild partial-volume blur
    return Volume(hu, spacing, 'synthetic chest phantom')
