#!/usr/bin/env python
import xls
from sys import argv, stderr

filename = argv[1]
try:
	sheet = argv[2]
except:
	sheet = None

WB = xls.XLSFile(argv[1])
if sheet is None: sheet = WB.sheetnames(0)
print >>stderr, sheet
print xls.utils.csvify(WB.sheet(sheet))
