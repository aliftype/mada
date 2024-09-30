import argparse

from fontTools import subset
from fontTools.ttLib import TTFont


def main():
    parser = argparse.ArgumentParser(description="Post process font for distribution.")
    parser.add_argument("input", metavar="FILE", help="input font to process")
    parser.add_argument("output", metavar="FILE", help="output font to save")

    args = parser.parse_args()

    font = TTFont(args.input)

    font["name"].names = [n for n in font["name"].names if n.platformID == 3]

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
