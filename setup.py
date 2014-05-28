from distutils.core import setup
setup(
	name='xls',
	version='0.1.1',
	author='SheetJS',
	author_email='dev@sheetjs.com',
	url='https://github.com/SheetJS/py-xls',
	description='XLS Parsing (from js-xls)',
	long_description = """
	Extract data from XLS Spreadsheets.

	This uses the js-xls library <http://oss.sheetjs.com/js-xls> and PyV8.
""",
	platforms = ["Any platform that supports PyV8"],
	requires=['PyV8'],
	install_requires=['PyV8'],
	py_modules=['xls'],
	scripts = [
		'scripts/xls2csv.py'
	],
	license = "Apache-2.0",
	keywords = ['xls', 'excel', 'spreadsheet', 'csv'],
	classifiers = [
		'Development Status :: 3 - Alpha',
		'License :: OSI Approved :: Apache Software License',
		'Topic :: Office/Business',
		'Topic :: Utilities',
	]
)
