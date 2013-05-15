from twisted.trial import unittest

from crawlmi.utils.sitemap import (get_sitemap_type, iter_urls_from_robots,
                                   iter_urls_from_sitemap)


sitemapindex = '''<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   <sitemap>
      <loc>http://www.example.com/sitemap1.xml.gz</loc>
      <lastmod>2004-10-01T18:23:17+00:00</lastmod>
   </sitemap>
   <sitemap>
      <loc>http://www.example.com/sitemap2.xml.gz</loc>
      <lastmod>2005-01-01</lastmod>
   </sitemap>
</sitemapindex>
'''

urlset = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.google.com/schemas/sitemap/0.84">
  <url>
    <loc>http://www.example.com/</loc>
    <lastmod>2009-08-16</lastmod>
    <changefreq>daily</changefreq>
    <priority>1</priority>
  </url>
  <url>
    <loc>http://www.example.com/Special-Offers.html</loc>
    <lastmod>2009-08-16</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
'''


class UtilsSitemapTest(unittest.TestCase):
    def test_iter_urls_from_sitemap(self):
        self.assertListEqual(list(iter_urls_from_sitemap(sitemapindex)),
            ['http://www.example.com/sitemap1.xml.gz', 'http://www.example.com/sitemap2.xml.gz'])
        self.assertListEqual(list(iter_urls_from_sitemap(urlset)),
            ['http://www.example.com/', 'http://www.example.com/Special-Offers.html'])

    def test_get_sitemap_type(self):
        self.assertEqual(get_sitemap_type(sitemapindex), 'sitemapindex')
        self.assertEqual(get_sitemap_type(urlset), 'urlset')

    def test_iter_urls_from_robots(self):
        robots = '''User-agent: *
                    Disallow: /aff/
                    Disallow: /wl/

                    # Search and shopping refining
                    Disallow: /s*/*facet
                    Disallow: /s*/*tags

                    # Sitemap files
                    Sitemap: http://example.com/sitemap.xml
                    Sitemap: http://example.com/sitemap-product-index.xml

                    # Forums
                    Disallow: /forum/search/
                    Disallow: /forum/active/
                    '''
        self.assertListEqual(list(iter_urls_from_robots(robots)),
            ['http://example.com/sitemap.xml', 'http://example.com/sitemap-product-index.xml'])
