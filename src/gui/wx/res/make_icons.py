#!/usr/bin/env python3
"""Regenerate the x64base application icon from the identity intake.

AIF-120 R91. The intake at
`dottalkpp/docs/media/x64base_identity_2026_07_12/` is preserved byte-for-byte
and is NOT edited; this script derives the runtime icon from it, so the
derivation is a recipe rather than a hand-cropped file nobody can reproduce.

    python3 src/gui/wx/res/make_icons.py

Writes x64base.ico and x64base_{16,32,48}.xpm beside this script. Requires
Pillow. The crop box is MEASURED, not eyeballed -- see CROP below.
"""

import io
import os
import struct
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
SOURCE = os.path.join(
    ROOT, 'dottalkpp', 'docs', 'media', 'x64base_identity_2026_07_12',
    '05-x64-smiling-database-site-icon.jpg')

# The intake image is a 784x1168 PORTRAIT canvas carrying a square icon tile.
# An application icon must be square, so the tile is cropped out of it.
#
# The box below was measured, not chosen: the tile is a few luminance levels
# brighter than the field it sits on, so blurring away the canvas texture
# (Gaussian sigma 5) and comparing a column band inside the tile against the
# left and right margins at the same row isolates it at
#
#     x 102..682   y 281..878
#
# The y extent runs 17 px longer than the x extent because the tile casts a
# drop shadow downward. Cropping to the SHADOW would push the tile off centre,
# so the box is squared on the tile itself and centred on it.
CROP = (100, 288, 684, 872)          # 584 x 584

ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48),
             (64, 64), (128, 128), (256, 256)]
# The conventional .ico layout: DIB frames for the small sizes, a PNG frame at
# 256. All-PNG is legal on Vista and later and is what a single Pillow save
# produces, but the small DIB frames are what every icon editor and every older
# shell path expects, and the mixed file is the one that cannot surprise
# anybody. Pillow writes one encoding per call, so the two calls are spliced.
PNG_FRAME_AT = 256
# 16 quantises to fewer than 48 distinct colours anyway; asking for more only
# grows the palette block.
XPM_SIZES = [(16, 48), (32, 64), (48, 64)]
CHARS = ('abcdefghijklmnopqrstuvwxyz'
         'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+@')

BANNER = (
    '/* XPM */\n'
    '/* GENERATED -- do not edit. Derived from\n'
    '   dottalkpp/docs/media/x64base_identity_2026_07_12/'
    '05-x64-smiling-database-site-icon.jpg\n'
    '   by the recipe in src/gui/wx/res/README.md (AIF-120 R91). */\n')


def _ico_frames(blob):
    """Frame payloads of an .ico held in memory, keyed by (width, height)."""
    count = struct.unpack('<H', blob[4:6])[0]
    frames = {}
    offset = 6
    for _ in range(count):
        w, h, colours, reserved, planes, bpp, size, at = struct.unpack(
            '<BBBBHHII', blob[offset:offset + 16])
        offset += 16
        frames[(w or 256, h or 256)] = (colours, reserved, planes, bpp,
                                        blob[at:at + size])
    return frames


def write_ico(tile, path):
    """A multi-size .ico: DIB frames below 256, a PNG frame at 256."""
    big = tile.resize((256, 256), Image.LANCZOS)

    # Both encodings are built IN MEMORY. An earlier version wrote two .tmp
    # files and removed them in a finally block, which works everywhere except
    # the one place this repository is routinely read from: a mounted working
    # tree that refuses unlink. A temporary file is a failure mode; a BytesIO
    # is not.
    def encode(bitmap_format):
        buf = io.BytesIO()
        big.save(buf, format='ICO', sizes=ICO_SIZES,
                 bitmap_format=bitmap_format)
        return _ico_frames(buf.getvalue())

    dib = encode('bmp')
    png = encode('png')

    chosen = [((w, h), (png if w >= PNG_FRAME_AT else dib)[(w, h)])
              for (w, h) in ICO_SIZES]
    directory = b''
    payload = b''
    at = 6 + 16 * len(chosen)
    for (w, h), (colours, reserved, planes, bpp, data) in chosen:
        directory += struct.pack('<BBBBHHII',
                                 0 if w == 256 else w, 0 if h == 256 else h,
                                 colours, reserved, planes, bpp, len(data), at)
        payload += data
        at += len(data)
    with open(path, 'wb') as handle:
        handle.write(struct.pack('<HHH', 0, 1, len(chosen)))
        handle.write(directory)
        handle.write(payload)


def write_xpm(tile, size, colours, path):
    im = tile.resize((size, size), Image.LANCZOS)
    im = im.convert('P', palette=Image.ADAPTIVE, colors=colours)
    palette = im.getpalette()
    pixels = list(im.tobytes())
    used = sorted(set(pixels))
    if len(used) > len(CHARS):
        raise SystemExit('%d colours needs a two-character XPM key' % len(used))
    key = {value: CHARS[i] for i, value in enumerate(used)}

    lines = [BANNER.rstrip('\n'),
             'static const char *const x64base_%d_xpm[] = {' % size,
             '"%d %d %d 1",' % (size, size, len(used))]
    for value in used:
        r, g, b = palette[value * 3:value * 3 + 3]
        lines.append('"%s c #%02X%02X%02X",' % (key[value], r, g, b))
    for y in range(size):
        row = ''.join(key[pixels[y * size + x]] for x in range(size))
        lines.append('"%s"%s' % (row, ',' if y < size - 1 else ''))
    lines.append('};')
    with open(path, 'w') as handle:
        handle.write('\n'.join(lines) + '\n')
    return len(used)


def main():
    if not os.path.isfile(SOURCE):
        sys.exit('intake image not found: %s' % SOURCE)
    tile = Image.open(SOURCE).convert('RGB').crop(CROP)
    if tile.size[0] != tile.size[1]:
        sys.exit('CROP is not square: %dx%d' % tile.size)

    ico = os.path.join(HERE, 'x64base.ico')
    write_ico(tile, ico)
    print('%s  %d bytes, %d sizes' % (os.path.basename(ico),
                                      os.path.getsize(ico), len(ICO_SIZES)))

    for size, colours in XPM_SIZES:
        path = os.path.join(HERE, 'x64base_%d.xpm' % size)
        n = write_xpm(tile, size, colours, path)
        print('%s  %d colours, %d bytes'
              % (os.path.basename(path), n, os.path.getsize(path)))


if __name__ == '__main__':
    main()
