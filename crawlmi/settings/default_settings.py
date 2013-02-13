# Downloader settings

DOWNLOAD_HANDLERS_BASE = {
    'file': 'crawlmi.core.handlers.FileDownloadHandler',
    'http': 'crawlmi.core.handlers.HttpDownloadHandler',
    'https': 'crawlmi.core.handlers.HttpDownloadHandler',
}

CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8  # use 0 not to limit requests per domain

DOWNLOAD_DELAY = 0
RANDOMIZE_DOWNLOAD_DELAY = True
