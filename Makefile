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
MKSLANT=$(TOOLDIR)/mkslant.py
MKINST=$(TOOLDIR)/mkinstance.py
MKVF=$(TOOLDIR)/mkvf.py

SAMPLE="صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار"

MASTERS=ExtraLight Regular Black ExtraLightItalic Italic BlackItalic ExtraLightSlanted Slanted BlackSlanted
FONTS=ExtraLight Light Regular Medium SemiBold Bold Black \
      ExtraLightItalic LightItalic Italic MediumItalic SemiBoldItalic BoldItalic BlackItalic

UFO=$(MASTERS:%=$(BUILDDIR)/$(NAME)-%.ufo)
OTF=$(FONTS:%=$(NAME)-%.otf)
TTF=$(FONTS:%=$(NAME)-%.ttf)
OTM=$(MASTERS:%=$(BUILDDIR)/masters/$(NAME)-%.otf)
TTM=$(MASTERS:%=$(BUILDDIR)/masters/$(NAME)-%.ttf)
OTV=$(NAME).otf
TTV=$(NAME).ttf
PNG=FontSample.png
SMP=$(FONTS:%=%.png)

export SOURCE_DATE_EPOCH ?= 0

all: otf doc

otf: $(OTF)
ttf: $(TTF)
otv: $(OTV)
ttv: $(TTV)
doc: $(PNG)

SHELL=/usr/bin/env bash

.SECONDARY:

define prepare_masters
echo "   MASTER    $(notdir $(4))"
mkdir -p $(BUILDDIR)
$(PY) $(PREPARE) --version=$(VERSION)                                          \
                 --feature-file=$(3)                                           \
                 --out-file=$(4)                                               \
                 $(1) $(2)
endef

define generate_master
@echo "   MASTER    $(notdir $(3))"
mkdir -p $(BUILDDIR)/masters
PYTHONPATH=$(abspath $(TOOLDIR)):${PYTHONMATH}                                 \
fontmake -u $(abspath $(2))                                                    \
         --output=$(1)                                                         \
         --verbose=WARNING                                                     \
         --feature-writer KernFeatureWriter                                    \
         --feature-writer markFeatureWriter::MarkFeatureWriter                 \
         --production-names                                                    \
         --optimize-cff=0                                                      \
         --keep-overlaps                                                       \
	 --output-path=$(3)                                                    \
         ;
endef

define generate_variable
@echo " VARIABLE    $(notdir $(2))"
$(PY) $(MKVF)                                                                  \
        --output=$(2)                                                          \
        --master-finder="$(BUILDDIR)/masters/{stem}.$(1)"                      \
        $(BUILDDIR)/$(NAME).designspace                                        \
        ;
endef

define generate_instance
@echo " INSTANCE    $(notdir $(3))"
$(PY) $(MKINST)                                                                \
      $(BUILDDIR)/$(NAME).designspace                                          \
      $(1)                                                                     \
      $(NAME)-$(2)                                                             \
      $(3)                                                                     \
      ;
endef

$(NAME)-%.otf: $(OTV) $(BUILDDIR)/$(NAME).designspace
	@$(call generate_instance,$<,$(*F),$@)

$(NAME)-%.ttf: $(TTV) $(BUILDDIR)/$(NAME).designspace
	@$(call generate_instance,$<,$(*F),$@)

$(BUILDDIR)/masters/$(NAME)-%.otf: $(BUILDDIR)/$(NAME)-%.ufo
	@$(call generate_master,otf,$<,$@)

$(BUILDDIR)/masters/$(NAME)-%.ttf: $(BUILDDIR)/$(NAME)-%.ufo
	@$(call generate_master,ttf,$<,$@)

$(OTV): $(OTM) $(BUILDDIR)/$(NAME).designspace
	@$(call generate_variable,otf,$@)

$(TTV): $(TTM) $(BUILDDIR)/$(NAME).designspace
	@$(call generate_variable,ttf,$@)

$(BUILDDIR)/$(NAME)-ExtraLightItalic.ufo: $(BUILDDIR)/$(NAME)-ExtraLight.ufo
	@echo "    SLANT    $(@F)"
	@mkdir -p $(BUILDDIR)
	@$(PY) $(MKSLANT) $< $@ -15

$(BUILDDIR)/$(NAME)-Italic.ufo: $(BUILDDIR)/$(NAME)-Regular.ufo
	@echo "    SLANT    $(@F)"
	@mkdir -p $(BUILDDIR)
	@$(PY) $(MKSLANT) $< $@ -15

$(BUILDDIR)/$(NAME)-BlackItalic.ufo: $(BUILDDIR)/$(NAME)-Black.ufo
	@echo "    SLANT    $(@F)"
	@mkdir -p $(BUILDDIR)
	@$(PY) $(MKSLANT) $< $@ -15

$(BUILDDIR)/$(NAME)-ExtraLightSlanted.ufo: $(BUILDDIR)/$(NAME)-ExtraLight.ufo
	@echo "    SLANT    $(@F)"
	@mkdir -p $(BUILDDIR)
	@$(PY) $(MKSLANT) $< $@ 15

$(BUILDDIR)/$(NAME)-Slanted.ufo: $(BUILDDIR)/$(NAME)-Regular.ufo
	@echo "    SLANT    $(@F)"
	@mkdir -p $(BUILDDIR)
	@$(PY) $(MKSLANT) $< $@ 15

$(BUILDDIR)/$(NAME)-BlackSlanted.ufo: $(BUILDDIR)/$(NAME)-Black.ufo
	@echo "    SLANT    $(@F)"
	@mkdir -p $(BUILDDIR)
	@$(PY) $(MKSLANT) $< $@ 15

$(BUILDDIR)/$(NAME)-%.ufo: $(SRCDIR)/$(NAME)-%.ufo $(SRCDIR)/$(LATIN)/Roman/Instances/%/font.ufo $(SRCDIR)/$(NAME).fea $(PREPARE)
	@echo "     PREP    $(@F)"
	@rm -rf $@
	@mkdir -p $(BUILDDIR)
	@$(PY) $(PREPARE) --version=$(VERSION) --out-file=$@ $< $(word 2,$+)

$(BUILDDIR)/$(NAME).designspace: $(SRCDIR)/$(NAME).designspace
	@echo "      GEN    $(@F)"
	@mkdir -p $(BUILDDIR)
	@cp $< $@

$(PNG): $(OTF)
	@echo "   SAMPLE    $(@F)"
	@for f in $(FONTS); do \
	  hb-view $(NAME)-$$f.otf $(SAMPLE) --font-size=130 > $$f.png; \
	 done
	@convert $(SMP) -define png:exclude-chunks=date,time -gravity center -append $@
	@rm -rf $(SMP)

dist: otf ttf otv ttv doc
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
	@rm -rf $(BUILDDIR) $(OTF) $(TTF) $(OTV) $(TTV) $(PNG) $(NAME)-$(VERSION) $(NAME)-$(VERSION).zip
