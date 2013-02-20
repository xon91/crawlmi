# General settings

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

PIPELINE_BASE = {}
PIPELINE = {}
