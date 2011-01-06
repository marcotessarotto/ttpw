#!/bin/env python
# -*- coding: utf-8 -*-
"""TreeTagger Python wrapper test module.
"""

import unittest
from test import test_support



StartProcess


class TTStartTestCase(unittest.TestCase):

    # Only use setUp() and tearDown() if necessary

    def setUp(self):
        ... code to execute in preparation for tests ...

    def tearDown(self):
        ... code to execute to clean up after tests ...

    def test_feature_one(self):
        # Test feature one.
        ... testing code ...

    def test_feature_two(self):
        # Test feature two.
        ... testing code ...

    ... more test methods ...



def test_main():
    test_support.run_unittest(TTStartTestCase,
                             )

if __name__ == '__main__':
    test_main()
