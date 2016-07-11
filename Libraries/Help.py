import argparse

class Help:
    """Console helper class"""
    def __init__(self):
        parser = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('-u', '--url', help="URL or page to scan; -u http://example.com")
        parser.add_argument('-t', '--threads', help="Allowed threads")
        parser.add_argument('-c', '--connections', default='30',
                            help="Set the max number of simultaneous connections allowed, default=30")
        args = parser.parse_args()
        return args