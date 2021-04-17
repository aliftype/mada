import argparse
import sys

from fontTools import configLogger
from fontTools.varLib import build
from pathlib import Path


def main(args=None):
    parser = argparse.ArgumentParser(description="Make Mada variable font.")
    parser.add_argument("designspace", help="input designspace file")
    parser.add_argument("output", help="output font to write")

    options = parser.parse_args(args)
    ext = Path(options.output).suffix

    configLogger(level="ERROR")

    finder = lambda x: Path(x).with_suffix(ext)
    font, _, _ = build(options.designspace, finder)

    name = font["name"]
    # Keep only Windows names
    name.names = [n for n in font["name"].names if n.platformID == 3]

    # Drop Regular from names
    for nameID in (3, 4, 6):
        record = name.getName(nameID, 3, 1)
        record.string = str(record).replace("-Regular", "").replace(" Regular", "")

    cmap = font["cmap"]
    cmap.tables = [t for t in cmap.tables if (t.platformID, t.platEncID) == (3, 10)]

    font.save(options.output)


if __name__ == "__main__":
    sys.exit(main())
