if "__main__" == __name__:
	from sys import argv, stderr
	WB = XLSFile();
	jswb = WB.readfile(argv[1]);
	print >>stderr, WB.sheetnames() 
	print utils.csvify(WB.sheet(1))
