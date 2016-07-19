NAME=Mada
VERSION=1.2
LATIN=SourceSansPro

SRCDIR=sources
DOCDIR=documentation
LATIN_SUBSET=$(SRCDIR)/latin-subset.txt
TOOLDIR=tools
TESTDIR=tests
DIST=$(NAME)-$(VERSION)

PY=python3
BUILD=$(TOOLDIR)/build.py

MASTERS=Light Medium Black
INSTANCES=ExtraLight Regular Semibold Bold
FONTS=$(MASTERS) $(INSTANCES)

MAS=$(MASTERS:%=$(SRCDIR)/$(NAME)-%.ufo)
INS=$(INSTANCES:%=$(SRCDIR)/$(NAME)-%.ufo)
OTF=$(FONTS:%=$(NAME)-%.otf)
TTF=$(FONTS:%=$(NAME)-%.ttf)
PDF=$(DOCDIR)/$(NAME)-Table.pdf

all: otf doc

otf: $(INS) $(OTF)
ttf: $(TTF)
doc: $(PDF)

SHELL=/usr/bin/env bash

$(SRCDIR)/%-ExtraLight.ufo $(SRCDIR)/%-Regular.ufo $(SRCDIR)/%-Semibold.ufo $(SRCDIR)/%-Bold.ufo: $(SRCDIR)/$(NAME).designspace $(MAS)
	@echo "   GEN	instances"
	@python2 -c "from mutatorMath.ufo import build; build('$<', outputUFOFormatVersion=3)"

$(NAME)-%.otf $(NAME)-%.ttf: $(SRCDIR)/$(NAME)-%.ufo $(SRCDIR)/$(LATIN)/Roman/%/font.ufo $(SRCDIR)/$(NAME).fea Makefile $(BUILD)
	@echo "   GEN	$@"
	@FILES=($+); $(PY) $(BUILD) --version=$(VERSION) --out-file=$@ --feature-file=$(SRCDIR)/$(NAME).fea --latin-subset=$(LATIN_SUBSET) $< $${FILES[1]}

$(DOCDIR)/$(NAME)-Table.pdf: $(NAME)-Regular.otf
	@echo "   GEN	$@"
	@mkdir -p $(DOCDIR)
	@fntsample --font-file $< --output-file $@.tmp --print-outline > $@.txt
	@pdfoutline $@.tmp $@.txt $@.comp
	@pdftk $@.comp output $@ uncompress
	@rm -f $@.tmp $@.comp $@.txt

dist: ttf
	@mkdir -p $(NAME)-$(VERSION)/ttf
	@cp $(OTF) $(PDF) $(NAME)-$(VERSION)
	@cp $(TTF) $(NAME)-$(VERSION)/ttf
	@cp OFL.txt $(NAME)-$(VERSION)
	@markdown README.md | w3m -dump -T text/html | sed -e "/^Sample$$/d" > $(NAME)-$(VERSION)/README.txt
	@zip -r $(NAME)-$(VERSION).zip $(NAME)-$(VERSION)

clean:
	@rm -rf $(OTF) $(PDF) $(NAME)-$(VERSION) $(NAME)-$(VERSION).zip
