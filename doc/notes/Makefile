ALLHTML = architecture.html execution.html imports.html misc.html subversion.html timeline.html

all: ${ALLHTML}

clean:
	rm -f ${ALLHTML}

%.html: %.txt
	markdown < $< > $@

