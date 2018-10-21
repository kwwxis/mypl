def xstr(x):
    if type(x) is bool:
        if x == True:
            return "true"
        else:
            return "false"
    if x == None:
        return '<UNDEFINED>'
    return str(x)