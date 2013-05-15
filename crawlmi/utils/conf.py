from operator import itemgetter


def arglist_to_dict(arglist):
    '''Convert a list of arguments like ['arg1=val1', 'arg2=val2', ...] to a
    dict.
    '''
    return dict(x.split('=', 1) for x in arglist)


def build_component_list(base, custom):
    '''Compose a component list based on a custom and base dict of components
    (typically middlewares or extensions), unless custom is already a list, in
    which case it's returned.
    '''
    if isinstance(custom, (list, tuple)):
        return custom
    compdict = base.copy()
    compdict.update(custom)
    return [k for k, v in sorted(compdict.items(), key=itemgetter(1))
            if v is not None]


def read_list_data_file(file_name):
    '''Read the file, line by line, trimming the lines at comments (`#`) and
    skipping the empty lines.
    Return the list of the lines read.
    '''

    result = []
    with open(file_name, 'rb') as f:
        for line in f:
            line = line.partition('#')[0].strip()
            if line:
                result.append(line)
    return result
