NAME=Mada
VERSION=1.4
LATIN=SourceSansPro

SRCDIR=sources
DOCDIR=documentation
BLDDIR=build
TOOLDIR=tools
TESTDIR=tests
DIST=$(NAME)-$(VERSION)

PY ?= python
PREPARE=$(TOOLDIR)/prepare.py
BUILD=$(TOOLDIR)/build.py

SAMPLE="صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار"

MASTERS=Light Regular Black
FONTS=Light Regular Medium SemiBold Bold Black

UFO=$(MASTERS:%=$(BLDDIR)/$(NAME)-%.ufo)
OTF=$(FONTS:%=$(NAME)-%.otf)
TTF=$(FONTS:%=$(NAME)-%.ttf)
TFV=$(NAME)-VF.ttf
PDF=$(DOCDIR)/$(NAME)-Table.pdf
PNG=$(DOCDIR)/$(NAME)-Sample.png
SMP=$(FONTS:%=%.png)

all: otf vf doc

otf: $(OTF)
ttf: $(TTF)
vf:  $(TFV)
doc: $(PDF) $(PNG)

SHELL=/usr/bin/env bash

.PRECIOUS: $(BLDDIR)/instance_otf/$(NAME)-%.otf $(BLDDIR)/instance_ttf/$(NAME)-%.ttf

define prepare_masters
echo "   GEN   $(4)"
mkdir -p $(BLDDIR)
$(PY) $(PREPARE) --version=$(VERSION)                                          \
                 --feature-file=$(3)                                           \
                 --out-file=$(4)                                               \
                 $(1) $(2)
endef

define generate_fonts
echo "   MAKE  $(1)"
mkdir -p $(BLDDIR)
cd $(BLDDIR);                                                                  \
$(PY) $(abspath $(BUILD)) --designspace=$(NAME).designspace                    \
               --source=$(abspath $(SRCDIR))                                   \
               --build=$(abspath $(BUILDDIR))                                  \
               --output=$(1)
endef

$(TFV): $(BLDDIR)/variable_ttf/$(TFV)
	@cp $< $@

$(NAME)-%.otf: $(BLDDIR)/instance_otf/$(NAME)-%.otf
	@cp $< $@

$(NAME)-%.ttf: $(BLDDIR)/instance_ttf/$(NAME)-%.ttf
	@cp $< $@

$(BLDDIR)/instance_otf/$(NAME)-%.otf: $(UFO) $(BLDDIR)/$(NAME).designspace
	@$(call generate_fonts,otf)

$(BLDDIR)/instance_ttf/$(NAME)-%.ttf: $(UFO) $(BLDDIR)/$(NAME).designspace
	@$(call generate_fonts,ttf)

$(BLDDIR)/variable_ttf/$(TFV): $(UFO) $(BLDDIR)/$(NAME).designspace
	@$(call generate_fonts,variable)

$(BLDDIR)/$(NAME)-%.ufo: $(SRCDIR)/$(NAME)-%.ufo $(SRCDIR)/$(LATIN)/Roman/Instances/%/font.ufo $(SRCDIR)/$(NAME).fea $(PREPARE)
	@echo "   GEN	$@"
	@rm -rf $@
	@$(PY) $(PREPARE) --version=$(VERSION) --feature-file=$(word 3,$+) --out-file=$@ $< $(word 2,$+)

$(SRCDIR)/$(LATIN)/Roman/Instances/%/font.ufo:
	@echo "   GET	$@"
	@if [ ! -f $@ ]; then git submodule init; git submodule update; fi

$(BLDDIR)/$(NAME).designspace: $(SRCDIR)/$(NAME).designspace
	@echo "   GEN	$@"
	@mkdir -p $(BLDDIR)
	@cp $< $@

$(PDF): $(NAME)-Regular.otf
	@echo "   GEN	$@"
	@mkdir -p $(DOCDIR)
	@fntsample --font-file $< --output-file $@.tmp --use-pango --write-outline
	@mutool clean -d -i -f -a $@.tmp $@ &> /dev/null || cp $@.tmp $@
	@rm -f $@.tmp

$(PNG): $(OTF)
	@echo "   GEN	$@"
	@for f in $(FONTS); do \
	  hb-view $(NAME)-$$f.otf $(SAMPLE) --font-size=130 > $$f.png; \
	 done
	@convert $(SMP) -define png:exclude-chunks=date,time -gravity center -append $@
	@rm -rf $(SMP)

dist: ttf vf $(PDF)
	@@echo "   GEN   $(NAME)-$(VERSION)"
	@mkdir -p $(NAME)-$(VERSION)/{ttf,vf}
	@cp $(OTF) $(PDF) $(NAME)-$(VERSION)
	@cp $(TTF) $(NAME)-$(VERSION)/ttf
	@cp $(TFV)  $(NAME)-$(VERSION)/vf
	@cp OFL.txt $(NAME)-$(VERSION)
	@sed -e "/^!\[Sample\].*./d" README.md > $(NAME)-$(VERSION)/README.txt
	@@echo "   ZIP   $(NAME)-$(VERSION)"
	@zip -rq $(NAME)-$(VERSION).zip $(NAME)-$(VERSION)

clean:
	@rm -rf $(BLDDIR) $(OTF) $(TTF) $(TFV) $(PDF) $(PNG) $(NAME)-$(VERSION) $(NAME)-$(VERSION).zip
