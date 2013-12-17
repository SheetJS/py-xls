from distutils.core import setup
setup(
	name='xls',
	version='0.0.1',
	description='XLS Parsing (from js-xls)',
	author='SheetJS',
	author_email='dev@sheetjs.com',
	py_modules=['xls'],
	requires=['PyV8'],
)
