'''This module contains the common regular expressions that one may need when
parsing HTML documents.
'''

import re


html_comment_re = re.compile(r'<!--.*?-->', re.DOTALL)
html_script_re = re.compile(r'<\s*script.*?>.*?</\s*script\s*>',
                            re.DOTALL | re.IGNORECASE)
html_noscript_re = re.compile(r'<\s*noscript.*?>.*?</\s*noscript\s*>',
                              re.DOTALL | re.IGNORECASE)
