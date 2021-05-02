NAME=Mada
VERSION=1.4
LATIN=SourceSansPro

SRCDIR=sources
BUILDDIR=build
DIST=$(NAME)-$(VERSION)

PY ?= python
PREPARE=prepare.py
MKSAMPLE=mksample.py

SAMPLE="صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار"

SOURCES=ExtraLight Regular Black
FONTS=ExtraLight Light Regular Medium SemiBold Bold ExtraBold Black

UFO=$(SOURCES:%=$(BUILDDIR)/$(NAME)-%.ufo)
OTF=$(FONTS:%=$(NAME)-%.otf)
TTF=$(FONTS:%=$(NAME)-%.ttf)
OTV=$(NAME).otf
TTV=$(NAME).ttf
SVG=FontSample.svg
SMP=$(FONTS:%=$(BUILDDIR)/$(NAME)-%.svg)

FMOPTS = --verbose=WARNING --overlaps-backend=pathops 

export SOURCE_DATE_EPOCH ?= 0

all: otv otf doc

otf: $(OTF)
ttf: $(TTF)
otv: $(OTV)
ttv: $(TTV)
doc: $(SVG)

SHELL=/usr/bin/env bash

.SECONDARY:

$(NAME)-%.otf: $(BUILDDIR)/$(NAME).designspace $(UFO)
	@echo " INSTANCE    $(@F)"
	@fontmake -m $< -i ".* $*" --output-path=$@ -o otf --optimize-cff=1 $(FMOPTS) 

$(NAME)-%.ttf: $(BUILDDIR)/$(NAME).designspace $(UFO)
	@echo " INSTANCE    $(@F)"
	@fontmake -m $< -i ".* $*" --output-path=$@ -o otf $(FMOPTS)

$(OTV): $(BUILDDIR)/$(NAME).designspace $(UFO)
	@echo " VARIABLE    $(@F)"
	@fontmake -m $< --output-path=$@ -o variable-cff2 --optimize-cff=1 $(FMOPTS)

$(TTV): $(BUILDDIR)/$(NAME).designspace $(UFO)
	@echo " VARIABLE    $(@F)"
	@fontmake -m $< --output-path=$@ -o variable $(FMOPTS)

$(BUILDDIR)/$(NAME)-%.ufo: $(NAME).glyphs $(LATIN)/Roman/Instances/%/font.ufo $(PREPARE)
	@echo "     PREP    $(@F)"
	@mkdir -p $(BUILDDIR)
	@$(PY) $(PREPARE) --version=$(VERSION) --out-file=$@ $< $(word 2,$+)

$(BUILDDIR)/$(NAME).designspace: $(NAME).designspace
	@echo "      GEN    $(@F)"
	@mkdir -p $(BUILDDIR)
	@cp $< $@

$(BUILDDIR)/$(NAME)-%.svg: $(NAME)-%.otf
	@echo "      GEN    $(@F)"
	@hb-view $< $(SAMPLE) --font-size=130 --output-file=$@

$(SVG): $(SMP)
	@echo "   SAMPLE    $(@F)"
	@$(PY) $(MKSAMPLE) -o $@ $+

dist: otf ttf doc
	@echo "     DIST    $(NAME)-$(VERSION)"
	@mkdir -p $(NAME)-$(VERSION)/{ttf,vf}
	@cp $(OTF) $(NAME)-$(VERSION)
	@cp $(TTF) $(NAME)-$(VERSION)/ttf
	@cp $(OTV)  $(NAME)-$(VERSION)/vf
	@cp $(TTV)  $(NAME)-$(VERSION)/vf
	@cp OFL.txt $(NAME)-$(VERSION)
	@sed -e "/^!\[Sample\].*./d" README.md > $(NAME)-$(VERSION)/README.txt
	@@echo "     ZIP    $(NAME)-$(VERSION)"
	@zip -rq $(NAME)-$(VERSION).zip $(NAME)-$(VERSION)

clean:
	@rm -rf $(BUILDDIR) $(OTF) $(TTF) $(OTV) $(TTV) $(SVG) $(NAME)-$(VERSION) $(NAME)-$(VERSION).zip
