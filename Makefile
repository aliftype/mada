NAME=Mada
VERSION=1.1
LATIN=SourceSansPro

SRCDIR=sources
DOCDIR=documentation
LATIN_SUBSET=$(SRCDIR)/latin-subset.txt
TOOLDIR=tools
TESTDIR=tests
DIST=$(NAME)-$(VERSION)

PY=python2
PY3=python3
BUILD=$(TOOLDIR)/build.py

FONTS=Light Regular Black

SFD=$(FONTS:%=$(SRCDIR)/$(NAME)-%.sfdir)
UFO=$(FONTS:%=$(SRCDIR)/$(NAME)-%.ufo)
OTF=$(FONTS:%=$(NAME)-%.otf)
TTF=$(FONTS:%=$(NAME)-%.ttf)
PDF=$(DOCDIR)/$(NAME)-Table.pdf

all: otf doc

otf: $(OTF)
ttf: $(TTF)
ufo: $(UFO)
doc: $(PDF)

$(SRCDIR)/$(NAME)-%.ufo: $(SRCDIR)/$(NAME)-%.sfdir
	@echo "   GEN	$@"
	@rm -rf $@
	@sfd2ufo $< $@

$(NAME)-%.otf $(NAME)-%.ttf: $(SRCDIR)/$(NAME)-%.ufo $(SRCDIR)/$(LATIN)/Roman/%/font.ufo $(SRCDIR)/$(NAME)-%.fea $(SRCDIR)/$(NAME).fea Makefile $(BUILD)
	@echo "   GEN	$@"
	@FILES=($+); $(PY3) $(BUILD) --version=$(VERSION) --out-file=$@ --feature-file=$${FILES[2]} --latin-subset=$(LATIN_SUBSET) $< $${FILES[1]}

#$(DOCDIR)/$(NAME)-table.pdf: $(NAME)-Regular.otf
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
