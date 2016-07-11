try:
    import httplib2
    import socket
    import sys
except ImportError:
    sys.exit("""You need httplib2, socket!
                install it from http://pypi.python.org/pypi
                or run pip install httplib2 socket .""")

class Http:
    """Http mapper class"""
    i = 12345

    def connect(url):
        print "It Works!"
