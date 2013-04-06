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
