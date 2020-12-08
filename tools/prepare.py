from datetime import datetime
from operator import attrgetter
from io import StringIO

from ufoLib2 import Font
from fontTools.feaLib import ast, parser

from glyphsLib import GSFont
from glyphsLib.builder import UFOBuilder

POSTSCRIPT_NAMES = "public.postscriptNames"


def generateStyleSets(ufo):
    """Generates ss01 feature which is used to move the final Yeh down so that
    it does not raise above the connecting part of other glyphs, as it does by
    default. We calculate the height difference between Yeh and Tatweel and set
    the feature accordingly."""

    tatweel = ufo["kashida-ar"].getBounds(ufo.layers.defaultLayer)
    yeh = ufo["alefMaksura-ar.fina"].getBounds(ufo.layers.defaultLayer)
    delta = tatweel.yMax - yeh.yMax

    fea = """
feature ss01 {
    pos alefMaksura-ar.fina <0 %s 0 0>;
} ss01;
""" % int(
        delta
    )

    return fea


def merge(ufo, args):
    """Merges Arabic and Latin fonts together, and messages the combined font a
    bit. Returns the combined font."""

    latin = Font(args.latinfile)

    # Save original glyph order, used below.
    glyphOrder = ufo.glyphOrder + latin.glyphOrder

    ufo.features.text += generateStyleSets(ufo)

    # Merge Arabic and Latin features, making sure languagesystem statements
    # come first.
    langsys = []
    statements = []
    ss = 0
    for font in (ufo, latin):
        if font is latin:
            featurefile = StringIO("include (../../../familyGSUB.fea);")
            includeDir = args.latinfile.parent
        else:
            featurefile = StringIO(font.features.text)
            includeDir = None

        fea = parser.Parser(featurefile, font.glyphOrder, includeDir=includeDir).parse()
        scripts = {}
        for s in fea.statements:
            if isinstance(s, ast.LanguageSystemStatement):
                langsys.append(s)
                scripts.setdefault(s.script, []).append(s.language)
        for s in fea.statements:
            if isinstance(s, ast.LanguageSystemStatement):
                continue
            if isinstance(s, ast.FeatureBlock) and s.name != "locl":
                if s.name in ("aalt", "size"):
                    # aalt and size are useless.
                    continue
                new = []
                for st in s.statements:
                    if isinstance(st, ast.LookupBlock):
                        statements.append(st)
                        new.append(ast.LookupReferenceStatement(st))
                    elif isinstance(st, ast.GlyphClassDefinition):
                        statements.append(st)
                    else:
                        new.append(st)
                s.statements = new
                new = []
                for script in scripts:
                    new.append(ast.ScriptStatement(script))
                    new.extend(s.statements)
                    for lang in scripts[script]:
                        if lang == "dflt":
                            continue
                        new.append(ast.LanguageStatement(lang))
                s.statements = new

                if s.name.startswith("ss"):
                    if font is ufo:
                        # Find max ssXX feature in Arabic font.
                        ss = max(ss, int(s.name[2:]))
                    else:
                        # Increment Latin ssXX features.
                        s.name = f"ss{int(s.name[2:]) + ss:02}"
            statements.append(s)

    # Make sure DFLT is the first.
    langsys = sorted(langsys, key=attrgetter("script"))
    fea.statements = langsys + statements
    ufo.features.text = fea.asFea()

    # Set Latin production names
    ufo.lib[POSTSCRIPT_NAMES].update(latin.lib[POSTSCRIPT_NAMES])

    # Copy Latin glyphs.
    for name in latin.glyphOrder:
        glyph = latin[name]
        # Add Arabic anchors to the dotted circle, we use an offset of 100
        # units because the Latin anchors are too close to the glyph.
        offset = 100
        if glyph.unicode == 0x25CC:
            for anchor in glyph.anchors:
                if anchor.name == "aboveLC":
                    glyph.appendAnchor(
                        dict(name="top.mark", x=anchor.x, y=anchor.y + offset)
                    )
                    glyph.appendAnchor(
                        dict(name="top.hamza", x=anchor.x, y=anchor.y + offset)
                    )
                if anchor.name == "belowLC":
                    glyph.appendAnchor(
                        dict(name="bottom.mark", x=anchor.x, y=anchor.y - offset)
                    )
                    glyph.appendAnchor(
                        dict(name="bottom.hamza", x=anchor.x, y=anchor.y - offset)
                    )
        # Break loudly if we have duplicated glyph in Latin and Arabic.
        # TODO should check duplicated Unicode values as well
        assert glyph.name not in ufo, glyph.name
        ufo.addGlyph(glyph)
        ufo.glyphOrder += [glyph.name]

    # Copy kerning and groups.
    ufo.groups.update(latin.groups)
    ufo.kerning.update(latin.kerning)

    # We don’t set these in the Arabic font, so we just copy the Latin’s.
    for attr in ("xHeight", "capHeight"):
        value = getattr(latin.info, attr)
        if value is not None:
            setattr(ufo.info, attr, getattr(latin.info, attr))

    # Make sure we don’t have glyphs with the same unicode value
    unicodes = []
    for glyph in ufo:
        unicodes.extend(glyph.unicodes)
    duplicates = set([u for u in unicodes if unicodes.count(u) > 1])
    assert len(duplicates) == 0, "Duplicate unicodes: %s " % (
        ["%04X" % d for d in duplicates]
    )

    # Make sure we have a fixed glyph order by using the original Arabic and
    # Latin glyph order, not whatever we end up with after adding glyphs.
    ufo.glyphOrder = sorted(ufo.glyphOrder, key=glyphOrder.index)

    return ufo


def decomposeFlippedComponents(ufo):
    from fontTools.pens.transformPen import TransformPointPen

    for glyph in ufo:
        for component in list(glyph.components):
            xx, xy, yx, yy = component.transformation[:4]
            if xx * yy - xy * yx < 0:
                pen = TransformPointPen(glyph.getPointPen(), component.transformation)
                ufo[component.baseGlyph].drawPoints(pen)
                glyph.removeComponent(component)


def setInfo(info, version):
    """Sets various font metadata fields."""

    info.versionMajor, info.versionMinor = map(int, version.split("."))

    copyright = (
        "Copyright © 2015-%s The Mada Project Authors, with Reserved Font Name “Source”."
        % datetime.now().year
    )

    info.copyright = copyright


def loadUFO(args):
    font = GSFont(args.arabicfile)
    master = args.out_file.stem.split("-")[1]
    builder = UFOBuilder(font, write_skipexportglyphs=True, generate_GDEF=False)
    for ufo in builder.masters:
        if ufo.info.styleName == master:
            return ufo


def build(args):
    ufo = loadUFO(args)
    ufo = merge(ufo, args)
    setInfo(ufo.info, args.version)
    decomposeFlippedComponents(ufo)

    return ufo


def main():
    from pathlib import Path
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Prepare Mada fonts.")
    parser.add_argument(
        "arabicfile", metavar="FILE", type=Path, help="input font to process"
    )
    parser.add_argument(
        "latinfile", metavar="FILE", type=Path, help="input font to process"
    )
    parser.add_argument(
        "--out-file",
        metavar="FILE",
        type=Path,
        required=True,
        help="output font to write",
    )
    parser.add_argument(
        "--version", metavar="version", help="version number", required=True
    )

    args = parser.parse_args()

    ufo = build(args)
    ufo.save(args.out_file, overwrite=True)


if __name__ == "__main__":
    main()
