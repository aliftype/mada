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
MKSLANT=$(TOOLDIR)/mkslant.py
BUILD=$(TOOLDIR)/build.py

SAMPLE="صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار"

MASTERS=ExtraLight Regular Black ExtraLightItalic BlackItalic ExtraLightSlanted BlackSlanted
FONTS=ExtraLight Light Regular Medium SemiBold Bold Black \
      ExtraLightItalic LightItalic Italic MediumItalic SemiBoldItalic BoldItalic BlackItalic

UFO=$(MASTERS:%=$(BLDDIR)/$(NAME)-%.ufo)
OTF=$(FONTS:%=$(NAME)-%.otf)
TTF=$(FONTS:%=$(NAME)-%.ttf)
TFV=$(NAME)-VF.ttf
PDF=$(DOCDIR)/FontTable.pdf
PNG=$(DOCDIR)/FontSample.png
SMP=$(FONTS:%=%.png)

all: otf vf doc

otf: $(OTF)
ttf: $(TTF)
vf:  $(TFV)
doc: $(PDF) $(PNG)

SHELL=/usr/bin/env bash

.PRECIOUS: $(BLDDIR)/master_otf/$(NAME)-%.otf                                  \
	$(BLDDIR)/master_ttf/$(NAME)-%.ttf                                     \
	$(BLDDIR)/instance_ufo/$(NAME)-%.ufo

define prepare_masters
echo "   MASTER    $(notdir $(4))"
mkdir -p $(BLDDIR)
$(PY) $(PREPARE) --version=$(VERSION)                                          \
                 --feature-file=$(3)                                           \
                 --out-file=$(4)                                               \
                 $(1) $(2)
endef

define generate_fonts
echo "     MAKE    $(if $(2),$(basename $(notdir $(2))).$(1),$(1))"
mkdir -p $(BLDDIR)
cd $(BLDDIR);                                                                  \
$(PY) $(abspath $(BUILD)) --designspace=$(NAME).designspace                    \
               --source=$(abspath $(SRCDIR))                                   \
               --build=$(abspath $(BUILDDIR))                                  \
               $(if $(2),--ufo=$(abspath $(2)))                                \
               --output=$(1)
endef

$(TFV): $(BLDDIR)/variable_ttf/$(TFV)
	@cp $< $@

$(NAME)-%.otf: $(BLDDIR)/master_otf/$(NAME)-%.otf
	@cp $< $@

$(NAME)-%.ttf: $(BLDDIR)/master_ttf/$(NAME)-%.ttf
	@cp $< $@

$(BLDDIR)/instance_ufo/$(NAME)-%.ufo: $(UFO) $(BLDDIR)/$(NAME).designspace
	@echo "     INST    $(@F)"
	@$(PY) -c                                                              \
	  "from mutatorMath.ufo.document import DesignSpaceDocumentReader as R;\
	   r = R('$(BLDDIR)/$(NAME).designspace', ufoVersion=3);               \
	   r.readInstance(('postscriptfontname', '$(basename $(@F))'))"

$(BLDDIR)/master_otf/$(NAME)-%.otf: $(BLDDIR)/instance_ufo/$(NAME)-%.ufo
	@$(call generate_fonts,otf,$<)

$(BLDDIR)/master_ttf/$(NAME)-%.ttf: $(BLDDIR)/instance_ufo/$(NAME)-%.ufo
	@$(call generate_fonts,ttf,$<)

$(BLDDIR)/variable_ttf/$(TFV): $(UFO) $(BLDDIR)/$(NAME).designspace
	@$(call generate_fonts,variable)

$(BLDDIR)/$(NAME)-ExtraLightItalic.ufo: $(BLDDIR)/$(NAME)-ExtraLight.ufo
	@echo "    SLANT    $(@F)"
	@$(PY) $(MKSLANT) $< $@ -15

$(BLDDIR)/$(NAME)-BlackItalic.ufo: $(BLDDIR)/$(NAME)-Black.ufo
	@echo "    SLANT    $(@F)"
	@$(PY) $(MKSLANT) $< $@ -15

$(BLDDIR)/$(NAME)-ExtraLightSlanted.ufo: $(BLDDIR)/$(NAME)-ExtraLight.ufo
	@echo "    SLANT    $(@F)"
	@$(PY) $(MKSLANT) $< $@ 15

$(BLDDIR)/$(NAME)-BlackSlanted.ufo: $(BLDDIR)/$(NAME)-Black.ufo
	@echo "    SLANT    $(@F)"
	@$(PY) $(MKSLANT) $< $@ 15

$(BLDDIR)/$(NAME)-%.ufo: $(SRCDIR)/$(NAME)-%.ufo $(SRCDIR)/$(LATIN)/Roman/Instances/%/font.ufo $(SRCDIR)/$(NAME).fea $(PREPARE)
	@echo "     PREP    $(@F)"
	@rm -rf $@
	@$(PY) $(PREPARE) --version=$(VERSION) --out-file=$@ $< $(word 2,$+)

$(BLDDIR)/$(NAME).designspace: $(SRCDIR)/$(NAME).designspace
	@echo "      GEN    $(@F)"
	@mkdir -p $(BLDDIR)
	@cp $< $@

$(PDF): $(NAME)-Regular.otf
	@echo "   SAMPLE    $(@F)"
	@mkdir -p $(DOCDIR)
	@fntsample --font-file $< --output-file $@.tmp --use-pango --write-outline
	@mutool clean -d -i -f -a $@.tmp $@ &> /dev/null || cp $@.tmp $@
	@rm -f $@.tmp

$(PNG): $(OTF)
	@echo "   SAMPLE    $(@F)"
	@for f in $(FONTS); do \
	  hb-view $(NAME)-$$f.otf $(SAMPLE) --font-size=130 > $$f.png; \
	 done
	@convert $(SMP) -define png:exclude-chunks=date,time -gravity center -append $@
	@rm -rf $(SMP)

dist: otf ttf vf doc
	@echo "     DIST    $(NAME)-$(VERSION)"
	@mkdir -p $(NAME)-$(VERSION)/{ttf,vf}
	@cp $(OTF) $(PDF) $(NAME)-$(VERSION)
	@cp $(TTF) $(NAME)-$(VERSION)/ttf
	@cp $(TFV)  $(NAME)-$(VERSION)/vf
	@cp OFL.txt $(NAME)-$(VERSION)
	@sed -e "/^!\[Sample\].*./d" README.md > $(NAME)-$(VERSION)/README.txt
	@@echo "     ZIP    $(NAME)-$(VERSION)"
	@zip -rq $(NAME)-$(VERSION).zip $(NAME)-$(VERSION)

clean:
	@rm -rf $(BLDDIR) $(OTF) $(TTF) $(TFV) $(PDF) $(PNG) $(NAME)-$(VERSION) $(NAME)-$(VERSION).zip
