import html


def onlyAplhaNumeric(s, substitute):
    return "".join([elem if elem.isalnum() else substitute for elem in list(s)])


def equalTo(s1, s2, normalize_whitespace=True):
    if normalize_whitespace:
        s1 = s1.replace("\s+", " ").strip()
        s2 = s2.replace("\s+", " ").strip()

    return s1 == s2


def fromHTML(astring):
    return html.unescape(astring)


def toHTML(astring):
    return html.escape(astring)
