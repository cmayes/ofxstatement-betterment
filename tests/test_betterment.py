# coding=utf-8

"""
Tests for the ofxstatement Betterment plugin.
"""
from datetime import date
import logging
import unittest

import os

from ofxstatement.plugins.betterment import BettermentPlugin, is_zero

__author__ = 'cmayes'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_betterment')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
ZERO_BAL_CSV_PATH = os.path.join(DATA_DIR, 'transactions.csv')
POS_CSV_PATH = os.path.join(DATA_DIR, 'transactions_positive.csv')
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


def to_date(dt):
    """Creates a comparable date object from the given datetime."""
    return date(dt.year, dt.month, dt.day)
