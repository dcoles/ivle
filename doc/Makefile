ALLHTML = app_howto.html

all: ${ALLHTML}

clean:
	rm -f ${ALLHTML}

%.html: %.txt
	markdown < $< > $@

