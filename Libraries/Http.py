try:
    import sys
    import urllib3
except ImportError:
    sys.exit("""You need urllib3!
                install it from http://pypi.python.org/pypi
                or run pip install urllib3""")

class Http:
    """Http mapper class"""

    def connect(url):
        print "It Works!"
