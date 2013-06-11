from twisted.trial import unittest

from crawlmi.utils.html import remove_entities


class UtilsHtmlTest(unittest.TestCase):
    def test_remove_entities(self):
        # make sure it always return uncode
        self.assertIsInstance(remove_entities('no entities'), unicode)
        self.assertIsInstance(remove_entities('Price: &pound;100!'), unicode)

        # regular conversions
        self.assertEqual(remove_entities(u'As low as &#163;100!'),
                         u'As low as \xa3100!')
        self.assertEqual(remove_entities('As low as &pound;100!'),
                         u'As low as \xa3100!')
        self.assertEqual(remove_entities('redirectTo=search&searchtext=MR0221Y&aff=buyat&affsrc=d_data&cm_mmc=buyat-_-ELECTRICAL & SEASONAL-_-MR0221Y-_-9-carat gold &frac12;oz solid crucifix pendant'),
                         u'redirectTo=search&searchtext=MR0221Y&aff=buyat&affsrc=d_data&cm_mmc=buyat-_-ELECTRICAL & SEASONAL-_-MR0221Y-_-9-carat gold \xbdoz solid crucifix pendant')
        # keep some entities
        self.assertEqual(remove_entities('<b>Low &lt; High &amp; Medium &pound; six</b>', keep=['lt', 'amp']),
                         u'<b>Low &lt; High &amp; Medium \xa3 six</b>')

        # illegal entities
        self.assertEqual(remove_entities('a &lt; b &illegal; c &#12345678; six', remove_illegal=False),
                         u'a < b &illegal; c &#12345678; six')
        self.assertEqual(remove_entities('a &lt; b &illegal; c &#12345678; six', remove_illegal=True),
                         u'a < b  c  six')
        self.assertEqual(remove_entities('x&#x2264;y'), u'x\u2264y')

        # check browser hack for numeric character references in the 80-9F range
        self.assertEqual(remove_entities('x&#153;y', encoding='cp1252'), u'x\u2122y')

        # encoding
        self.assertEqual(remove_entities('x\x99&#153;&#8482;y', encoding='cp1252'),
                         u'x\u2122\u2122\u2122y')
