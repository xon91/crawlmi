from time import time  # used in global tests code


def get_engine_status(engine):
    tests = [
        'time()-engine.start_time',
        'engine.running',
        'engine.paused',
        'engine.pending_requests',
        'len(engine.inq)',
        'len(engine.outq)',
        'len(downloader.slots)',
        'downloader.num_in_progress',
    ]

    status = []
    downloader = engine.downloader
    for test in tests:
        try:
            status += [(test, eval(test))]
        except Exception as e:
            status += [(test, '%s (exception)' % type(e).__name__)]

    return status


def format_engine_status(engine):
    status = get_engine_status(engine)
    s = 'Execution engine status\n\n'
    for test, result in status:
        s += '%-47s : %s\n' % (test, result)
    return s


def print_engine_status(engine):
    print format_engine_status(engine)
