NAME=mada
VERSION=1.0
LATIN=sourcesanspro

SRCDIR=sources
DOCDIR=documentation
TOOLDIR=tools
TESTDIR=tests
DIST=$(NAME)-$(VERSION)

PY=python2
PY3=python3
BUILD=$(TOOLDIR)/build.py
COMPOSE=$(TOOLDIR)/build-encoded-glyphs.py
#RUNTEST=$(TOOLDIR)/runtest.py
#SFDLINT=$(TOOLDIR)/sfdlint.py

FONTS=thin medium black
#TESTS=wb yeh-ragaa

SFD=$(FONTS:%=$(SRCDIR)/$(NAME)-%.sfdir)
OTF=$(FONTS:%=$(NAME)-%.otf)
TTF=$(FONTS:%=$(NAME)-%.ttf)
PDF=$(DOCDIR)/$(NAME)-table.pdf

#TST=$(TESTS:%=$(TESTDIR)/%.txt)
#SHP=$(TESTS:%=$(TESTDIR)/%.shp)
#RUN=$(TESTS:%=$(TESTDIR)/%.run)
#LNT=$(FONTS:%=$(TESTDIR)/$(NAME)-%.lnt)

ttx?=false
crunch?=false

#all: lint otf doc
all: otf doc

otf: $(OTF)
ttf: $(TTF)
doc: $(PDF)
#lint: $(LNT)
check: #lint $(RUN)

$(NAME)-%.otf: $(SRCDIR)/$(NAME)-%.sfdir $(SRCDIR)/$(LATIN)-%.sfdir $(SRCDIR)/$(NAME).fea Makefile $(BUILD)
	@echo "   FF	$@"
	@FILES=($+); $(PY) $(BUILD) --version=$(VERSION) --out-file=$@ --feature-file=$${FILES[2]} $${FILES[0]} $${FILES[1]}
ifeq ($(ttx), true)
	@echo "   TTX	$@"
	@pyftsubset $@ --output-file=$@.tmp --unicodes='*' --layout-features='*' --name-IDs='*'
	@mv $@.tmp $@
endif

$(NAME)-%.ttf: $(SRCDIR)/$(NAME)-%.sfdir $(SRCDIR)/$(LATIN)-%.sfdir $(SRCDIR)/$(NAME).fea Makefile $(BUILD)
	@echo "   FF	$@"
	@FILES=($+); $(PY) $(BUILD) --version=$(VERSION) --out-file=$@ --feature-file=$${FILES[2]} $${FILES[0]} $${FILES[1]}
ifeq ($(ttx), true)
	@echo "   TTX	$@"
	@pyftsubset $@ --output-file=$@.tmp --unicodes='*' --layout-features='*' --name-IDs='*'
	@mv $@.tmp $@
endif
ifeq ($(crunch), true)
	@echo "   FC	$@"
	@font-crunch -q -j8 -o $@ $@
endif


#$(TESTDIR)/%.run: $(TESTDIR)/%.txt $(TESTDIR)/%.shp $(NAME)-regular.otf
#	@echo "   TST	$*"
#	@$(PY3) $(RUNTEST) $(NAME)-regular.otf $(@D)/$*.txt $(@D)/$*.shp $(@D)/$*.run

#$(TESTDIR)/%.lnt: $(SRCDIR)/%.sfdir $(SFDLINT)
#	@echo "   LNT	$<"
#	@mkdir -p $(TESTDIR)
#	@$(PY) $(SFDLINT) $< $@

#$(DOCDIR)/$(NAME)-table.pdf: $(NAME)-regular.otf
$(DOCDIR)/$(NAME)-table.pdf: $(NAME)-medium.otf
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

dist:
	@make -B ttx=true crunch=false all ttf
	@mkdir -p $(NAME)-$(VERSION)/ttf
	@cp $(OTF) $(PDF) $(NAME)-$(VERSION)
	@cp $(TTF) $(NAME)-$(VERSION)/ttf
	@cp OFL.txt $(NAME)-$(VERSION)
	@markdown -v
	@markdown README.md | w3m -dump -T text/html | sed -e "/^Sample$$/d" > $(NAME)-$(VERSION)/README.txt
	@zip -r $(NAME)-$(VERSION).zip $(NAME)-$(VERSION)

clean:
	@rm -rf $(OTF) $(PDF) $(NAME)-$(VERSION) $(NAME)-$(VERSION).zip
