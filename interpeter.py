import sys,parser
rootdir = "."
exec_file = None
verbose = False
i=1

while i<len(sys.argv):
	if sys.argv[i]=="--rootdir":
		rootdir = sys.argv[i+1]
		i+=2
	elif sys.argv[i]=="--run":
		exec_file = sys.argv[i+1]
		i+=2
	elif sys.argv[i]=="--verbose":
		verbose = True
		i+=1
	else:
		print("Invalid cmd parameter: "+str(sys.argv[i])) # Python 2: print("Invalid cmd parameter: {}".format(str(sys.argv[i])))
		sys.exit()

if exec_file is not None:
	parser.exec_block(open(exec_file).read())

while True:
	block = raw_input("csvdb>")
	while block[-1]!=";":
		block += raw_input("......")
	parser.exec_block(block,verbose=verbose,rootdir=rootdir)