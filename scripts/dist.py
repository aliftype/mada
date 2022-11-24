import argparse

from fontTools import subset
from fontTools.ttLib import TTFont

from gftools.fix import fix_unhinted_font
from gftools.stat import gen_stat_tables


def main():
    parser = argparse.ArgumentParser(description="Post process font for distribution.")
    parser.add_argument("input", metavar="FILE", help="input font to process")
    parser.add_argument("output", metavar="FILE", help="output font to save")
    parser.add_argument("version", metavar="VERSION", help="Font version")

    args = parser.parse_args()

    font = TTFont(args.input)

    version = args.version.split("-")[0]
    if args.version[0] == "v":
        version = version[1:]

    font["head"].fontRevision = float(version)

    font["name"].names = [n for n in font["name"].names if n.platformID == 3]
    for name in font["name"].names:
        if name.nameID == 5:
            v = f"Version {version}"
            name.string = v
        if name.nameID == 3:
            parts = [version] + str(name).split(";")[1:]
            name.string = ";".join(parts)

    if "fvar" in font:
       #for n in font["name"].names:
       #    if n.nameID == 6:
       #        psname = str(n).split("-")[0]
       #        n.string = psname
       #    elif n.nameID == 3:
       #        n.string = str(n).split("-")[0]
       #    elif n.nameID == 4:
       #        n.string = str(n).replace(" Regular", "")
        gen_stat_tables([font])
    fix_unhinted_font(font)

    unicodes = set(font.getBestCmap().keys())
    options = subset.Options()
    options.set(
        layout_features="*",
        layout_scripts="*",
        name_IDs="*",
        name_languages="*",
        notdef_outline=True,
        glyph_names=False,
        recalc_average_width=True,
        drop_tables=[],
    )
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=unicodes)
    subsetter.subset(font)

    font.save(args.output)


if __name__ == "__main__":
    main()
