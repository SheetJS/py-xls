#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""
XLS Parser

This module leverages js-xls <http://oss.sheetjs.com/js-xls/>

Requires PyV8 (javascript)

Sample usage:

>>> import xls
>>> filename = "formula_stress_test.xls" # http://oss.sheetjs.com/test_files/formula_stress_test.xls
>>> workbook = xls.XLSFile(filename)
>>> first_sheet_name = workbook.sheetnames(0)
>>> print xls.utils.csvify(workbook.sheet(sheet))

The supplied xls2csv.py binary generates CSV output from the XLS file.

For unported functions, the raw PyV8 object is available at `.wb`:

>>> raw_book = workbook.wb

Copyright (C) 2013  SheetJS
"""

