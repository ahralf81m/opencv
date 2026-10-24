#!/usr/bin/env python
'''Self-checks on the synthetic phantom: python test_medical_viewer.py'''

from __future__ import print_function

import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from volume import PHANTOM_LESION, load_volume, make_phantom  # noqa: E402
from segmentation import BONE, LUNG, LABEL_COLORS, label_3d, segment  # noqa: E402
from rendering import Renderer, mpr  # noqa: E402


class PhantomTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vol = make_phantom()
        cls.labels, cls.lesions = segment(cls.vol)

    def test_lesion_measurement(self):
        self.assertEqual(len(self.lesions), 1)
        r = PHANTOM_LESION['radius_mm']
        true_ml = 4.0 / 3.0 * np.pi * r ** 3 / 1000.0
        lesion = self.lesions[0]
        self.assertAlmostEqual(lesion['volume_ml'], true_ml, delta=0.15 * true_ml)
        self.assertAlmostEqual(lesion['equivalent_diameter_mm'], 2 * r, delta=1.5)
        self.assertAlmostEqual(lesion['max_axial_diameter_mm'], 2 * r, delta=2 * self.vol.spacing[1])
        z, y, x = lesion['centroid_voxel']
        cz, cy, cx = PHANTOM_LESION['center_mm']
        Z, Y, X = self.vol.shape
        dz, dy, dx = self.vol.spacing
        self.assertLessEqual(abs(z - (cz / dz + Z / 2.0)), 1)
        self.assertLessEqual(abs(x - (cx / dx + X / 2.0)), 1)
        self.assertLessEqual(abs(y - (cy / dy + Y / 2.0)), 1)

    def test_lung_volume(self):
        true_ml = 2 * 4.0 / 3.0 * np.pi * 100 * 60 * 45 / 1000.0
        lung_ml = (self.labels == LUNG).sum() * self.vol.voxel_ml
        self.assertAlmostEqual(lung_ml, true_ml, delta=0.05 * true_ml)

    def test_bone_found(self):
        self.assertGreater((self.labels == BONE).sum(), 1000)

    def test_rendering(self):
        r = Renderer(self.vol, self.labels, max_dim=64)
        for img in (r.vrt(30, 10, 'bone'), r.vrt(0, 0, 'soft'), r.vrt(0, 0, 'lung'),
                    r.mip(90), r.surfaces(45, 0, LABEL_COLORS)):
            self.assertEqual(img.dtype, np.uint8)
            self.assertEqual(img.ndim, 3)
            self.assertGreater(img.max(), 50)
        sag = mpr(self.vol, 2, 64, (40, 400), self.labels, LABEL_COLORS)
        self.assertEqual(sag.shape, (96, 128, 3))


class Label3DTest(unittest.TestCase):
    def test_merges_across_slices(self):
        m = np.zeros((4, 10, 10), np.uint8)
        m[0, 1:3, 1:3] = 1
        m[1, 2:4, 2:4] = 1      # overlaps slice 0 -> same object
        m[1, 6:8, 6:8] = 1      # separate object
        m[3, 2:3, 2:3] = 1      # slice 2 empty -> separate object
        labels, n = label_3d(m)
        self.assertEqual(n, 3)
        self.assertEqual(labels[0, 1, 1], labels[1, 3, 3])
        self.assertNotEqual(labels[1, 3, 3], labels[1, 6, 6])


class DicomTest(unittest.TestCase):
    def test_series_sorted_by_position(self):
        try:
            import pydicom  # noqa: F401
            from pydicom.dataset import Dataset, FileMetaDataset
            from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian, generate_uid
        except ImportError:
            self.skipTest('pydicom is not installed')
        data = np.arange(5 * 8 * 8, dtype=np.float32).reshape(5, 8, 8) - 100
        tmp = tempfile.mkdtemp()
        try:
            series = generate_uid()
            for k, z in enumerate([3, 0, 4, 1, 2]):  # files out of order
                meta = FileMetaDataset()
                meta.MediaStorageSOPClassUID = CTImageStorage
                meta.MediaStorageSOPInstanceUID = generate_uid()
                meta.TransferSyntaxUID = ExplicitVRLittleEndian
                ds = Dataset()
                ds.file_meta = meta
                ds.SOPClassUID, ds.SOPInstanceUID = CTImageStorage, meta.MediaStorageSOPInstanceUID
                ds.SeriesInstanceUID, ds.Modality = series, 'CT'
                ds.Rows, ds.Columns = 8, 8
                ds.PixelSpacing, ds.ImageOrientationPatient = [0.7, 0.8], [1, 0, 0, 0, 1, 0]
                ds.ImagePositionPatient = [0, 0, -50 + 3.0 * z]
                ds.RescaleSlope, ds.RescaleIntercept = 1, -1024
                ds.SamplesPerPixel, ds.PhotometricInterpretation = 1, 'MONOCHROME2'
                ds.BitsAllocated, ds.BitsStored, ds.HighBit, ds.PixelRepresentation = 16, 16, 15, 0
                ds.PixelData = (data[z] + 1024).astype(np.uint16).tobytes()
                ds.save_as(os.path.join(tmp, 'f%d.dcm' % k), enforce_file_format=True)
            with open(os.path.join(tmp, 'notes.txt'), 'w') as f:
                f.write('not a DICOM file')
            vol = load_volume(tmp)
            self.assertEqual(vol.spacing, (3.0, 0.7, 0.8))
            np.testing.assert_array_equal(vol.data, data)
        finally:
            shutil.rmtree(tmp)


if __name__ == '__main__':
    unittest.main()
