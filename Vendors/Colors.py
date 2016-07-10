try:
    import sys
    from colorama import init
    from termcolor import colored
except ImportError:
    sys.exit("""You need colorama and termcolor!
                install it from http://pypi.python.org/pypi
                or run pip install colorama termcolor .""")

