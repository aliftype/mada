Mada
====

![Sample](FontSample.svg)

Mada (مدى) is a modernist, low contrast Arabic typeface based largely on the typeface
seen in Cairo metro old signage which was designed by Professor Fathi Gouda of
Faculty of Applied Arts, Helwan University.

Mada is characterised by low descenders, open contours and low contrast forms
making it suitable for small point sizes, user interfaces, signage or low
resolution settings.

Mada can work also as a display typeface giving modernist and simplistic feeling.

Mada comes in 7 weights (ExtraLight, Light, Regular, Medium, SemiBold, Bold and
Black), as well as an interpolatable variable font that can provide any
intermediate weight on the fly.

Building
--------

If you are building from cloned Git repository, you will need to update the git
sub modules:

    git submodule update --init

You need GNU Make and a few Python packages. To install the Python
requirements, run:

    pip install -r requirements.txt

Then to build the fonts:

    make otf # CFF-flavoured fonts
    make ttf # TTF-flavoured fonts

Installation
------------

Mada comes in two flavours, a [variable font][2] that has all the font styles
in the same file, and allow dynamic changes of the font styles, and a set of
static instances for specific font styles.

The variable font file is `Mada.otf` and the static instances has the style as
part of the file name (e.g. `Mada-Regular.otf`). It is not recommended to
install both variable font and the static instances at the same time, as it
would confuse some applications. You should install either of them based on the
degree of variable font support in the software you use.

[2]: https://web.dev/variable-fonts
