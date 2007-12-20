# Makefile - bin directory
# Do not commit

all: bin/trampoline

bin:
	mkdir -p bin

bin/trampoline: trampoline/trampoline.c
	gcc -o bin/trampoline trampoline/trampoline.c
	sudo chown root bin/trampoline
	sudo chmod +s bin/trampoline
