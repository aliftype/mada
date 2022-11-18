NAME=Mada

BUILDDIR = build
DIST = $(NAME)-$(VERSION)

PY ?= python
PREPARE = prepare.py
MKSAMPLE = mksample.py

SAMPLE = "صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار"

OTF = $(NAME).otf
TTF = $(NAME).ttf

SVG = FontSample.svg

FMOPTS = --verbose=WARNING --master-dir="{tmp}"

TAG=$(shell git describe --tags --abbrev=0)
VERSION=$(TAG:v%=%)

export SOURCE_DATE_EPOCH ?= $(shell stat -c "%Y" $(NAME).glyphs)

all: otf doc

otf: $(OTF)
ttf: $(TTF)
doc: $(SVG)

SHELL=/usr/bin/env bash
MAKEFLAGS := -s -r

.SECONDARY:

$(OTF): $(BUILDDIR)/$(NAME).glyphs
	echo " VARIABLE    $(@F)"
	fontmake $< --output-path=$@ -o variable-cff2 --optimize-cff=1 $(FMOPTS)
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
	$(PY) $(MKSAMPLE) -t $(SAMPLE) -o $@ $<

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
