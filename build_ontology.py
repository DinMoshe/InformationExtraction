from rdflib import Graph, Literal, URIRef, Namespace

import requests
import lxml.html
import time

prefix = "http://en.wikipedia.org"
visited = set()

OUR_NAMESPACE = Namespace("https://example.org/")
WIKI = Namespace("http://en.wikipedia.org/wiki/")
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def get_page(url):
    page = ''
    while page == '':
        try:
            page = requests.get(url)
            break

        except requests.exceptions.ConnectionError:
            time.sleep(5)
            continue
    return page


def iterate_movies_list(url):
    g = Graph()
    urls = []
    r = get_page(url)
    doc = lxml.html.fromstring(r.content)
    for t in doc.xpath("""//table[contains(@class, 'wikitable sortable')]
                        //tr[td[2]//a/text()[number(.) >= 2010]]/td[1]//a[@href]/@href"""):
        # get all the links of movies which are a column of a row which its second child of type td contains
        # an element <a> whose text is the year and it is 2010 or above
        if t in visited:
            continue

        urls.append(f"{prefix}{t}")
        visited.add(t)

    i = 0

    # urls = ["http://en.wikipedia.org/wiki/Nomadland_(film)"]
    # visited.add("Nomadland_(film)")

    for next_url in urls:
        crawl_film(next_url, g)
        # i += 1
        # if i > 1:
        #     break

    g.serialize("ontology.nt", format='nt')
    # print(g.serialize(format="nt").decode("utf-8"))
    return g


def add_relation_based_on_type(subject, relation, urls, g, query_results, is_link):
    for t in query_results:
        if is_link:
            object_entity = URIRef(prefix + t)
        else:
            t = t.split()
            t = "_".join(t)
            if "Executive_Producer" in t:
                return
            object_entity = WIKI[t]

        g.add((subject, OUR_NAMESPACE[relation], object_entity))

        # print(f"---- {t}")
        if is_link and t not in visited:
            urls.append(f"{prefix}{t}")
            visited.add(t)


def add_relation(subject, relation, urls, doc, g, prefix_query, text_to_match, just_text):
    object_text_to_match = doc.xpath(f"{prefix_query}[./th[.//text() = '{text_to_match}']]")
    if len(object_text_to_match) == 0:
        return

    if not just_text:
        query_results = object_text_to_match[0].xpath(f".//a/@href[. != '/wiki/Producers_Mark']")
        # removed this link because of the Birdman film
        add_relation_based_on_type(subject, relation, urls, g, query_results, True)

    query_results = object_text_to_match[0].xpath(f"./td//text()[. != '\n' and . != ')' and . != '(p.g.a)' "
                                                  f"and not(./parent::a)]")
    # we do not want to add twice links to the graph
    # (g.p.a) is in Birdman film

    add_relation_based_on_type(subject, relation, urls, g, query_results, False)


def extract_name_from_url(url):
    index = len(prefix + "/wiki/")
    name = url[index:].replace("_", " ")
    return name


def parse_date(date):
    if "(" in date:
        index_paren = date.index("(")
    else:
        index_paren = len(date)
    date = date[:index_paren]

    if ")" in date:
        index_paren = date.index(")")
    else:
        index_paren = len(date)
    date = date[:index_paren]
    date = date.replace(",", "")
    date = date.replace("-", " ")  # to handle range of years
    date = date.replace("/", " ")  # to handle range of years
    date = date.replace("\\", " ")  # to handle range of years
    date_list = date.split()

    if len(date_list) == 0:
        # if we just got parentheses
        return None

    month = None
    day = None
    year = None
    for item in date_list:
        if item in MONTHS:
            month = str(MONTHS.index(item) + 1)
            if len(month) < 2:
                month = "0" + month
        elif item.isnumeric() and int(item) > 31:  # it is a year
            if year is None or int(year) > int(item):  # we want to take the minimal year
                year = item
        else:
            if item.isnumeric():
                day = item
                if len(day) < 2:
                    day = "0" + day
    if year is not None:
        if month is not None and day is not None:
            return f"{year}-{month}-{day}"
        else:
            return year
    else:
        return None


def crawl_film(url, g):
    """
    :param url: url to explore
    :param g: ontology graph
    :return: creates the ontology graph
    """
    urls = []
    r = get_page(url)
    doc = lxml.html.fromstring(r.content)

    current_entity = URIRef(url)
    prefix_query = "//table[contains(@class, 'infobox')]//tr"

    add_relation(current_entity, "director", urls, doc, g, prefix_query, text_to_match="Directed by", just_text=False)
    add_relation(current_entity, "producer", urls, doc, g, prefix_query, text_to_match="Produced by", just_text=False)
    add_relation(current_entity, "starring", urls, doc, g, prefix_query, text_to_match="Starring", just_text=False)

    # find if the movie is based on a book
    query_results = doc.xpath(f"{prefix_query}[./th[contains(text(), 'Based on')]]")
    if len(query_results) > 0:
        g.add((current_entity, OUR_NAMESPACE["based_on"], Literal(True)))

    # get release date
    # //li/text()

    query_results = doc.xpath(f"{prefix_query}[./th[contains(.//text(), 'Release date')]]")
    if len(query_results) > 0:
        t = query_results[0].xpath("./td//span[contains(@class, 'bday')]//text()")
        if len(t) > 0:
            g.add((current_entity, OUR_NAMESPACE["release_date"], Literal(t[0])))
        else:
            text_results = query_results[0].xpath("./td//text()[. != '\n']")
            for t in text_results:
                t = parse_date(t)
                if t is not None:
                    g.add((current_entity, OUR_NAMESPACE["release_date"], Literal(t)))

    query_results = doc.xpath(
        f"{prefix_query}[./th[contains(.//text(), 'Running time')]]/td/"
        f"/text()[not(ancestor::sup) and not(ancestor::style)]")
    # maybe add  and @class != 'reference'
    for t in query_results:
        t = t.split()
        if len(t) == 0:  # if t was only whitespaces
            continue
        t = " ".join(t)
        g.add((current_entity, OUR_NAMESPACE["running_time"], Literal(t)))

    for next_url in urls:
        crawl_person(next_url, g)


def crawl_person(url, g):
    """
    :param url: url to explore
    :param g: ontology graph
    :return: creates the ontology graph
    """
    r = requests.get(url)
    doc = lxml.html.fromstring(r.content)

    current_entity = URIRef(url)
    prefix_query = ".//table[contains(@class, 'infobox')]"
    infobox = doc.xpath(prefix_query)

    if len(infobox) == 0:
        # we only extract information from the infobox
        return

    # get the birth date
    # format Date of Birth
    query_results = infobox[0].xpath(".//tr/th[contains(text(), 'Date of birth') or contains(text(), 'Born')]")
    if len(query_results) > 0:
        t = query_results[0].xpath("./../td//span[contains(@class, 'bday')]//text()")
        # //*[not(self::text() and @class != 'reference']
        if len(t) > 0:
            g.add((current_entity, OUR_NAMESPACE["born"], Literal(t[0])))
        else:  # there is no bday, extract plain text
            query_results = query_results[0].xpath("./../td//text()")
            for t in query_results:
                t = parse_date(t)
                if t is not None:
                    g.add((current_entity, OUR_NAMESPACE["born"], Literal(t)))

    # get the occupation
    query_results = infobox[0].xpath(f".//tr[./th[contains(.//text(), 'Occupation')]]/td"
                                     f"//text()[. != '\n' and not(ancestor::sup) and not(ancestor::style)]")
    for t in query_results:
        list_occupations = t.split()
        t = " ".join(list_occupations)
        list_occupations = t.split(",")
        for occ in list_occupations:
            # remove redundant whitespaces
            words = occ.strip().split()
            occ = " ".join(words)
            if len(occ) != 0:
                g.add((current_entity, OUR_NAMESPACE["occupation"], Literal(occ.lower())))


def build_ontology():
    url_root = "https://en.wikipedia.org/wiki/List_of_Academy_Award-winning_films"
    iterate_movies_list(url_root)


build_ontology()



