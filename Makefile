# Copyright (C) 2013  SheetJS
.PHONY: src
src:
	#npm install xlsjs
	#cp node_modules/xlsjs/xls.js bits/50_xls.js
	curl https://raw.github.com/SheetJS/js-xls/master/xls.js | sed 's#\\#\\\\#g'> bits/50_xls.js
	cat bits/* > xls.py

.PHONY: push
push:
	python setup.py sdist upload
