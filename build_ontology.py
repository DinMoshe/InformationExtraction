from rdflib import Graph, Literal, RDF, URIRef, Namespace, BNode
# rdflib knows about some namespaces, like FOAF
from rdflib.namespace import FOAF, XSD

import requests
import lxml.html
import datetime

prefix = "http://en.wikipedia.org"
visited = set()

DBPEDIA = Namespace("https://dbpedia.org/ontology/")
WIKI = Namespace("http://en.wikipedia.org/wiki/")


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

    # urls = ["https://en.wikipedia.org/wiki/Fifty_Shades_of_Grey_(film)"] + urls

    for next_url in urls:
        crawl_film(next_url, g)
        i += 1
        if i > 1:
            break

    print(g.serialize(format='nt').decode("utf-8"))


def add_relation_based_on_type(subject, relation, urls, g, query_results, is_link):
    for t in query_results:
        if is_link:
            object_entity = URIRef(prefix + t)
        else:
            object_entity = WIKI[t.replace(" ", "_")]

        g.add((subject, DBPEDIA[relation], object_entity))

        if is_link and t in visited:
            continue

        # print(f"---- {t}")
        if is_link:
            urls.append(f"{prefix}{t}")
            visited.add(t)


def add_relation(subject, relation, urls, doc, g, prefix_query, text_to_match, just_text):
    if not just_text:
        query_results = doc.xpath(f"{prefix_query}[./th[.//text() = '{text_to_match}']]//a/@href")
        add_relation_based_on_type(subject, relation, urls, g, query_results, True)

    query_results = doc.xpath(f"{prefix_query}[./th[.//text() = '{text_to_match}']]//li/text()")
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

    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    month = None
    day = None
    year = None
    for item in date_list:
        if item in months:
            month = str(months.index(item) + 1)
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
        g.add((current_entity, DBPEDIA["based_on"], Literal(True)))

    # get release date
    query_results = doc.xpath(f"{prefix_query}[./th[.//text() = 'Release date']]//li/text()")
    for t in query_results:
        t = parse_date(t)
        if t is not None:
            g.add((current_entity, DBPEDIA["release_date"], Literal(t)))

    query_results = doc.xpath(f"{prefix_query}[./th[.//text() = 'Running time']]/td/text()")
    for t in query_results:
        g.add((current_entity, DBPEDIA["running_time"], Literal(t)))

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
    prefix_query = "//table[contains(@class, 'infobox')]//tr"

    # get the birth date
    query_results = doc.xpath(f"{prefix_query}[./th[.//text() = 'Born']]/td//text()")
    for t in query_results:
        t = parse_date(t)
        if t is not None:
            g.add((current_entity, DBPEDIA["born"], Literal(t)))

    # get the occupation
    query_results = doc.xpath(f"{prefix_query}[./th[.//text() = 'Occupation']]/td//text()")
    for t in query_results:
        list_occupations = t.split(",")
        for occ in list_occupations:
            g.add((current_entity, DBPEDIA["occupation"], Literal(occ.strip().lower())))


def create_ontology():
    # create a Graph
    g = Graph()

    # Create an RDF URI node to use as the subject for multiple triples
    donna = URIRef("http://example.org/donna")

    # Add triples using store's add() method.
    g.add((donna, RDF.type, FOAF.Person))
    g.add((donna, FOAF.nick, Literal("donna", lang="ed")))
    g.add((donna, FOAF.name, Literal("Donna Fales")))
    g.add((donna, FOAF.mbox, URIRef("mailto:donna@example.org")))

    # Add another person
    ed = URIRef("http://example.org/edward")

    # Add triples using store's add() method.
    g.add((ed, RDF.type, FOAF.Person))
    g.add((ed, FOAF.nick, Literal("ed", datatype=XSD.string)))
    g.add((ed, FOAF.name, Literal("Edward Scissorhands")))
    g.add((ed, FOAF.mbox, URIRef("mailto:e.scissorhands@example.org")))

    # Iterate over triples in store and print them out.
    print("--- printing raw triples ---")
    for s, p, o in g:
        print((s, p, o))

    # For each foaf:Person in the store, print out their mbox property's value.
    print("--- printing mboxes ---")
    for person in g.subjects(RDF.type, FOAF.Person):
        for mbox in g.objects(person, FOAF.mbox):
            print(mbox)

    # Bind the FOAF namespace to a prefix for more readable output
    g.bind("foaf", FOAF)

    # print all the data in the Notation3 format
    print("--- printing mboxes ---")
    print(g.serialize(format='n3').decode("utf-8"))


url_root = "https://en.wikipedia.org/wiki/List_of_Academy_Award-winning_films"
iterate_movies_list(url_root)

