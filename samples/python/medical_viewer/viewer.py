#!/usr/bin/env python
'''
===============================================================================
Medical volume viewer prototype: MPR, 3D VRT/MIP with auto-rotation,
automatic segmentation and lesion measurement.

NOT A MEDICAL DEVICE. For research and education only.

USAGE:
    python viewer.py [<dicom_dir> | <volume.npy|.npz>] [--spacing DZ DY DX]
                     [--export OUT_DIR] [--frames N] [--preset bone|soft|lung]

    Without an input file a synthetic chest CT phantom is used.
    --export renders MPR images, a rotation video and a JSON/text report
    instead of opening a window (works with opencv-python-headless).

KEYS (interactive mode):
    SPACE   - toggle auto-rotation
    a / d   - rotate left / right          w / x   - tilt up / down
    1 2 3   - VRT presets bone / soft / lung
    m       - MIP          g  - segmentation surfaces (organs + lesions)
    j / k   - previous / next axial slice  (mouse wheel too)
    l       - cycle window: soft / lung / bone
    o       - toggle segmentation overlay on MPR
    s       - save screenshot              q / ESC - quit
===============================================================================
'''

from __future__ import print_function

import argparse
import json
import os
import sys

import numpy as np
import cv2 as cv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from volume import WINDOWS, load_volume  # noqa: E402
from segmentation import LABEL_COLORS, organ_stats, segment  # noqa: E402
from rendering import Renderer, mpr  # noqa: E402

DISCLAIMER = 'Prototype - not for clinical use'
TILE = 320


def fit(img, size=TILE):
    h, w = img.shape[:2]
    s = float(size) / max(h, w)
    img = cv.resize(img, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv.INTER_LINEAR)
    canvas = np.zeros((size, size, 3), np.uint8)
    y0, x0 = (size - img.shape[0]) // 2, (size - img.shape[1]) // 2
    canvas[y0:y0 + img.shape[0], x0:x0 + img.shape[1]] = img
    return canvas


def caption(img, text, y=18, color=(0, 255, 255), x=8):
    (w, h), base = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv.rectangle(img, (x - 3, y - h - 3), (x + w + 3, y + base), (0, 0, 0), -1)
    cv.putText(img, text, (x, y), cv.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv.LINE_AA)
    return img


def build_report(volume, labels, lesions):
    return {
        'disclaimer': DISCLAIMER,
        'series': volume.name,
        'shape_zyx': list(volume.shape),
        'spacing_mm_zyx': list(volume.spacing),
        'structures': organ_stats(volume, labels),
        'lesions': lesions,
    }


def report_text(report):
    lines = ['%s  [%s]' % (report['series'], report['disclaimer']),
             'shape (z,y,x) %s   spacing (mm) %s' % (report['shape_zyx'], report['spacing_mm_zyx']), '']
    for name, st in report['structures'].items():
        lines.append('%-8s volume %9.1f mL   mean %s HU' % (name, st['volume_ml'], st['mean_hu']))
    lines.append('')
    if not report['lesions']:
        lines.append('no lung lesion candidate found')
    for les in report['lesions']:
        lines.append('lesion #%d: %.2f mL, max axial diameter %.1f mm, equivalent diameter %.1f mm, '
                     'mean %.0f HU, slices %d-%d'
                     % (les['id'], les['volume_ml'], les['max_axial_diameter_mm'], les['equivalent_diameter_mm'],
                        les['mean_hu'], les['slices'][0], les['slices'][1]))
    return '\n'.join(lines)


class App(object):
    MODES = ['bone', 'soft', 'lung', 'mip', 'seg']

    def __init__(self, volume, preset='bone'):
        self.vol = volume
        print('segmenting...')
        self.labels, self.lesions = segment(volume)
        self.report = build_report(volume, self.labels, self.lesions)
        print(report_text(self.report))
        self.renderer = Renderer(volume, self.labels)
        self.mode = preset
        self.azimuth, self.elevation = 0.0, 0.0
        self.auto_rotate = True
        self.window_names = list(WINDOWS)
        self.window = 'lung' if self.lesions else 'soft'
        self.overlay = True
        Z, Y, X = volume.shape
        # start on the first lesion if there is one
        self.cursor = list(self.lesions[0]['centroid_voxel']) if self.lesions else [Z // 2, Y // 2, X // 2]

    def render_3d(self):
        if self.mode == 'mip':
            img = self.renderer.mip(self.azimuth, self.elevation)
        elif self.mode == 'seg':
            img = self.renderer.surfaces(self.azimuth, self.elevation, LABEL_COLORS)
        else:
            img = self.renderer.vrt(self.azimuth, self.elevation, self.mode)
        return img

    def compose(self):
        win = WINDOWS[self.window]
        lab = self.labels if self.overlay else None
        z, y, x = self.cursor
        views = [
            (mpr(self.vol, 0, z, win, lab, LABEL_COLORS), 'Axial %d/%d' % (z + 1, self.vol.shape[0])),
            (mpr(self.vol, 1, y, win, lab, LABEL_COLORS), 'Coronal'),
            (mpr(self.vol, 2, x, win, lab, LABEL_COLORS), 'Sagittal'),
            (self.render_3d(), '3D %s  az %d el %d' % (self.mode.upper(), self.azimuth % 360, self.elevation)),
        ]
        tiles = [caption(fit(img), text) for img, text in views]
        grid = np.vstack([np.hstack(tiles[:2]), np.hstack(tiles[2:])])
        caption(grid, DISCLAIMER, grid.shape[0] - 10, (80, 80, 255))
        caption(grid, 'W/L %s %d/%d' % ((self.window,) + win), TILE - 10)
        for i, les in enumerate(self.lesions[:3]):
            caption(grid, 'Lesion %d: %.1f mm, %.2f mL' % (les['id'], les['max_axial_diameter_mm'], les['volume_ml']),
                    2 * TILE - 34 - 20 * i, (60, 60, 255), TILE + 8)
        return grid

    def export(self, out_dir, frames=36):
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        with open(os.path.join(out_dir, 'report.json'), 'w') as f:
            json.dump(self.report, f, indent=2)
        with open(os.path.join(out_dir, 'report.txt'), 'w') as f:
            f.write(report_text(self.report) + '\n')
        cv.imwrite(os.path.join(out_dir, 'overview.png'), self.compose())
        for mode in self.MODES:
            self.mode = mode
            cv.imwrite(os.path.join(out_dir, '3d_%s.png' % mode), self.render_3d())
        self.mode = 'bone'
        writer = None
        for i in range(frames):
            self.azimuth = 360.0 * i / frames
            frame = self.compose()
            if writer is None:
                h, w = frame.shape[:2]
                writer = cv.VideoWriter(os.path.join(out_dir, 'rotation.avi'), cv.VideoWriter_fourcc(*'MJPG'),
                                        12, (w, h))
            writer.write(frame)
        if writer is not None:
            writer.release()
        print('exported to %s' % out_dir)

    def on_mouse(self, event, x, y, flags, param):
        if event == cv.EVENT_MOUSEWHEEL:
            step = 1 if flags > 0 else -1
            self.cursor[0] = int(np.clip(self.cursor[0] + step, 0, self.vol.shape[0] - 1))

    def run(self):
        title = 'Medical viewer (%s)' % DISCLAIMER
        cv.namedWindow(title)
        cv.setMouseCallback(title, self.on_mouse)
        shot = 0
        while True:
            if self.auto_rotate:
                self.azimuth = (self.azimuth + 5) % 360
            cv.imshow(title, self.compose())
            key = cv.waitKey(1 if self.auto_rotate else 30) & 0xFF
            if key in (27, ord('q')):
                break
            elif key == ord(' '):
                self.auto_rotate = not self.auto_rotate
            elif key in (ord('a'), ord('d')):
                self.azimuth += -10 if key == ord('a') else 10
            elif key in (ord('w'), ord('x')):
                self.elevation = float(np.clip(self.elevation + (10 if key == ord('w') else -10), -80, 80))
            elif key in (ord('1'), ord('2'), ord('3')):
                self.mode = self.MODES[key - ord('1')]
            elif key == ord('m'):
                self.mode = 'mip'
            elif key == ord('g'):
                self.mode = 'seg'
            elif key in (ord('j'), ord('k')):
                self.cursor[0] = int(np.clip(self.cursor[0] + (1 if key == ord('k') else -1),
                                             0, self.vol.shape[0] - 1))
            elif key == ord('l'):
                self.window = self.window_names[(self.window_names.index(self.window) + 1) % len(self.window_names)]
            elif key == ord('o'):
                self.overlay = not self.overlay
            elif key == ord('s'):
                name = 'screenshot_%03d.png' % shot
                cv.imwrite(name, self.compose())
                print('saved', name)
                shot += 1
        cv.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input', nargs='?', help='DICOM directory, .npy or .npz volume (default: phantom)')
    parser.add_argument('--spacing', nargs=3, type=float, default=(1.0, 1.0, 1.0), metavar=('DZ', 'DY', 'DX'),
                        help='voxel spacing in mm for .npy input')
    parser.add_argument('--export', metavar='OUT_DIR', help='render images, video and report, no window')
    parser.add_argument('--frames', type=int, default=36, help='frames of the exported rotation')
    parser.add_argument('--preset', default='bone', choices=App.MODES)
    args = parser.parse_args()

    app = App(load_volume(args.input, args.spacing), args.preset)
    if args.export:
        app.export(args.export, args.frames)
        return
    try:
        app.run()
    except cv.error as e:
        print('cannot open a window (%s); use --export OUT_DIR instead' % str(e).strip().splitlines()[-1])
        sys.exit(1)


if __name__ == '__main__':
    print(__doc__)
    main()
