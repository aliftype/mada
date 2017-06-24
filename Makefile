NAME=Mada
VERSION=1.4
LATIN=SourceSansPro

SRCDIR=sources
DOCDIR=documentation
BLDDIR=build
LATIN_SUBSET=$(SRCDIR)/latin-subset.txt
TOOLDIR=tools
TESTDIR=tests
DIST=$(NAME)-$(VERSION)

PY ?= python
PREPARE=$(TOOLDIR)/prepare.py

MASTERS=Light Regular Black
FONTS=Light Regular SemiBold Bold Black

UFO=$(MASTERS:%=$(BLDDIR)/$(NAME)-%.ufo)
OTF=$(FONTS:%=$(NAME)-%.otf)
TTF=$(FONTS:%=$(NAME)-%.ttf)
VF =$(NAME)-VF.ttf
PDF=$(DOCDIR)/$(NAME)-Table.pdf
PNG=$(DOCDIR)/$(NAME)-Sample.png

all: otf doc

otf: $(OTF)
ttf: $(TTF)
vf:  $(VF)
doc: $(PDF) $(PNG)

SHELL=/usr/bin/env bash

define prepare_masters
echo "   GEN   $(4)"
mkdir -p $(BLDDIR)
$(PY) $(PREPARE) --version=$(VERSION)                                          \
                 --feature-file=$(3)                                           \
                 --out-file=$(4)                                               \
                 --latin-subset=$(LATIN_SUBSET)                                \
                 $(1) $(2)
endef

define generate_fonts
echo "   MAKE  $(1)"
mkdir -p $(BLDDIR)
pushd $(BLDDIR) 1>/dev/null;                                                   \
fontmake --mm-designspace $(NAME).designspace                                  \
         $(if $(filter-out $(1),variable),--interpolate)                       \
         --autohint                                                            \
         --output $(1)                                                         \
         --verbose WARNING                                                     \
         ;                                                                     \
popd 1>/dev/null
endef

define subset_fonts
echo "   SUB   $(2)"
pyftsubset $(1)                                                                \
           --unicodes='*'                                                      \
           --layout_features='*'                                               \
           --name-IDs='*'                                                      \
           --notdef-outline                                                    \
           --glyph-names                                                       \
           --recalc-average-width                                              \
           --output-file=$(2)                                                  \
           ;
endef

$(VF): $(BLDDIR)/variable_ttf/$(VF)
	@$(call subset_fonts,$<,$@)

$(NAME)-%.otf: $(BLDDIR)/instance_otf/$(NAME)-%.otf
	@$(call subset_fonts,$<,$@)

$(NAME)-%.ttf: $(BLDDIR)/instance_ttf/$(NAME)-%.ttf
	@$(call subset_fonts,$<,$@)

$(BLDDIR)/instance_otf/$(NAME)-%.otf: $(UFO) $(BLDDIR)/$(NAME).designspace
	@$(call generate_fonts,otf)

$(BLDDIR)/instance_ttf/$(NAME)-%.ttf: $(UFO) $(BLDDIR)/$(NAME).designspace
	@$(call generate_fonts,ttf)

$(BLDDIR)/variable_ttf/$(VF): $(UFO) $(BLDDIR)/$(NAME).designspace
	@$(call generate_fonts,variable)

$(BLDDIR)/$(NAME)-%.ufo: $(SRCDIR)/$(NAME)-%.ufo $(SRCDIR)/$(LATIN)/Roman/%/font.ufo $(SRCDIR)/$(NAME).fea $(SRCDIR)/$(NAME).designspace $(PREPARE)
	@$(call prepare_masters,$<,$(word 2,$+),$(word 3,$+),$@)

$(SRCDIR)/$(LATIN)/Roman/%/font.ufo:
	@echo "   GET	$@"
	@if [ ! -f $@ ]; then git submodule init; git submodule update; fi

$(BLDDIR)/$(NAME).designspace: $(SRCDIR)/$(NAME).designspace
	@echo "   GEN   $@"
	@mkdir -p $(BLDDIR)
	@cp $< $@

$(PDF): $(NAME)-Regular.otf
	@echo "   GEN	$@"
	@mkdir -p $(DOCDIR)
	@fntsample --font-file $< --output-file $@.tmp --print-outline > $@.txt
	@pdfoutline $@.tmp $@.txt $@.comp
	@pdftk $@.comp output $@ uncompress
	@rm -f $@.tmp $@.comp $@.txt

$(PNG): $(DOCDIR)/$(NAME)-Sample.tex $(OTF)
	@echo "   GEN	$@"
	@xetex --interaction=batchmode $< &> /dev/null
	@pdfcrop $(NAME)-Sample.pdf &> /dev/null
	@rm $(NAME)-Sample.{pdf,log}
	@pdftocairo -png -r 600 $(NAME)-Sample-crop.pdf
	@rm $(NAME)-Sample-crop.pdf
	@mv $(NAME)-Sample-crop-1.png $@

dist: ttf vf
	@mkdir -p $(NAME)-$(VERSION)/{ttf,vf}
	@cp $(OTF) $(PDF) $(NAME)-$(VERSION)
	@cp $(TTF) $(NAME)-$(VERSION)/ttf
	@cp $(VF)  $(NAME)-$(VERSION)/vf
	@cp OFL.txt $(NAME)-$(VERSION)
	@markdown README.md | w3m -dump -T text/html | sed -e "/^Sample$$/d" > $(NAME)-$(VERSION)/README.txt
	@zip -r $(NAME)-$(VERSION).zip $(NAME)-$(VERSION)

clean:
	@rm -rf $(BLDDIR) $(OTF) $(PDF) $(NAME)-$(VERSION) $(NAME)-$(VERSION).zip
