from ofxstatement.plugin import Plugin
from ofxstatement.parser import CsvStatementParser
import re

from ofxstatement import statement

__author__ = 'Chris Mayes'
__email__ = 'cmayes@cmay.es'
__version__ = '0.1.0'


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
        encoding = self.settings.get('charset', 'utf-8')
        f = open(fin, 'r', encoding=encoding)
        parser = BettermentParser(f)
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
    :return: The statement with modified start_balance, end_balance, start_date, and_end_date.
    """
    if not stmt.lines:
        return False
    first_line = stmt.lines[0]
    stmt.start_balance = (first_line.end_balance - first_line.amount)
    stmt.end_balance = stmt.lines[-1].end_balance
    stmt.start_date = min(sl.date for sl in stmt.lines)
    stmt.end_date = max(sl.date for sl in stmt.lines)
    return True


class BettermentParser(CsvStatementParser):
    mappings = {"date": 4,
                "memo": 1,
                "amount": 2
                }
    date_format = "%Y-%m-%d %H:%M:%S.%f"

    def parse(self):
        stmt = super(BettermentParser, self).parse()
        process_balances(stmt)
        return stmt

    def parse_record(self, line):
        if self.cur_record == 1:
            return None

        san_line = []
        for lval in line:
            san_line.append(re.sub("\$", "", lval))

        sl = super(BettermentParser, self).parse_record(san_line)

        if self.statement.filter_zeros and is_zero(sl.amount):
            return None

        sl.end_balance = float(san_line[3])

        # generate transaction id out of available data
        sl.id = statement.generate_transaction_id(sl)
        return sl


def is_zero(fval):
    """Returns whether the given float is an approximation of zero."""
    return abs(fval - 0.0) <= 0.000001


def str2bool(v):
    """Converts a string to a boolean value.  From http://stackoverflow.com/a/715468"""
    return v.lower() in ("yes", "true", "t", "1")