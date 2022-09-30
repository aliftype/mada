NAME=Mada
VERSION=1.4

MAKEFLAGS := -s -r

SRCDIR = sources
BUILDDIR = build
DIST = $(NAME)-$(VERSION)

PY ?= python
PREPARE = prepare.py
MKSAMPLE = mksample.py

SAMPLE = "صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار"

OTF = $(NAME).otf
TTF = $(NAME).ttf

SVG = FontSample.svg
INSTANCES = 200 300 400 500 600 700 800 900

FMOPTS = --verbose=WARNING --master-dir="{tmp}"

export SOURCE_DATE_EPOCH ?= 0

all: otf doc

otf: $(OTF)
ttf: $(TTF)
doc: $(SVG)

SHELL=/usr/bin/env bash

.SECONDARY:

$(OTF): $(BUILDDIR)/$(NAME).glyphs
	echo " VARIABLE    $(@F)"
	fontmake $< --output-path=$@ -o variable-cff2 $(FMOPTS)
	python3 update-stat.py $@

$(TTF): $(BUILDDIR)/$(NAME).glyphs
	echo " VARIABLE    $(@F)"
	fontmake $< --output-path=$@ -o variable $(FMOPTS)
	python3 update-stat.py $@

$(BUILDDIR)/$(NAME).glyphs: $(NAME).glyphs $(PREPARE)
	echo "     PREP    $(@F)"
	mkdir -p $(BUILDDIR)
	$(PY) $(PREPARE) $< $@ $(VERSION)

$(SVG): $(OTF)
	echo "   SAMPLE    $(@F)"
	$(PY) $(MKSAMPLE) -t $(SAMPLE) -l "$(INSTANCES)" -o $@ $<

dist: otf ttf doc
	echo "     DIST    $(DIST)"
	install -Dm644 -t $(DIST) $(OTF)
	install -Dm644 -t $(DIST)/ttf $(TTF)
	install -Dm644 -t $(DIST) OFL.txt
	install -Dm644 -t $(DIST) README.md
	echo "     ZIP     $(DIST)"
	zip -q -r $(DIST).zip $(DIST)

clean:
	rm -rf $(BUILDDIR) $(OTF) $(TTF) $(SVG) $(DIST) $(DIST).zip
