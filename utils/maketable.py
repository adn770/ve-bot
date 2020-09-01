#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2020 Josep Torra
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# pylint: skip-file

"""
maketable

Tool to create random tables in json

Usage:
    maketable [options] FILENAME

Options:
    -h --help             Show this message
    --version             Show version
    --log-level=LEVEL     Level of logging to produce [default: INFO]
    --log-file=PATH       Specify a file to write the log
    -v --verbose          Verbose logging (equivalent to --log-level=DEBUG)

Log levels:  DEBUG INFO WARNING ERROR CRITICAL

"""

import json
import logging
import sys
from os import path

from docopt import docopt


def load_file_from_disk(filename):
    """Loads a file from disk"""
    with open(filename, "r") as handle:
        return handle.readlines()


def main():
    """main"""
    args = docopt(__doc__, version="0.1")

    if args.pop('--verbose'):
        loglevel = 'DEBUG'
    else:
        loglevel = args.pop('--log-level').upper()

    logging.basicConfig(filename=args.pop('--log-file'), filemode='w',
                        level=loglevel, format='%(levelname)s: %(message)s')

    filename = args.pop('FILENAME')
    if not path.isfile(filename):
        logging.error('File "%s" not found', filename)
        sys.exit(-1)

    lines = load_file_from_disk(filename)
    count = len(lines)
    entries = []
    for (eid, line) in enumerate(lines, 1):
        line = line.strip()
        entries += [{"Id": str(eid), "Details": line}]

    table = {"Id": "undefined", "Title": "undefined title", "Type": 2,
             "Die": f"1d{count}", "Pages": entries}

    print(json.dumps(table, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
