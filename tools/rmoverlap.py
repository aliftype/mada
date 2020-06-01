import argparse
import sys

from cffsubr import subroutinize
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from pathops import Path, PathPen


def main(args=None):
    parser = argparse.ArgumentParser(description="Remove path overlaps.")
    parser.add_argument("input", help="input font to read")
    parser.add_argument("output", help="output font to write")

    options = parser.parse_args(args)

    font = TTFont(options.input)
    names = font.getGlyphOrder()
    glyphs = font.getGlyphSet()

    charStrings = None
    CFF2 = False
    if 'glyf' in font:
        assert False
    elif "CFF2" in font:
        CFF2 = True
        charStrings = font["CFF2"].cff.topDictIndex[0].CharStrings
    else:
        charStrings = font["CFF "].cff.topDictIndex[0].CharStrings
    for name in names:
        glyph = glyphs[name]
        path = Path()
        glyph.draw(path.getPen())
        path.simplify(fix_winding=True, keep_starting_points=True)
        if charStrings is not None:
            charString = charStrings[name]
            pen = T2CharStringPen(None, None, CFF2=CFF2)
            path.draw(pen)
            charStrings[name] = pen.getCharString(charString.private)
            if not CFF2:
                charStrings[name].program.insert(0, charString.width)

    if charStrings is not None:
        subroutinize(font, cff_version=1)

    font.save(options.output)


if __name__ == "__main__":
    sys.exit(main())
