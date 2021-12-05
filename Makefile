NAME=Mada
VERSION=1.4

SRCDIR=sources
BUILDDIR=build
DIST=$(NAME)-$(VERSION)

PY ?= python
PREPARE=prepare.py
MKSAMPLE=mksample.py

SAMPLE="صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار"

SOURCES=ExtraLight Black
INSTANCES=200 300 400 500 600 700 800 900

UFO=$(SOURCES:%=$(BUILDDIR)/$(NAME)-%.ufo)
SVG=FontSample.svg
SMP=$(INSTANCES:%=$(BUILDDIR)/$(NAME)-%.svg)

FMOPTS = --verbose=WARNING

export SOURCE_DATE_EPOCH ?= 0

all: otf doc

otf: $(NAME).otf
ttf: $(NAME).ttf
doc: $(SVG)

SHELL=/usr/bin/env bash

.SECONDARY:

$(NAME).otf: $(BUILDDIR)/$(NAME).designspace $(UFO)
	@echo " VARIABLE    $(@F)"
	@fontmake -m $< --output-path=$@ -o variable-cff2 $(FMOPTS)

$(NAME).ttf: $(BUILDDIR)/$(NAME).designspace $(UFO)
	@echo " VARIABLE    $(@F)"
	@fontmake -m $< --output-path=$@ -o variable $(FMOPTS)

$(BUILDDIR)/$(NAME)-%.ufo: $(NAME).glyphs $(PREPARE)
	@echo "     PREP    $(@F)"
	@mkdir -p $(BUILDDIR)
	@$(PY) $(PREPARE) --version=$(VERSION) --out-file=$@ $<

$(BUILDDIR)/$(NAME).designspace: $(NAME).designspace
	@echo "      GEN    $(@F)"
	@mkdir -p $(BUILDDIR)
	@cp $< $@

$(BUILDDIR)/$(NAME)-%.svg: $(NAME).otf
	@echo "      GEN    $(@F)"
	@hb-view $< $(SAMPLE) --font-size=130 --output-file=$@ --variations="wght=$*"

$(SVG): $(SMP)
	@echo "   SAMPLE    $(@F)"
	@$(PY) $(MKSAMPLE) -o $@ $+

dist: otf ttf doc
	@echo "     DIST    $(NAME)-$(VERSION)"
	@mkdir -p $(NAME)-$(VERSION)/ttf
	@cp $(NAME).otf $(NAME)-$(VERSION)
	@cp $(NAME).ttf $(NAME)-$(VERSION)/ttf
	@cp OFL.txt $(NAME)-$(VERSION)
	@sed -e "/^!\[Sample\].*./d" README.md > $(NAME)-$(VERSION)/README.txt
	@@echo "     ZIP    $(NAME)-$(VERSION)"
	@zip -rq $(NAME)-$(VERSION).zip $(NAME)-$(VERSION)

clean:
	@rm -rf $(BUILDDIR) $(OTF) $(TTF) $(OTV) $(TTV) $(SVG) $(NAME)-$(VERSION) $(NAME)-$(VERSION).zip
