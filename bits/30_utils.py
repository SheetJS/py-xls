class Utils():
	def __init__(self):
		self._gc = GlobalContext();
		self.c = PyV8.JSContext(self._gc);
		self.c.enter();
		self.c.eval(xlsjscode);
		self._utils = self.c.locals['XLS'].utils; 

	def csvify(self, sheet):
		return self._utils.sheet_to_csv(sheet.ws if isinstance(sheet, XLSSheet) else sheet);


