from glyphsLib import GSFont


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

    font = GSFont(args.arabicfile)
    font.versionMajor, font.versionMinor = map(int, args.version.split("."))
    font.save(args.out_file)


if __name__ == "__main__":
    main()
