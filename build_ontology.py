from rdflib import Graph, Literal, URIRef, Namespace

import requests
import lxml.html

prefix = "http://en.wikipedia.org"
visited = set()

OUR_NAMESPACE = Namespace("https://example.org/")
WIKI = Namespace("http://en.wikipedia.org/wiki/")
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def iterate_movies_list(url):
    g = Graph()
    urls = []
    r = requests.get(url)
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

    # urls = ["https://en.wikipedia.org/wiki/Colette_(2020_film)"]
    # visited.add("Colette_(2020_film)")

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
            object_entity = WIKI[t.replace(" ", "_")]

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
        query_results = object_text_to_match[0].xpath(".//a/@href")
        add_relation_based_on_type(subject, relation, urls, g, query_results, True)

    query_results = object_text_to_match[0].xpath(f"./td//text()[. != '\n' and not(./parent::a)]")
    # we do not want to add twice links to the graph

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
            year = item
        else:
            if item.isnumeric():
                day = item
                if len(day) < 2:
                    day = "0" + day
    if month is None or day is None or year is None:
        return None
    return f"{year}-{month}-{day}"


def crawl_film(url, g):
    """
    :param url: url to explore
    :param g: ontology graph
    :return: creates the ontology graph
    """
    urls = []
    r = requests.get(url)
    doc = lxml.html.fromstring(r.content)

    current_entity = URIRef(url)
    prefix_query = "//table[contains(@class, 'infobox')]//tr"

    add_relation(current_entity, "director", urls, doc, g, prefix_query, text_to_match="Directed by", just_text=False)
    add_relation(current_entity, "producer", urls, doc, g, prefix_query, text_to_match="Produced by", just_text=False)
    add_relation(current_entity, "starring", urls, doc, g, prefix_query, text_to_match="Starring", just_text=False)

    # find if the movie is based on a book
    query_results = doc.xpath(f"{prefix_query}[./th[text() = 'Based on']]")
    if len(query_results) > 0:
        g.add((current_entity, OUR_NAMESPACE["based_on"], Literal(True)))

    # get release date
    query_results = doc.xpath(f"{prefix_query}[./th[.//text() = 'Release date']]//li/text()")
    for t in query_results:
        t = parse_date(t)
        if t is not None:
            g.add((current_entity, OUR_NAMESPACE["release_date"], Literal(t)))

    query_results = doc.xpath(f"{prefix_query}[./th[.//text() = 'Running time']]/td/text()")
    for t in query_results:
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
        # we only extract information form the infobox
        return

    # get the birth date
    # format Born:
    query_results = infobox[0].xpath(".//tr[./th[.//text() = 'Born']]/td//text()")
    for t in query_results:
        t = parse_date(t)
        if t is not None:
            g.add((current_entity, OUR_NAMESPACE["born"], Literal(t)))
    # format Date of Birth
    query_results = infobox[0].xpath(".//tr//th[contains(text(), 'Date of birth')]")
    for t in query_results:
        t = t.xpath("./../td//span[@class='bday']//text()")
        if len(t) > 0:
            t = [str(s) for s in t]
            dob = "".join(t)
            g.add((current_entity, OUR_NAMESPACE["born"], Literal(dob)))

    # get the occupation
    query_results = infobox[0].xpath(f".//tr[./th[.//text() = 'Occupation']]/td//text()")
    for t in query_results:
        list_occupations = t.split(",")
        for occ in list_occupations:
            g.add((current_entity, OUR_NAMESPACE["occupation"], Literal(occ.strip().lower())))


url_root = "https://en.wikipedia.org/wiki/List_of_Academy_Award-winning_films"
g = iterate_movies_list(url_root)

