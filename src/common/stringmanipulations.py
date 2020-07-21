def onlyAplhaNumeric(s, substitute):
    l = list(s)
    return "".join([elem if elem.isalnum() else substitute for elem in list(s)])
