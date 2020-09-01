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
# pylint: disable=no-member
#

"""
Helper classes to manages books.
"""

import logging
import json
import glob
from enum import Enum
from os import path

import rolldice


def load_json_from_disk(filename):
    """Loads a json file from disk"""
    with open(filename, "r") as handle:
        return json.load(handle)


class BookType(Enum):
    """Book type"""
    MONSTER_MANUAL = 1
    TABLE = 2


class Page():  # pylint: disable=too-few-public-methods
    """A book page"""
    def __init__(self, json_dict: dict):
        for (key, value) in json_dict.items():
            self.add(key, value)

    @property
    def id_as_range(self):
        """Returns a range representing the Id"""
        values = self.Id.split("-")
        if len(values) == 1:
            return range(int(self.Id), int(self.Id)+1)
        return range(int(values[0]), int(values[1])+1)

    def add(self, key: str, value: any):
        """Adds info to the page"""
        self.__dict__[key] = value


class GroupOfPages():  # pylint: disable=too-few-public-methods
    """A book page"""
    __pages: list

    def __init__(self, page0: Page, page1: Page):
        self.__pages = [page0, page1]
        self.__gid = page0.Id

    @property
    def Id(self):  # pylint: disable=invalid-name
        """Getter for GroupOfPages Id"""
        return self.__gid

    @property
    def pages(self):
        """Getter for Pages"""
        return self.__pages

    @property
    def id_as_range(self):
        """Returns a range representing the Id"""
        values = self.Id.split("-")
        if len(values) == 1:
            return range(int(self.Id), int(self.Id)+1)
        return range(int(values[0]), int(values[1])+1)


class Book():
    """A book"""

    __bid: str
    __title: str
    __type: BookType
    _pages: dict
    library: object

    def __init__(self, json_file: str = "", book: dict = None):
        self.__bid = "undefined"
        self.__title = "undefined"
        self.__type = -1
        self._pages = None
        self.library = None
        if json_file:
            book = load_json_from_disk(json_file)
        self.load(book)

    @property
    def bid(self):
        """Getter for book id"""
        return self.__bid

    @property
    def title(self):
        """Getter for book title"""
        return self.__title

    @property
    def type(self):
        """Getter for book type"""
        return self.__type

    def load(self, book: dict, load_pages: bool = False):
        """Load the book pages into memory"""
        if not book:
            raise RuntimeError("book dictionary not provided")

        self._pages = dict()
        self.__bid = book["Id"]
        self.__title = book["Title"]
        self.__type = BookType(book["Type"])

        if not load_pages:
            return

        for page_dict in book['Pages']:
            page = self.make_page(page_dict)
            try:
                page0 = self._pages[page.Id]
                if isinstance(page0, GroupOfPages):
                    page0.add(page)
                    page = page0
                else:
                    page = GroupOfPages(page0, page)
            except KeyError:
                pass

            self._pages[page.Id] = page

    def make_page(self, page_dict: dict):  # pylint: disable=no-self-use
        """Make a page for the book"""
        return Page(page_dict)

    def index(self):
        """Returns the list of pages in the book"""
        result = self._pages.values()
        return result

    def search(self, pid: str):
        """Returns the page for the specified pid"""
        if not pid:
            return None

        try:
            page = self._pages[pid]
            return page
        except KeyError:
            pass
        return None


class MonsterPage(Page):  # pylint: disable=too-few-public-methods
    """Monster"""

    def roll(self, num: int = 1, die: str = "1d8"):
        """Rolls hp for the specified number of monsters"""
        factors = self.HP.split("+")
        die = f'{factors[0]} * {die}'
        hitppoints = []
        for _ in range(num):
            result, _ = rolldice.roll_dice(die)
            hitppoints += [result]
        return sorted(hitppoints)


class MonsterBook(Book):
    """Monster Manual"""

    def load(self, book: dict, load_pages: bool = True):
        """Load the book pages into memory"""
        super().load(book, True)
        logging.info('  %d monsters found', len(self._pages))

    def make_page(self, page_dict: dict):
        """Make a page for the monster book"""
        return MonsterPage(page_dict)


class TableEntry(Page):  # pylint: disable=too-few-public-methods
    """An entry in a table"""

    @property
    def result(self):
        """Returns a friendly description for this entry result"""
        details = self.Details
        count = 0
        if hasattr(self, 'Number') and self.Number:
            die = self.Number
            count, _ = rolldice.roll_dice(die)

        if count == 1:
            details = details.replace('#', 'un')
        elif count > 1:
            details = details.replace('#a', str(count))
            details = details.replace('#', str(count))
            details = details.replace('a$(-es)', 'es')
            details = details.replace('$(es)', 'es')
            details = details.replace('$', 's')

        details = details.replace('#a', '')
        details = details.replace('#', '')
        details = details.replace('$', '')
        details = details.replace('  ', ' ')
        return details

    def add(self, key: str, value: any):
        """Adds info to the page"""
        if key == 'Table':
            if value:
                self.__dict__[key] = Table(book=value)
            else:
                self.__dict__[key] = None
        else:
            self.__dict__[key] = value


class Table(Book):
    """A table is just a small book"""

    def load(self, book: dict, load_pages: bool = True):
        """Load the table entries into memory"""
        super().load(book, True)
        self.Die = book["Die"]  # pylint: disable=invalid-name
        if "forced_roll" in book:
            self.forced_roll = book["forced_roll"]

        # result operation
        self.rop = "replace"
        if "rop" in book:
            self.rop = book["rop"]
        logging.info('  %d entries found', len(self._pages))

    def make_page(self, page_dict: dict):
        """Make a table entry for the table"""
        return TableEntry(page_dict)

    def find(self, rid: str):
        """Finds all entries matching in the range IDs"""
        entries = []

        for entry in self._pages.values():
            if rid in entry.id_as_range:
                if isinstance(entry, GroupOfPages):
                    entries += entry.pages
                else:
                    entries += [entry]
        return entries

    def roll(self):
        """Rolls on a table and it's chained ones"""
        die = self.Die
        rid, _ = rolldice.roll_dice(die)
        if hasattr(self, "forced_roll") and self.forced_roll:
            rid = self.forced_roll

        logging.info("rolled %s in %s for %s", rid, self.Die, self.title)
        entries = self.find(rid)
        result = ""
        explanation = [f'{die} -> **{rid}**']
        for entry in entries:
            cresult = entry.result
            # explanation.append(f'**{entry.Id}**. {cresult}')
            if hasattr(entry, 'Table') and entry.Table:
                sresult, sexpl = entry.Table.roll()
                if sresult:
                    if entry.Table.rop == "replace":
                        cresult = sresult
                    elif entry.Table.rop == "append":
                        cresult = cresult + "\n" + sresult
                    elif entry.Table.rop == "concat":
                        cresult = cresult + sresult
                    explanation += sexpl
            result = result + "\n" + cresult

        logging.info('> %s\n%s', result, "\n".join(explanation))
        return result, explanation


class Library():
    """A collection of books"""
    settings: object
    __books: dict

    def __init__(self, settings: object):
        self.settings = settings
        self.load(settings.library_paths)

    def load(self, library_paths: list = None):
        """Load the books into memory"""
        self.__books = dict()

        for books_path in library_paths:
            files = glob.glob(path.join(books_path, '*.json'))
            for file in files:
                logging.info('loading book "%s', file)
                book = self.add_book(file)
                logging.info('  book "%s [%s]" loaded', book.title, book.bid)

    def add_book(self, file: str = None):
        """Add a book into the Library"""
        book = Book(file)
        if book.type == BookType.MONSTER_MANUAL:
            book = MonsterBook(file)
        elif book.type == BookType.TABLE:
            book = Table(file)
        book.library = self
        self.__books[book.bid] = book
        return book

    def index(self):
        """Returns the list of books in the library"""
        result = self.__books.values()
        return result

    def search(self, bid: str):
        """Returns the specified book"""
        bids = list(filter(lambda x: x.startswith(bid), self.__books.keys()))
        if len(bids) != 1:
            return None
        bid = bids[0]

        try:
            book = self.__books[bid]
            logging.info('found "%s [%s]" in the library', book.title, book.bid)
            return book
        except KeyError:
            pass
        return None
