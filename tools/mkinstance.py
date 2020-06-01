import argparse
import sys

from fontTools.ttLib import TTFont
from fontTools.designspaceLib import DesignSpaceDocument
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
    name = font["name"]

    typoFamilyName = instance.familyName
    typoStyleName = instance.styleName
    familyName = instance.styleMapFamilyName
    styleName = instance.styleMapStyleName.title()

    for rec in name.names:
        if rec.nameID == 1:
            rec.string = familyName
        elif rec.nameID == 2:
            rec.string = styleName
        elif rec.nameID == 4:
            rec.string = f"{typoFamilyName} {typoStyleName}"
        elif rec.nameID == 6:
            rec.string = instance.postScriptFontName
        elif rec.nameID == 16 and typoFamilyName != familyName:
            rec.string = typoFamilyName
        elif rec.nameID == 17 and typoStyleName != styleName:
            rec.string = typoStyleName


def main(args=None):
    parser = argparse.ArgumentParser(description="Instantiate Mada fonts.")
    parser.add_argument("designspace", help="DesignSpace file")
    parser.add_argument("font", help="variable font file")
    parser.add_argument("instance", help="instance PS name")
    parser.add_argument("output", help="output font to write")

    options = parser.parse_args(args)

    doc = DesignSpaceDocument()
    doc.read(options.designspace)
    for instance in doc.instances:
        if instance.postScriptFontName == options.instance:
            font = TTFont(options.font)
            location = toLocation(instance.location, doc)
            instantiateVariableFont(font, location, inplace=True)
            setNames(font, instance)
            font.save(options.output)
            return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
