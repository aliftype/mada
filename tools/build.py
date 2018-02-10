#!/usr/bin/env python
# encoding: utf-8

import argparse
import os

from fontmake.font_project import FontProject

def build(args):
    designspace = os.path.join(args.build, args.designspace)

    project = FontProject(verbose="WARNING")
    if args.ufo:
        project.run_from_ufos([args.ufo],
            output=args.output, remove_overlaps=False, reverse_direction=False,
            subroutinize=True, autohint="")
    else:
        project.run_from_designspace(designspace,
            output=args.output, subroutinize=True, autohint="")

def main():
    parser = argparse.ArgumentParser(description="Build Mada fonts.")
    parser.add_argument("--source", metavar="DIR", help="Source directory", required=True)
    parser.add_argument("--build", metavar="DIR", help="Build directory", required=True)
    parser.add_argument("--designspace", metavar="FILE", help="DesignSpace file", required=True)
    parser.add_argument("--ufo", metavar="FONT", help="UFO source to process")
    parser.add_argument("--output", metavar="OUTPUT", help="Output format", required=True)
    parser.add_argument("--release", help="Build with optimizations for release", action="store_true")

    args = parser.parse_args()

    build(args)

if __name__ == "__main__":
    main()
