# Makefile - bin directory
# Do not commit

all: bin/trampoline bin/timount

bin:
	mkdir -p bin

bin/trampoline: bin trampoline/trampoline.c
	gcc -o bin/trampoline trampoline/trampoline.c
	sudo chown root bin/trampoline
	sudo chmod +s bin/trampoline

bin/timount: bin timount/timount.c
	gcc -o bin/timount timount/timount.c
