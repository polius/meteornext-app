import secure_imports
import argparse
from core import core

# Execute Meteor using $ python meteor.py ...
if __name__ == '__main__':
    from meteor import meteor
    meteor()

class meteor:
    def __init__(self):
        self._args = self.__init_parser()
        core(self._args)

    def __init_parser(self):
        parser = argparse.ArgumentParser(description='meteor')
        parser.add_argument('--path', required=False, action='store', dest='path', help=argparse.SUPPRESS)
        parser.add_argument('--validate', required=False, action='store_true', dest='validate', help=argparse.SUPPRESS)
        parser.add_argument('--test', required=False, action='store_true', dest='test', help=argparse.SUPPRESS)
        parser.add_argument('--deploy', required=False, action='store_true', dest='deploy', help=argparse.SUPPRESS)
        # Region Commands
        parser.add_argument('--region', required=False, action='store', dest='region', help=argparse.SUPPRESS)
        parser.add_argument('--compress', required=False, action='store_true', dest='compress', help=argparse.SUPPRESS)
        args = parser.parse_args()
        return args