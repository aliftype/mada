NAME=Mada

SOURCEDIR = sources
FONTDIR = fonts
SCRIPTDIR = scripts
BUILDDIR = build
DIST = ${NAME}-${VERSION}

PY ?= python

SAMPLE = "صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار"

GLYPHS = ${SOURCEDIR}/${NAME}.glyphs
OTF = ${FONTDIR}/${NAME}.otf
TTF = ${FONTDIR}/${NAME}.ttf
DOTF = ${BUILDDIR}/${NAME}.otf
DTTF = ${BUILDDIR}/${NAME}.ttf

SVG = FontSample.svg

FMOPTS = --verbose=WARNING --master-dir="{tmp}"

TAG=$(shell git describe --tags --abbrev=0)
VERSION=$(TAG:v%=%)

export SOURCE_DATE_EPOCH ?= $(shell stat -c "%Y" ${GLYPHS})

all: otf doc

otf: ${OTF}
ttf: ${TTF}
doc: ${SVG}

SHELL=/usr/bin/env bash
MAKEFLAGS := -s -r

.SECONDARY:

${OTF}: ${GLYPHS}
	echo " VARIABLE    $(@F)"
	fontmake $< --output-path=$@ -o variable-cff2 --optimize-cff=1 ${FMOPTS}

${TTF}: ${GLYPHS}
	echo " VARIABLE    $(@F)"
	fontmake $< --output-path=$@ -o variable ${FMOPTS} --flatten-components --filter DecomposeTransformedComponentsFilter

${DTTF}: ${TTF}
	echo " DIST        $(@F)"
	mkdir -p ${BUILDDIR}
	${PY} ${SCRIPTDIR}/dist.py $< $@ ${VERSION}

${DOTF}: ${OTF}
	echo " DIST        $(@F)"
	mkdir -p ${BUILDDIR}
	${PY} ${SCRIPTDIR}/dist.py $< $@ ${VERSION}

${SVG}: ${OTF}
	echo " SAMPLE      $(@F)"
	${PY} ${SCRIPTDIR}/mksample.py -t ${SAMPLE} -o $@ $<

dist: ${DTTF} ${DOTF} ${SVG}
	echo " DIST        ${DIST}"
	install -Dm644 -t ${DIST} ${DOTF}
	install -Dm644 -t ${DIST}/ttf ${DTTF}
	install -Dm644 -t ${DIST} OFL.txt
	install -Dm644 -t ${DIST} README.md
	echo " ZIP         ${DIST}"
	zip -q -r ${DIST}.zip ${DIST}

clean:
	rm -rf ${BUILDDIR} ${OTF} ${TTF} ${SVG} ${DIST} ${DIST}.zip
