NAME=Mada
VERSION=1.0
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
COMPOSE=$(TOOLDIR)/build-encoded-glyphs.py
#RUNTEST=$(TOOLDIR)/runtest.py
#SFDLINT=$(TOOLDIR)/sfdlint.py

FONTS=Light Medium Black
#TESTS=wb yeh-ragaa

SFD=$(FONTS:%=$(SRCDIR)/$(NAME)-%.sfdir)
OTF=$(FONTS:%=$(NAME)-%.otf)
TTF=$(FONTS:%=$(NAME)-%.ttf)
PDF=$(DOCDIR)/$(NAME)-Table.pdf

#TST=$(TESTS:%=$(TESTDIR)/%.txt)
#SHP=$(TESTS:%=$(TESTDIR)/%.shp)
#RUN=$(TESTS:%=$(TESTDIR)/%.run)
#LNT=$(FONTS:%=$(TESTDIR)/$(NAME)-%.lnt)

#all: lint otf doc
all: otf doc

otf: $(OTF)
ttf: $(TTF)
doc: $(PDF)
#lint: $(LNT)
check: #lint $(RUN)

$(SRCDIR)/$(NAME)-%.ufo: $(SRCDIR)/$(NAME)-%.sfdir
	@echo "   GEN	$@"
	@rm -rf $@
	@sfd2ufo $< $@

$(NAME)-%.otf $(NAME)-%.ttf: $(SRCDIR)/$(NAME)-%.ufo $(SRCDIR)/$(LATIN)/Roman/%/font.ufo $(SRCDIR)/$(NAME)-%.fea $(SRCDIR)/$(NAME).fea Makefile $(BUILD)
	@echo "   GEN	$@"
	@FILES=($+); $(PY3) $(BUILD) --version=$(VERSION) --out-file=$@ --feature-file=$${FILES[2]} --latin-subset=$(LATIN_SUBSET) $< $${FILES[1]}

#$(TESTDIR)/%.run: $(TESTDIR)/%.txt $(TESTDIR)/%.shp $(NAME)-regular.otf
#	@echo "   TST	$*"
#	@$(PY3) $(RUNTEST) $(NAME)-regular.otf $(@D)/$*.txt $(@D)/$*.shp $(@D)/$*.run

#$(TESTDIR)/%.lnt: $(SRCDIR)/%.sfdir $(SFDLINT)
#	@echo "   LNT	$<"
#	@mkdir -p $(TESTDIR)
#	@$(PY) $(SFDLINT) $< $@

#$(DOCDIR)/$(NAME)-table.pdf: $(NAME)-Regular.otf
$(DOCDIR)/$(NAME)-Table.pdf: $(NAME)-Medium.otf
	@echo "   GEN	$@"
	@mkdir -p $(DOCDIR)
	@fntsample --font-file $< --output-file $@.tmp --print-outline > $@.txt
	@pdfoutline $@.tmp $@.txt $@.comp
	@pdftk $@.comp output $@ uncompress
	@rm -f $@.tmp $@.comp $@.txt

build-encoded-glyphs: $(SFD) $(SRCDIR)/$(NAME).fea
	@$(foreach sfd, $(SFD), \
	     echo "   CMP	"`basename $(sfd)`; \
	     $(PY) $(COMPOSE) $(sfd) $(SRCDIR)/$(NAME).fea; \
	  )

dist: ttf
	@mkdir -p $(NAME)-$(VERSION)/ttf
	@cp $(OTF) $(PDF) $(NAME)-$(VERSION)
	@cp $(TTF) $(NAME)-$(VERSION)/ttf
	@cp OFL.txt $(NAME)-$(VERSION)
	@markdown -v
	@markdown README.md | w3m -dump -T text/html | sed -e "/^Sample$$/d" > $(NAME)-$(VERSION)/README.txt
	@zip -r $(NAME)-$(VERSION).zip $(NAME)-$(VERSION)

clean:
	@rm -rf $(OTF) $(PDF) $(NAME)-$(VERSION) $(NAME)-$(VERSION).zip
