import argparse
import sys

from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.varLib.mutator import instantiateVariableFont


AXIS_TAGS = {}


def toLocation(loc, doc):
    new = {}
    for name, value in loc.items():
        if name not in AXIS_TAGS:
            for axis in doc.axes:
                if axis.name == name:
                    AXIS_TAGS[name] = axis.tag
        tag = AXIS_TAGS.get(name)
        new[tag] = value

    return new


def setNames(font, instance):
    fontName = instance.postScriptFontName
    typoFamilyName = instance.familyName
    typoStyleName = instance.styleName
    fullName = f"{typoFamilyName} {typoStyleName}"
    familyName = instance.styleMapFamilyName
    styleName = instance.styleMapStyleName.title()

    version = font["head"].fontRevision
    vendor = font["OS/2"].achVendID
    uniqueID = f"{version:g};{vendor};{fontName}"

    platformID = 3
    platEncID = 1
    langID = 0x409

    name = font["name"]
    name.setName(familyName, 1, platformID, platEncID, langID)
    name.setName(styleName, 2, platformID, platEncID, langID)
    name.setName(uniqueID, 3, platformID, platEncID, langID)
    name.setName(fullName, 4, platformID, platEncID, langID)
    name.setName(fontName, 6, platformID, platEncID, langID)
    name.setName(typoFamilyName, 16, platformID, platEncID, langID)
    name.setName(typoStyleName, 17, platformID, platEncID, langID)

def removeOverlap(font):
    from pathops import Path

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
        from cffsubr import subroutinize
        subroutinize(font, cff_version=1)
        font["post"].formatType = 3.0


def main(args=None):
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Instantiate Mada fonts.")
    parser.add_argument("designspace", help="DesignSpace file")
    parser.add_argument("font", help="variable font file")
    parser.add_argument("output", help="output font to write")

    options = parser.parse_args(args)

    name = Path(options.output).stem
    font = TTFont(options.font)
    doc = DesignSpaceDocument()
    doc.read(options.designspace)
    for instance in doc.instances:
        if instance.postScriptFontName == name:
            location = toLocation(instance.location, doc)
            instantiateVariableFont(font, location, inplace=True)
            setNames(font, instance)
            removeOverlap(font)
            font.save(options.output)
            return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
