import csv
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation

import hashlib
import re
from ofxstatement.parser import StatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import StatementLine, Statement

__author__ = 'Chris Mayes'
__email__ = 'cmayes@cmay.es'
__version__ = '0.3.1'


def warning(*objs):
    print("WARNING: ", *objs, file=sys.stderr)


class BettermentPlugin(Plugin):
    """Plugin for Betterment CSV statements.

    Note that you can specify 'bank' and 'account' in ofxstatement's configuration file (accessible
    using the `ofxstatement edit-config` command or directly at
    `~/.local/share/ofxstatement/config.ini` (on Linux, at least).  Setting these values under the
    "betterment section" (i.e. "[betterment]") makes it easier for your personal finance application
    to recognize which account the file's data belongs to.

    Also note that transactions for zero amounts are filtered by default.  If you wish to include
    zero-amount transactions, set 'zero_filter' to 'false' in your settings.
    """

    def get_parser(self, fin):
        parser = BettermentParser(fin, self.settings.get('charset', 'utf-8'))
        parser.statement.bank_id = self.settings.get('bank', 'Betterment')
        parser.statement.account_id = self.settings.get('account', None)
        parser.statement.filter_zeros = str2bool(self.settings.get('filter_zeros', "true"))
        return parser


def process_balances(stmt):
    """
    Based on `ofxstatement.statement.recalculate_balance`. Uses the "Ending Balance" field
    from the Betterment transaction data for fetching the start and end balance for this statement.
    If the statement has no transactions, it is returned unmodified.

    :param stmt: The statement data to process.
    :return: Whether the balances were calculated.
    """
    if not stmt.lines:
        return False
    date_sorted_lines = sorted(stmt.lines, key=lambda k: k.date)
    first_line = date_sorted_lines[0]
    stmt.start_balance = (first_line.end_balance - first_line.amount)
    stmt.start_date = first_line.date
    last_line = date_sorted_lines[-1]
    stmt.end_balance = last_line.end_balance
    stmt.end_date = last_line.date
    return True


class BettermentParser(StatementParser):
    mappings = {"date": "Date Completed",
                "memo": "Transaction Description",
                "amount": "Amount"
                }
    date_format = "%Y-%m-%d %H:%M:%S %z"
    old_date_format = "%Y-%m-%d %H:%M:%S.%f"

    def __init__(self, fin, encoding):
        self.statement = Statement()
        self.fin = fin
        self.encoding = encoding

    def parse(self):
        """Read and parse statement

        Return Statement object

        May raise exceptions.ParseException on malformed input.
        """
        with open(self.fin, 'r', encoding=self.encoding) as fhandle:
            for line in csv.DictReader(fhandle):
                self.cur_record += 1
                if not line:
                    continue
                stmt_line = self.parse_record(line)
                if stmt_line:
                    stmt_line.assert_valid()
                    self.statement.lines.append(stmt_line)
            process_balances(self.statement)
            return self.statement

    def parse_record(self, line):
        san_line = {}
        for lkey, lval in line.items():
            san_line[lkey] = re.sub("\$", "", lval)

        stmt_line = StatementLine()
        for field, col in self.mappings.items():
            rawvalue = san_line[col]
            try:
                value = self.parse_value(rawvalue, field)
            except ValueError as e:
                # Invalid data line; skip it
                warning("Error parsing value '{}' on line '{}': {}".format(rawvalue, san_line, e))
                return None
            setattr(stmt_line, field, value)

        if self.statement.filter_zeros and stmt_line.amount == 0:
            return None

        try:
            stmt_line.end_balance = Decimal(san_line['Ending Balance'])
        except InvalidOperation:
            # Usually indicates a pending transaction
            return None

        # generate transaction id out of available data
        stmt_line.id = generate_stable_transaction_id(stmt_line)
        return stmt_line

    def parse_datetime(self, value):
        try:
            return datetime.strptime(value, self.date_format)
        except ValueError:
            return datetime.strptime(value, self.old_date_format)


def str2bool(v):
    """Converts a string to a boolean value.  From http://stackoverflow.com/a/715468"""
    return v.lower() in ("yes", "true", "t", "1")


def generate_stable_transaction_id(stmt_line):
    """Generates a stable, pseudo-unique id for given statement line.

    This function can be used in statement parsers when a real transaction id is
    not available in the source statement.
    """
    h = hashlib.sha256()
    if stmt_line.date is not None:
        h.update(str(stmt_line.date).encode('utf-8'))
    if stmt_line.memo is not None:
        h.update(stmt_line.memo.encode('utf-8'))
    if stmt_line.amount is not None:
        h.update(str(stmt_line.amount).encode('utf-8'))
    return h.hexdigest()
