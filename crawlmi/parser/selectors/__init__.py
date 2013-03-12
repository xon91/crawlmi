__all__ = ['XPathSelector', 'XmlXPathSelector', 'HtmlXPathSelector']


try:
    import lxml
    from .lxml_selector import XPathSelector, XmlXPathSelector, HtmlXPathSelector
except ImportError:
    pass
