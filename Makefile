NAME=Mada
VERSION=1.4
LATIN=SourceSansPro

SRCDIR=sources
DOCDIR=documentation
BUILDDIR=build
TOOLDIR=tools
TESTDIR=tests
DIST=$(NAME)-$(VERSION)

PY ?= python
PREPARE=$(TOOLDIR)/prepare.py
MKINST=$(TOOLDIR)/mkinstance.py
MKVF=$(TOOLDIR)/mkvf.py
MKSAMPLE=$(TOOLDIR)/mksample.py

SAMPLE="صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار"

SOURCES=ExtraLight Regular Black
FONTS=ExtraLight Light Regular Medium SemiBold Bold ExtraBold Black

UFO=$(SOURCES:%=$(BUILDDIR)/$(NAME)-%.ufo)
OTF=$(FONTS:%=$(NAME)-%.otf)
TTF=$(FONTS:%=$(NAME)-%.ttf)
OTM=$(SOURCES:%=$(BUILDDIR)/$(NAME)-%.otf)
TTM=$(SOURCES:%=$(BUILDDIR)/$(NAME)-%.ttf)
OTV=$(NAME).otf
TTV=$(NAME).ttf
SVG=FontSample.svg
SMP=$(FONTS:%=$(BUILDDIR)/$(NAME)-%.svg)

export SOURCE_DATE_EPOCH ?= 0

all: otf doc

otf: $(OTF)
ttf: $(TTF)
otv: $(OTV)
ttv: $(TTV)
doc: $(SVG)

SHELL=/usr/bin/env bash

.SECONDARY:

define generate_source
@echo "   SOURCE    $(notdir $(3))"
fontmake -u $(abspath $(2))                                                    \
         --output=$(1)                                                         \
         --verbose=WARNING                                                     \
         --production-names                                                    \
         --optimize-cff=0                                                      \
         --keep-overlaps                                                       \
	 --output-path=$(3)                                                    \
         ;
endef

$(BUILDDIR):
	@mkdir -p $(BUILDDIR)

$(NAME)-%.otf: $(OTV) $(BUILDDIR)/$(NAME).designspace
	@echo " INSTANCE    $(@F)"
	@$(PY) $(MKINST) $(BUILDDIR)/$(NAME).designspace $< $@

$(NAME)-%.ttf: $(TTV) $(BUILDDIR)/$(NAME).designspace
	@echo " INSTANCE    $(@F)"
	@$(PY) $(MKINST) $(BUILDDIR)/$(NAME).designspace $< $@

$(BUILDDIR)/$(NAME)-%.otf: $(BUILDDIR)/$(NAME)-%.ufo
	@$(call generate_source,otf,$<,$@)

$(BUILDDIR)/$(NAME)-%.ttf: $(BUILDDIR)/$(NAME)-%.ufo
	@$(call generate_source,ttf,$<,$@)

$(OTV): $(OTM) $(UFO) $(BUILDDIR)/$(NAME).designspace
	@echo " VARIABLE    $(@F)"
	@$(PY) $(MKVF) $(BUILDDIR)/$(NAME).designspace $@

$(TTV): $(TTM) $(UFO) $(BUILDDIR)/$(NAME).designspace
	@echo " VARIABLE    $(@F)"
	@$(PY) $(MKVF) $(BUILDDIR)/$(NAME).designspace $@

$(BUILDDIR)/$(NAME)-%.ufo: $(SRCDIR)/$(NAME).glyphs $(SRCDIR)/$(LATIN)/Roman/Instances/%/font.ufo $(PREPARE) $(BUILDDIR)
	@echo "     PREP    $(@F)"
	@$(PY) $(PREPARE) --version=$(VERSION) --out-file=$@ $< $(word 2,$+)

$(BUILDDIR)/$(NAME).designspace: $(SRCDIR)/$(NAME).designspace $(BUILDDIR)
	@echo "      GEN    $(@F)"
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
