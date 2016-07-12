import argparse

class Args:
    """Console helper class"""
    def __init__(self):
        parser = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
        parser.add_argument('-u', '--url', help="URL or page to scan; -u http://example.com")
        parser.add_argument('-c', '--check', help="Directory scan eg --check=dir or subdomains --check=sub")
        parser.add_argument('-t', '--threads', help="Allowed threads")
        parser.add_argument('-d', '--delay', help="Delay between requests")
        parser.add_argument('-r', '--random-agents', help="Use random user agents")
        parser.add_argument('-p', '--proxy-list', help="Proxy list")
        args = parser.parse_args()
        return args