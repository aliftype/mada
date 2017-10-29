#!/usr/bin/env python
# encoding: utf-8

import argparse
import os

from fontmake.font_project import FontProject
from mutatorMath.ufo.document import DesignSpaceDocumentReader

def epoch(args):
    reader = DesignSpaceDocumentReader(args.designspace, ufoVersion=3)
    paths = reader.getSourcePaths() + [args.designspace]
    epoch = max([os.stat(os.path.join(args.source, p)).st_mtime for p in paths])

    return str(int(epoch))

def build(args):
    designspace = os.path.join(args.build, args.designspace)

    os.environ["SOURCE_DATE_EPOCH"] = epoch(args)

    interpolate = True
    if args.output == "variable":
        interpolate = False

    autohint = None
    if args.release:
        autohint = ""

    project = FontProject(verbose="WARNING")
    project.run_from_designspace(designspace,
            output=args.output, interpolate=interpolate,
            remove_overlaps=args.release, reverse_direction=args.release,
            subroutinize=args.release, autohint=autohint)

def main():
    parser = argparse.ArgumentParser(description="Build Mada fonts.")
    parser.add_argument("--source", metavar="DIR", help="Source directory", required=True)
    parser.add_argument("--build", metavar="DIR", help="Build directory", required=True)
    parser.add_argument("--designspace", metavar="FILE", help="DesignSpace file", required=True)
    parser.add_argument("--output", metavar="OUTPUT", help="Output format", required=True)
    parser.add_argument("--release", help="Build with optimizations for release", action="store_true")

    args = parser.parse_args()

    build(args)

if __name__ == "__main__":
    main()
