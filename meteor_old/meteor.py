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
        # Core Commands
        parser.add_argument('--environment', required=False, action='store', dest='environment', help=argparse.SUPPRESS)
        parser.add_argument('--validate', required=False, action='store_true', dest='validate', help=argparse.SUPPRESS)
        parser.add_argument('--test', required=False, action='store_true', dest='test', help=argparse.SUPPRESS)
        parser.add_argument('--deploy', required=False, action='store_true', dest='deploy', help=argparse.SUPPRESS)

        # Meteor Next Commands
        parser.add_argument('--execution_id', required=False, action='store', dest='execution_id', help=argparse.SUPPRESS)
        parser.add_argument('--execution_mode', required=False, action='store', dest='execution_mode', help=argparse.SUPPRESS)
        parser.add_argument('--execution_user', required=False, action='store', dest='execution_user', help=argparse.SUPPRESS)
        parser.add_argument('--execution_path', required=False, action='store', dest='execution_path', help=argparse.SUPPRESS)
        parser.add_argument('--execution_limit', required=False, action='store', dest='execution_limit', help=argparse.SUPPRESS)
        parser.add_argument('--execution_threads', required=False, action='store', dest='execution_threads', help=argparse.SUPPRESS)
        args = parser.parse_args()
        return args