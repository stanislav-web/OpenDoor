import argparse

class Help:
    """Console helper class"""
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='''My Description. And what a lovely description it is. ''',
            epilog="""All's well that ends well.""")
        parser.add_argument('--foo', type=int, default=42, help='FOO!')
        parser.add_argument('bar', nargs='*', default=[1, 2, 3], help='BAR!')
        args = parser.parse_args()


