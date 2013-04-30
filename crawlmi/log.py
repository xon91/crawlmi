import sys
import logging
import warnings

from twisted.python import log

from crawlmi.utils.python import to_str


# Logging levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
SILENT = CRITICAL + 1

level_names = {
    DEBUG: 'DEBUG',
    INFO: 'INFO',
    WARNING: 'WARNING',
    ERROR: 'ERROR',
    CRITICAL: 'CRITICAL',
    SILENT: 'SILENT',
}


class CrawlmiFileLogObserver(log.FileLogObserver):
    def __init__(self, f, level=INFO, encoding='utf-8'):
        self.level = level
        self.encoding = encoding
        self.emit = self._emit
        log.FileLogObserver.__init__(self, f)

    def _emit(self, eventDict):
        ev = _adapt_eventdict(eventDict, self.level, self.encoding)
        if ev is not None:
            log.FileLogObserver.emit(self, ev)
        return ev


def _adapt_eventdict(eventDict, log_level=INFO, encoding='utf-8', prepend_level=True):
    '''Adapt Twisted log eventDict making it suitable for logging with a Crawlmi
    log observer. It may return None to indicate that the event should be
    ignored by a Crawlmi log observer.

    `log_level` is the minimum level being logged, and `encoding` is the log
    encoding.
    '''
    ev = eventDict.copy()
    if ev['isError']:
        ev.setdefault('logLevel', ERROR)

    # ignore non-error messages from outside crawlmi
    if ev.get('system') != 'crawlmi' and not ev['isError']:
        return

    level = ev.get('logLevel')
    if level < log_level:
        return

    lvlname = level_names.get(level, 'NOLEVEL')
    message = ev.get('message')
    if message:
        message = [to_str(x, encoding) for x in message]
        if prepend_level:
            message[0] = '%s: %s' % (lvlname, message[0])
        ev['message'] = message

    why = ev.get('why')
    if why:
        why = to_str(why, encoding)
        if prepend_level:
            why = '%s: %s' % (lvlname, why)
        ev['why'] = why

    fmt = ev.get('format')
    if fmt:
        fmt = to_str(fmt, encoding)
        if prepend_level:
            fmt = '%s: %s' % (lvlname, fmt)
        ev['format'] = fmt

    return ev


def _get_log_level(level_name_or_id):
    if isinstance(level_name_or_id, int):
        return level_name_or_id
    elif isinstance(level_name_or_id, basestring):
        return globals()[level_name_or_id]
    else:
        raise ValueError("Unknown log level: %r" % level_name_or_id)


def start(logfile=None, loglevel='INFO', logstdout=True, encoding='utf-8'):
    loglevel = _get_log_level(loglevel)
    file = open(logfile, 'ab') if logfile else sys.stderr
    observer = CrawlmiFileLogObserver(file, loglevel, encoding)
    _oldshowwarning = warnings.showwarning
    log.startLoggingWithObserver(observer.emit, setStdout=logstdout)
    # restore warnings, wrongly silenced by Twisted
    warnings.showwarning = _oldshowwarning
    return observer


def msg(message=None, level=INFO, **kw):
    kw['logLevel'] = level
    kw.setdefault('system', 'crawlmi')
    if message is None:
        log.msg(**kw)
    else:
        log.msg(message, **kw)


def err(stuff=None, why=None, level=ERROR, **kw):
    kw['logLevel'] = level
    kw.setdefault('system', 'crawlmi')
    log.err(stuff, why, **kw)
