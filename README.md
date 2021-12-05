Mada
====

![Sample](FontSample.svg)

Mada (مدى) is a modernist, low contrast Arabic typeface based largely on the
typeface seen in Cairo metro old signage which was designed by Professor
Fathi Gouda of the Faculty of Applied Arts, Helwan University.

Mada is characterised by low descenders, open contours and low contrast forms
making it suitable for small point sizes, user interfaces, signage or low
resolution settings.

Mada can work also as a display typeface giving modernist and simplistic
feeling.

Mada is [variable font][2] that has all the font weights in the same file, and
allow dynamic changes of the font weight. Font weights supported by Mada range
from Extra Light to Black.

Building
--------

You need GNU Make and a few Python packages. To install the Python
requirements, run:

    pip install -r requirements.txt

Then to build the fonts:

    make otf # CFF-flavoured fonts
    make ttf # TTF-flavoured fonts

[2]: https://web.dev/variable-fonts
