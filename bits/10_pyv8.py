import PyV8, base64

class _MyConsole(PyV8.JSClass):
    def log(self, *args):
        print(" ".join([str(x) for x in args]))
    def error(self, *args):
        print >>stderr, " ".join([str(x) for x in args])

class GlobalContext(PyV8.JSClass):
    console = _MyConsole()

