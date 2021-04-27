from parse_query import parse_query
import rdflib


def parse_cmd_line():
    pass


def get_name_from_URI(lst, g):
    lst = [g.compute_qname(uri[0])[-1].replace("_", " ") for uri in lst]
    return lst


def execute_query(input_string):
    g = rdflib.Graph()
    g.parse("ontology.nt", format="nt")
    query_tuple = parse_query(input_string)

    if 1 <= query_tuple[0] <= 6:
        query_string = f"SELECT ?y WHERE " \
                       "{" \
                       f" <{query_tuple[2]}> <{query_tuple[1]}> ?y . " \
                        "}" \
                        "ORDER BY ?y"
        results = g.query(query_string)
        results = get_name_from_URI(list(results), g)
        print(", ".join(results))


# print("loading the graph")
# g = rdflib.Graph()
# g.parse("ontology.nt", format="nt")
# j = WIKI["Joaquin_Phoenix"]
# print(g.qname(j))

execute_query("Who produced Colette (2020 film)?")
