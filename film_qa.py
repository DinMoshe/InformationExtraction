from parse_query import parse_query
import rdflib


def parse_cmd_line():
    pass


def get_name_from_URI(lst, g):
    lst = [g.compute_qname(uri[0])[-1].replace("_", " ") for uri in lst]
    return lst


def print_yes_or_no(results):
    if len(results) > 0:
        print("Yes")
    else:
        print("No")


def execute_query(input_string):
    g = rdflib.Graph()
    g.parse("ontology.nt", format="nt")
    query_tuple = parse_query(input_string)

    if 1 <= query_tuple[0] <= 6 or 8 <= query_tuple[0] <= 9:
        query_string = f"SELECT ?y WHERE " \
                       "{" \
                       f" <{query_tuple[2]}> <{query_tuple[1]}> ?y . " \
                       "}" \
                       "ORDER BY ?y"
        results = g.query(query_string)
        if query_tuple[0] == 3:
            print_yes_or_no(results)
        elif 8 <= query_tuple[0] <= 9:
            results = [str(item[0]) for item in list(results)]
            print(", ".join(results))
        else:
            results = get_name_from_URI(list(results), g)
            print(", ".join(results))

    if query_tuple[0] == 7:
        query_string = "SELECT ?film WHERE {" \
                       f" ?film <{query_tuple[1]}> <{query_tuple[3]}> ." \
                       f" ?film a <{query_tuple[2]}> . " + "}"
        # f""" FILTER ( regex(str(?film), "{str(query_tuple[2])}" ) """ + "}"

        results = g.query(query_string)
        print(results)
        print(list(results))
        print_yes_or_no(results)


# execute_query("Is A Star Is Born (2018 film) based on a book?")
# execute_query("What is the occupation of Lady Gaga?")
# execute_query("When was Lady Gaga born?")
execute_query("Did Lady Gaga star in Is A Star Is Born (2018 film)?")
