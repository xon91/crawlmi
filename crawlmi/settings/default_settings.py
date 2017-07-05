from OpenSSL import SSL

# General settings

DATA_DIR = None

COMMAND_MODULES = []
SPIDER_MODULES = []

STATS_CLASS = 'crawlmi.stats.MemoryStats'
STATS_DUMP = True


# Log settings

LOG_ENABLED = True
LOG_ENCODING = 'utf-8'
LOG_FILE = None
LOG_LEVEL = 'DEBUG'
LOG_STDOUT = False


# Downloader settings

DOWNLOAD_HANDLERS = {
    'file': 'crawlmi.core.handlers.FileDownloadHandler',
    'http': 'crawlmi.core.handlers.http_handler.HttpDownloadHandler',
    'https': 'crawlmi.core.handlers.https_handler.HttpsDownloadHandler',
}

DOWNLOAD_HANDLER_SSL_METHODS = [SSL.SSLv3_METHOD, SSL.TLSv1_METHOD]

DOWNLOAD_TIMEOUT = 180  # 3mins
DOWNLOAD_SIZE_LIMIT = 0  # size limit of object to download (600KB is good option)

# sum of sizes of active responses. When exceeded, downloader holds back
RESPONSE_ACTIVE_SIZE_LIMIT = 10000000

CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8  # use 0 not to limit requests per domain

DOWNLOAD_DELAY = 0
RANDOMIZE_DOWNLOAD_DELAY = True


# Extensions

EXTENSIONS_BASE = {
    'crawlmi.middleware.extensions.core_stats.CoreStats': 0,
    'crawlmi.middleware.extensions.log_stats.LogStats': 0,
    'crawlmi.middleware.extensions.save_response.SaveResponse': 0,
}
EXTENSIONS = {}

LOG_STATS_INTERVAL = 60.0

SAVE_RESPONSE_DIR = 'saved'

# Downloader pipeline

PIPELINE_BASE = {
    'crawlmi.middleware.pipelines.duplicate_filter.DuplicateFilter': 25,
    'crawlmi.middleware.pipelines.filter.Filter': 50,
    'crawlmi.middleware.pipelines.random_user_agent.RandomUserAgent': 400,
    'crawlmi.middleware.pipelines.retry.Retry': 500,
    'crawlmi.middleware.pipelines.tor.Tor': 510,
    'crawlmi.middleware.pipelines.canonical.Canonical': 525,
    'crawlmi.middleware.pipelines.default_headers.DefaultHeaders': 550,
    'crawlmi.middleware.pipelines.redirect.MetaRefreshRedirect': 580,
    'crawlmi.middleware.pipelines.http_compression.HttpCompression': 590,
    'crawlmi.middleware.pipelines.redirect.Redirect': 600,
    'crawlmi.middleware.pipelines.cookies.Cookies': 700,
    'crawlmi.middleware.pipelines.chunked_transfer.ChunkedTransfer': 830,
    'crawlmi.middleware.pipelines.downloader_stats.DownloaderStats': 850,
    'crawlmi.middleware.pipelines.http_cache.HttpCache': 900,
}
PIPELINE = {}

CANONICAL_ENABLED = False

COOKIES_ENABLED = False
COOKIES_DEBUG = False

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}

DUPLICATE_FILTER_ENABLED = False

FILTER_NONTEXT_RESPONSE = False  # filter all binary responses (images, pdfs, etc.)
FILTER_SCHEMES = ['mailto', 'ftp']
FILTER_URL_LENGTH_LIMIT = 2083  # uses IE limit
FILTER_NON_200_RESPONSE_STATUS = False  # filter all non-200 responses
FILTER_RESPONSE_STATUS = lambda status_code: False  # if True, filter the response

HTTP_CACHE_ENABLED = False
HTTP_CACHE_DIR = 'httpcache'
HTTP_CACHE_IGNORE_MISSING = False
HTTP_CACHE_STORAGE = 'crawlmi.middleware.pipelines.http_cache.storage.DbmCacheStorage'
HTTP_CACHE_EXPIRATION_SECS = 0
HTTP_CACHE_IGNORE_NON_200_STATUS = True
HTTP_CACHE_IGNORE_STATUS = lambda status_code: False  # if True, don't cache the response
HTTP_CACHE_IGNORE_SCHEMES = ['file']
HTTP_CACHE_DBM_MODULE = 'anydbm'
HTTP_CACHE_POLICY = 'crawlmi.middleware.pipelines.http_cache.policy.DummyPolicy'

RANDOM_USER_AGENT_LIST = []

REDIRECT_MAX_TIMES = 20  # uses Firefox default setting
REDIRECT_PRIORITY_ADJUST = +2
REDIRECT_MAX_METAREFRESH_DELAY = 100

RETRY_TIMES = 2  # initial response + 2 retries = 3 requests
RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 408]
RETRY_PRIORITY_ADJUST = -1  # it is better to wait a little

TOR_ENABLED = False
TOR_HTTP_PROXY = 'http://127.0.0.1:8118/'
# following settings are used to set new tor identity and are not required
TOR_CONNECTION = ('127.0.0.1', 9051)  # connection parameters for tor, not privoxy!
TOR_PASSWORD = None  # use empty string if no password is usedt
