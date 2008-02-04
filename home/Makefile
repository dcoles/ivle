
.PHONY: rsync

WEB = $(USER)@shell.sourceforge.net:/home/groups/i/iv/ivle/htdocs
RSYNC_OPTS = -arvz -e ssh --relative --cvs-exclude

rsync:
	rsync $(RSYNC_OPTS) index.html images $(WEB)



