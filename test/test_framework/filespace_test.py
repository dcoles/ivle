from TestFramework import *

filespace = TestFilespace({"initial_file.txt":"Initial file contents\n"})

global_space = {}
global_space['file'] = lambda filename, mode='r', bufsize=-1: filespace.openfile(filename, mode)
global_space['open'] = global_space['file']
global_space['raw_input'] = lambda x=None: raw_input()

execfile("file_test.py", global_space)


