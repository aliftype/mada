NAME=Mada
VERSION=1.4
LATIN=SourceSansPro

SRCDIR=sources
DOCDIR=documentation
LATIN_SUBSET=$(SRCDIR)/latin-subset.txt
TOOLDIR=tools
TESTDIR=tests
DIST=$(NAME)-$(VERSION)

PY ?= python
BUILD=$(TOOLDIR)/build.py

MASTERS=Light Medium Black
INSTANCES=Regular SemiBold Bold
FONTS=$(MASTERS) $(INSTANCES)

MAS=$(MASTERS:%=$(SRCDIR)/$(NAME)-%.ufo)
INS=$(INSTANCES:%=$(SRCDIR)/$(NAME)-%.ufo)
OTF=$(FONTS:%=$(NAME)-%.otf)
TTF=$(FONTS:%=$(NAME)-%.ttf)
PDF=$(DOCDIR)/$(NAME)-Table.pdf
PNG=$(DOCDIR)/$(NAME)-Sample.png

all: otf doc

otf: $(INS) $(OTF)
ttf: $(TTF)
doc: $(PDF) $(PNG)

SHELL=/usr/bin/env bash

$(SRCDIR)/%-Regular.ufo $(SRCDIR)/%-SemiBold.ufo $(SRCDIR)/%-Bold.ufo: $(SRCDIR)/$(NAME).designspace $(MAS)
	@echo "   GEN	instances"
	@python2 -c "from mutatorMath.ufo import build; build('$<', outputUFOFormatVersion=3)"

# hack since Adobe names it Semibold but Dave wants SemiBold
$(SRCDIR)/$(LATIN)/Roman/SemiBold/font.ufo: $(SRCDIR)/$(LATIN)/Roman/Semibold/font.ufo
	@mkdir -p $@
	@rm -rf $@
	@cp -r $< $@

$(SRCDIR)/$(LATIN)/Roman/%/font.ufo:
	@echo "   GET	$@"
	@if [ ! -f $@ ]; then git submodule init; git submodule update; fi

$(NAME)-%.otf $(NAME)-%.ttf: $(SRCDIR)/$(NAME)-%.ufo $(SRCDIR)/$(LATIN)/Roman/%/font.ufo $(SRCDIR)/$(NAME).fea $(BUILD)
	@echo "   GEN	$@"
	@FILES=($+); $(PY) $(BUILD) --version=$(VERSION) --out-file=$@ --feature-file=$(SRCDIR)/$(NAME).fea --latin-subset=$(LATIN_SUBSET) $< $${FILES[1]}

$(DOCDIR)/$(NAME)-Table.pdf: $(NAME)-Regular.otf
	@echo "   GEN	$@"
	@mkdir -p $(DOCDIR)
	@fntsample --font-file $< --output-file $@.tmp --print-outline > $@.txt
	@pdfoutline $@.tmp $@.txt $@.comp
	@pdftk $@.comp output $@ uncompress
	@rm -f $@.tmp $@.comp $@.txt

$(DOCDIR)/$(NAME)-Sample.png: $(DOCDIR)/$(NAME)-Sample.tex $(OTF)
	@echo "   GEN	$@"
	@xetex --interaction=batchmode $< &> /dev/null
	@pdfcrop $(NAME)-Sample.pdf &> /dev/null
	@rm $(NAME)-Sample.{pdf,log}
	@pdftocairo -png -r 600 $(NAME)-Sample-crop.pdf
	@rm $(NAME)-Sample-crop.pdf
	@mv $(NAME)-Sample-crop-1.png $@

dist: ttf
	@mkdir -p $(NAME)-$(VERSION)/ttf
	@cp $(OTF) $(PDF) $(NAME)-$(VERSION)
	@cp $(TTF) $(NAME)-$(VERSION)/ttf
	@cp OFL.txt $(NAME)-$(VERSION)
	@markdown README.md | w3m -dump -T text/html | sed -e "/^Sample$$/d" > $(NAME)-$(VERSION)/README.txt
	@zip -r $(NAME)-$(VERSION).zip $(NAME)-$(VERSION)

clean:
	@rm -rf $(OTF) $(PDF) $(NAME)-$(VERSION) $(NAME)-$(VERSION).zip
