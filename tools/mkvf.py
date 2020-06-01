import argparse
import sys

from fontTools import configLogger
from fontTools.varLib import build, MasterFinder


def main(args=None):
    parser = argparse.ArgumentParser(description="Make Mada variable font.")
    parser.add_argument("designspace", help="input designspace file")
    parser.add_argument("--output", help="output font to write")
    parser.add_argument("--master-finder", help="master finder template")

    options = parser.parse_args(args)

    configLogger(level="ERROR")
    finder = MasterFinder(options.master_finder)
    font, _, _ = build(options.designspace, finder)

    font.save(options.output)


if __name__ == "__main__":
    sys.exit(main())
