import os

from crawlmi.utils.settings import read_list_data_file


# General settings

COMMANDS_MODULE = ''

STATS_CLASS = 'crawlmi.stats.MemoryStats'
STATS_DUMP = True

SPIDER_MODULES = []


# Log settings

LOG_ENABLED = True
LOG_ENCODING = 'utf-8'
LOG_FILE = None
LOG_LEVEL = 'DEBUG'
LOG_STDOUT = False


# Downloader settings

DOWNLOAD_HANDLERS = {
    'file': 'crawlmi.core.handlers.FileDownloadHandler',
    'http': 'crawlmi.core.handlers.HttpDownloadHandler',
    'https': 'crawlmi.core.handlers.HttpDownloadHandler',
}

CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8  # use 0 not to limit requests per domain

DOWNLOAD_DELAY = 0
RANDOMIZE_DOWNLOAD_DELAY = True


# Extensions

EXTENSIONS_BASE = {
    'crawlmi.middleware.extensions.log_stats.LogStats': 0,
}
EXTENSIONS = {}

LOG_STATS_INTERVAL = 60.0


# Downloader pipeline

PIPELINE_BASE = {
    'crawlmi.middleware.pipelines.filter.Filter': 50,
    'crawlmi.middleware.pipelines.random_user_agent.RandomUserAgent': 400,
    'crawlmi.middleware.pipelines.default_headers.DefaultHeaders': 550,
    'crawlmi.middleware.pipelines.redirect.Redirect': 600,
    'crawlmi.middleware.pipelines.http_compression.HttpCompression': 800,
    'crawlmi.middleware.pipelines.chunked_transfer.ChunkedTransfer': 830,
    'crawlmi.middleware.pipelines.downloader_stats.DownloaderStats': 850,
}
PIPELINE = {}


DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}

FILTER_NONTEXT_RESPONSE = False  # filter all binary responses (images, pdfs, etc.)
FILTER_BODY_LENGTH_LIMIT = 0  # good size can be 600KB
FILTER_URL_LENGTH_LIMIT = 2083  # uses IE limit
FILTER_NON_200_RESPONSE_STATUS = False  # filter all non-200 responses
FILTER_RESPONSE_STATUS = lambda status_code: False  # if True, filter the response

RANDOM_USER_AGENT_LIST = read_list_data_file(os.path.join(os.path.dirname(__file__), 'user_agents.txt'))

REDIRECT_MAX_TIMES = 20  # uses Firefox default setting
REDIRECT_PRIORITY_ADJUST = +2
