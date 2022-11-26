NAME=Mada

SOURCEDIR = sources
FONTDIR = fonts
SCRIPTDIR = scripts
BUILDDIR = build
DIST = ${NAME}-${VERSION}

PY ?= python

SAMPLE = "صف خلق خود كمثل ٱلشمس إذ بزغت يحظى ٱلضجيع بها نجلاء معطار"

GLYPHS = ${SOURCEDIR}/${NAME}.glyphs
TTF = ${FONTDIR}/${NAME}.ttf
DTTF = ${BUILDDIR}/${NAME}.ttf

SVG = FontSample.svg

FMOPTS = --verbose=WARNING --master-dir="{tmp}"

TAG=$(shell git describe --tags --abbrev=0)
VERSION=$(TAG:v%=%)

export SOURCE_DATE_EPOCH ?= $(shell stat -c "%Y" ${GLYPHS})

all: ttf doc

ttf: ${TTF}
doc: ${SVG}

SHELL=/usr/bin/env bash
MAKEFLAGS := -s -r

.SECONDARY:

${TTF}: ${GLYPHS}
	echo " VARIABLE    $(@F)"
	fontmake $< --output-path=$@ -o variable ${FMOPTS} --flatten-components --filter DecomposeTransformedComponentsFilter

${DTTF}: ${TTF}
	echo " DIST        $(@F)"
	mkdir -p ${BUILDDIR}
	${PY} ${SCRIPTDIR}/dist.py $< $@ ${VERSION}

${SVG}: ${TTF}
	echo " SAMPLE      $(@F)"
	${PY} ${SCRIPTDIR}/mksample.py -t ${SAMPLE} -o $@ $<

dist: ${DTTF} ${SVG}
	echo " DIST        ${DIST}"
	install -Dm644 -t ${DIST} ${DTTF}
	install -Dm644 -t ${DIST} OFL.txt
	install -Dm644 -t ${DIST} README.md
	echo " ZIP         ${DIST}"
	zip -q -r ${DIST}.zip ${DIST}

clean:
	rm -rf ${BUILDDIR} ${TTF} ${SVG} ${DIST} ${DIST}.zip
