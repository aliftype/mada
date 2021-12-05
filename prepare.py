from datetime import datetime

from ufoLib2 import Font

from glyphsLib import GSFont
from glyphsLib.builder import UFOBuilder


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
    ufo.features.text += generateStyleSets(ufo)
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
