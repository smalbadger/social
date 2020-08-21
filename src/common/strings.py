import html


def onlyAplhaNumeric(s, substitute):
    return "".join([elem if elem.isalnum() else substitute for elem in list(s)])


def equalTo(s1, s2, normalize_whitespace=True, normalize_html_chars=True):
    if normalize_whitespace:

        s1 = "".join(s1.replace(r"\n"," ").split())
        s2 = "".join(s2.replace(r"\n"," ").split())

    if normalize_html_chars:
        s1 = fromHTML(s1).replace(u'\xa0', u' ')
        s2 = fromHTML(s2).replace(u'\xa0', u' ')

    return s1 == s2

def xpathConcat(s, quotation="'"):
    return f"concat({quotation}" + f"{quotation}, {quotation}".join(list(s)) + f"{quotation})"


def fromHTML(astring):
    return html.unescape(astring)


def toHTML(astring):
    return html.escape(astring)
