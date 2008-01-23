def print_file(name, mode='r'):
    f = file(name, mode)
    print f.read()
    f.close()
    print

# read inital file
print "initial_file.txt: read in r mode"
print_file("initial_file.txt", "r")

print "initial_file.txt: read in r mode again"
print_file("initial_file.txt", "r")

print "initial_file.txt: read in r+ mode"
print_file("initial_file.txt", "r+")

print "initial_file.txt: read in a+ mode"
print_file("initial_file.txt", "a+")


print "initial_file.txt: read in w+ mode"
print_file("initial_file.txt", "w+")
                               
# simple write tests
f = file("file_1.txt", "w")
f.write("Write a new file, mode = 'w'\n")
f.close()

print "file_1.txt: write test"
print_file("file_1.txt")

f = file("file_2.txt", "w")
f.write("Write to file multiple times\n")
f.write("mode = 'w'\n")
f.close()

# read tests
print "file_2.txt: read in r mode"
print_file("file_2.txt", "r")

print "file_2.txt: read in r+ mode"
print_file("file_2.txt", "r+")

print "file_2.txt: read in a+ mode"
print_file("file_2.txt", "a+")

print "file_2.txt: read in w+ mode"
print_file("file_2.txt", "w+")

# append tests
f = file("file_3.txt", "w")
f.write("Text in w mode\n")
f.close()
f = file("file_3.txt", "a")
f.write("Text appended in\n")
f.write("a mode\n")
f.close()

print "file_3.txt: append test"
print_file("file_3.txt")

# rwa + modes tests here


# error tests
f = file("file_4.txt", 'w')
f.write("File for testing errors\n")
f.close()

print "Writing to read only files"
try:
    file("file_4.txt").write("a")
    print "Test failed"
except Exception, e:
    print e

print
print "Reading non-existant files"
try:
    file("non_existant.txt").read()
    print "Test failed"
except Exception, e:
    print e

print
print "Reading form write only files"
try:
    file("file_4.txt",'w').read()
    print "Test failed"
except Exception, e:
    print e

print
print "Reading form append only files"
try:
    file("file_4.txt",'a').read()
    print "Test failed"
except Exception, e:
    print e
