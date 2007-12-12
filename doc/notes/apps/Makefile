ALLHTML = browser.html dispatch.html

all: ${ALLHTML}

clean:
	rm -f ${ALLHTML}

%.html: %.txt
	markdown < $< > $@

