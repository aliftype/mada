import argparse
import math

from ufoLib2 import Font
from fontTools.misc.transform import Identity


def main():
    parser = argparse.ArgumentParser(description="Build Mada slanted fonts.")
    parser.add_argument("file", metavar="FILE", help="input font to process")
    parser.add_argument("outfile", metavar="FILE", help="output font to write")
    parser.add_argument("angle", metavar="FILE", help="slant angle", type=float)

    args = parser.parse_args()

    matrix = Identity.skew(math.radians(-args.angle))

    font = Font(args.file)

    info = font.info

    if args.angle < 0:
        style = "Italic"
    else:
        style = "Slanted"
    info.styleName += " " + style
    info.italicAngle = info.postscriptSlantAngle = args.angle

    for glyph in font:
        for contour in glyph:
            for point in contour:
                point.x, point.y = matrix.transformPoint((point.x, point.y))
        for anchor in glyph.anchors:
            anchor.x, anchor.y = matrix.transformPoint((anchor.x, anchor.y))

    font.save(args.outfile, overwrite=True)


if __name__ == "__main__":
    main()
