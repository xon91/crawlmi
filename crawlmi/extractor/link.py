class Link(object):
    __slots__ = ['url', 'text']

    def __init__(self, url, text=''):
        self.url = url
        self.text = text

    def __eq__(self, other):
        return self.url == other.url and self.text == other.text

    def __hash__(self):
        return hash(self.url) ^ hash(self.text)

    def __repr__(self):
        return 'Link(url=%r, text=%r)' % (self.url, self.text)
