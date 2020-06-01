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

    # Keep only Windows names
    font["name"].names = [n for n in font["name"].names if n.platformID == 3]

    font.save(options.output)


if __name__ == "__main__":
    sys.exit(main())
