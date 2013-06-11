from twisted.trial import unittest

from crawlmi.utils.regex import (html_comment_re, html_script_re, html_noscript_re)


html = '''
<html>
<head>
</head>
<body>
    <!-- This is comment 1 < > -- -->
    < script src="#" type="text/javascript" >hello<worl/d </ ScRiPt>
    <!---->
    < NoScript >Blah </ noscript>
    <!--[if (gte IE 9)|!(IE)]><!-->
</body>
</html>
'''


class ReTest(unittest.TestCase):
    def test_html_comment_re(self):
        self.assertListEqual(html_comment_re.findall(html),
            ['<!-- This is comment 1 < > -- -->',
             '<!---->',
             '<!--[if (gte IE 9)|!(IE)]><!-->'])

    def test_html_script_re(self):
        self.assertListEqual(html_script_re.findall(html),
            ['< script src="#" type="text/javascript" >hello<worl/d </ ScRiPt>'])

    def test_html_noscript_re(self):
        self.assertListEqual(html_noscript_re.findall(html),
            ['< NoScript >Blah </ noscript>'])
