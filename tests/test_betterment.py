# coding=utf-8

"""
Tests for the ofxstatement Betterment plugin.
"""
from datetime import date
import logging
import unittest
from ofxstatement.statement import StatementLine

import os

from ofxstatement.plugins.betterment import BettermentPlugin, is_zero, generate_stable_transaction_id

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_betterment')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
ZERO_BAL_CSV_PATH = os.path.join(DATA_DIR, 'transactions.csv')
POS_CSV_PATH = os.path.join(DATA_DIR, 'transactions_positive.csv')
NOV_2015_CSV_PATH = os.path.join(DATA_DIR, 'transactions_11_2015.csv')
ALL_ZERO_CSV_PATH = os.path.join(DATA_DIR, 'transactions_zeros.csv')
HEADER_CSV_PATH = os.path.join(DATA_DIR, 'transactions_header.csv')
EMPTY_CSV_PATH = os.path.join(DATA_DIR, 'transactions_empty.csv')
BLANK_BAL_PATH = os.path.join(DATA_DIR, 'transactions_blankbal.csv')


# Shared Methods #


class TestBettermentStatement(unittest.TestCase):
    def testZeroBalance(self):
        """Statement starts with a zero balance."""
        stmt = BettermentPlugin(None, {}).get_parser(ZERO_BAL_CSV_PATH).parse()
        self.assertAlmostEqual(0.0, stmt.start_balance)
        self.assertAlmostEqual(817.44, stmt.end_balance)
        self.assertEqual(date(2015, 9, 22), to_date(stmt.start_date))
        self.assertEqual(date(2015, 9, 25), to_date(stmt.end_date))
        self.assertEqual(5, len(stmt.lines))
        for stline in stmt.lines:
            self.assertTrue(stline.memo in ('Initial Deposit from ****', 'Market Change'))
            self.assertFalse(is_zero(stline.amount))
            self.assertTrue(date(2015, 9, 25) >= to_date(stline.date) >= date(2015, 9, 22))

    def testPositiveBalance(self):
        """Statement starts with a positive balance."""
        stmt = BettermentPlugin(None, {}).get_parser(POS_CSV_PATH).parse()
        self.assertAlmostEqual(1000.0, stmt.start_balance)
        self.assertAlmostEqual(1817.44, stmt.end_balance)
        self.assertEqual(date(2015, 9, 22), to_date(stmt.start_date))
        self.assertEqual(date(2015, 9, 25), to_date(stmt.end_date))
        self.assertEqual(5, len(stmt.lines))
        for stline in stmt.lines:
            self.assertTrue(stline.memo in ('Initial Deposit from ****', 'Market Change'))
            self.assertFalse(is_zero(stline.amount))
            self.assertTrue(date(2015, 9, 25) >= to_date(stline.date) >= date(2015, 9, 22))

    def testPositiveBalanceNov2015(self):
        """Statement starts with a positive balance and the new November 2015 CSV format."""
        stmt = BettermentPlugin(None, {}).get_parser(NOV_2015_CSV_PATH).parse()
        self.assertAlmostEqual(1631.25, stmt.start_balance)
        self.assertAlmostEqual(1254.43, stmt.end_balance)
        self.assertEqual(date(2015, 10, 29), to_date(stmt.start_date))
        self.assertEqual(date(2015, 11, 11), to_date(stmt.end_date))
        self.assertEqual(12, len(stmt.lines))
        for stline in stmt.lines:
            self.assertTrue(stline.memo in ('Initial Deposit from ****', 'Market Change', 'Dividend'))
            self.assertFalse(is_zero(stline.amount))
            self.assertTrue(date(2015, 11, 11) >= to_date(stline.date) >= date(2015, 10, 29))

class TestBettermentSettings(unittest.TestCase):
    def testAccountNoFilterZeros(self):
        """Set an account and disable zero-value transaction filtering."""
        stmt = BettermentPlugin(None, {'account': '12345', 'filter_zeros': 'false'}
                                ).get_parser(ZERO_BAL_CSV_PATH).parse()
        self.assertEqual(stmt.account_id, '12345')
        self.assertEqual(stmt.bank_id, 'Betterment')
        # Check that the zero balance lines are present
        self.assertEqual(7, len(stmt.lines))

    def testBankNoFilterZeros(self):
        """Set a custom bank and filter zero-value transactions."""
        stmt = BettermentPlugin(None, {'bank': 'CustomBank', 'filter_zeros': 'true'}
                                ).get_parser(ZERO_BAL_CSV_PATH).parse()
        self.assertIsNone(stmt.account_id)
        self.assertEqual(stmt.bank_id, 'CustomBank')
        # Check that the zero balance lines are present
        self.assertEqual(5, len(stmt.lines))


class TestBettermentEmpties(unittest.TestCase):
    def testAccountFilterZerosAll(self):
        """All lines filtered by zeros policy."""
        stmt = BettermentPlugin(None, {}).get_parser(ALL_ZERO_CSV_PATH).parse()
        self.assertIsNone(stmt.start_balance)
        self.assertIsNone(stmt.end_balance)
        self.assertIsNone(stmt.start_date)
        self.assertIsNone(stmt.end_date)
        self.assertEqual(0, len(stmt.lines))

    def testHeaderOnly(self):
        """File only has a header line."""
        stmt = BettermentPlugin(None, {}).get_parser(HEADER_CSV_PATH).parse()
        self.assertIsNone(stmt.start_balance)
        self.assertIsNone(stmt.end_balance)
        self.assertIsNone(stmt.start_date)
        self.assertIsNone(stmt.end_date)
        self.assertEqual(0, len(stmt.lines))

    def testEmpty(self):
        """Empty file."""
        stmt = BettermentPlugin(None, {}).get_parser(EMPTY_CSV_PATH).parse()
        self.assertIsNone(stmt.start_balance)
        self.assertIsNone(stmt.end_balance)
        self.assertIsNone(stmt.start_date)
        self.assertIsNone(stmt.end_date)
        self.assertEqual(0, len(stmt.lines))

    def testEmptyEndingBalance(self):
        """Strip out pending transactions."""
        stmt = BettermentPlugin(None, {}).get_parser(BLANK_BAL_PATH).parse()
        self.assertAlmostEqual(1319.74, stmt.start_balance)
        self.assertAlmostEqual(1692.68, stmt.end_balance)
        self.assertEqual(date(2015, 10, 2), to_date(stmt.start_date))
        self.assertEqual(date(2015, 10, 2), to_date(stmt.end_date))
        self.assertEqual(3, len(stmt.lines))
        for stline in stmt.lines:
            self.assertTrue(stline.memo in ('Dividend Reinvestment', 'Market Change'))
            self.assertFalse(is_zero(stline.amount))
            self.assertEqual(date(2015, 10, 2), to_date(stline.date))


class TestBettermentStatementIdStability(unittest.TestCase):
    all_hash = "316fcd14b9bb7d9bdb6a00473356c896aede98da3df9268bc57c319f209ad3d1"
    amt_hash = "4ebc4a141b378980461430980948a55988fbf56f85d084ac33d8a8f61b9fab88"
    none_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def testAllFilled(self):
        """All of the fields used in the hash have a value"""
        sline = StatementLine()
        sline.date = date(2015, 10, 2)
        sline.memo = "Test statement line"
        sline.amount = 123.45
        self.assertEqual(self.all_hash, generate_stable_transaction_id(sline))

    def testAmount(self):
        """Only amount is set"""
        sline = StatementLine()
        sline.amount = 123.45
        self.assertEqual(self.amt_hash, generate_stable_transaction_id(sline))

    def testNone(self):
        """Nothing is set"""
        sline = StatementLine()
        self.assertEqual(self.none_hash, generate_stable_transaction_id(sline))


def to_date(dt):
    """Creates a comparable date object from the given datetime."""
    return date(dt.year, dt.month, dt.day)
