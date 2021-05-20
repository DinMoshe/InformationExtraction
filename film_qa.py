from parse_query import parse_query
import rdflib
import sys
from build_ontology import build_ontology


def parse_cmd_line():
    if len(sys.argv) < 2:
        print("Not enough arguments")
        return

    action = sys.argv[1]
    if action == "create":
        build_ontology()
    elif action == "question":
        if len(sys.argv) < 3:
            print("Not enough arguments")
            return
        question = sys.argv[2]
        execute_query(question)
    else:
        print("Illegal action")


def get_name_from_URI(lst):
    start = len("http://en.wikipedia.org/wiki/")
    lst = [str(uri[0])[start:].replace("_", " ") for uri in lst]
    return lst


def answer_yes_or_no(results):
    if len(results) > 0:
        return "Yes"
    else:
        return "No"


def execute_query(input_string):
    answer = None
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
        results = list(results)
        if query_tuple[0] == 3:
            answer = answer_yes_or_no(results)
        elif 4 <= query_tuple[0] <= 5 or 8 <= query_tuple[0] <= 9:
            results = [str(item[0]) for item in results]
            answer = ", ".join(results)
        else:
            results = get_name_from_URI(results)
            answer = ", ".join(results)

    if query_tuple[0] == 7:
        query_string = f"ASK WHERE " + "{" \
                                       f" <{query_tuple[2]}> <{query_tuple[1]}> <{query_tuple[3]}> ." + "}"

        results = g.query(query_string)
        results = [True] if results.askAnswer else []
        answer = answer_yes_or_no(results)

    if 10 <= query_tuple[0] <= 11:
        additional_string = "?is_based" if query_tuple[0] == 10 else f"<{query_tuple[2]}>"
        query_string = "SELECT (COUNT(DISTINCT ?film) AS ?count) WHERE {" \
                       f" ?film <{query_tuple[1]}> {additional_string} ." \
                       "}"
        results = g.query(query_string)
        results = list(results)
        answer = str(results[0][0])

    if query_tuple[0] == 12:
        query_string = "SELECT (COUNT(DISTINCT ?person) AS ?count) WHERE {" \
                       f" ?person <{query_tuple[1]}> ?occupation1 ." \
                       f" ?person <{query_tuple[1]}> ?occupation2 ." \
                       "}"
        results = g.query(query_string, initBindings={'occupation1': rdflib.Literal(query_tuple[2]),
                                                      'occupation2': rdflib.Literal(query_tuple[3])})
        results = list(results)
        answer = str(results[0][0])

    if query_tuple[0] == 13:
        query_string = "SELECT ?film WHERE {" \
                       f" ?film <{query_tuple[1]}> ?person1 ." \
                       f" ?film <{query_tuple[1]}> ?person2 ." \
                       "}"
        results = g.query(query_string, initBindings={'person1': query_tuple[2],
                                                      'person2': query_tuple[3]})
        results = list(results)
        answer = answer_yes_or_no(results)

    print(answer)
    return answer


if __name__ == "__main__":
    # execute_query("Is A Star Is Born (2018 film) based on a book?")
    # execute_query("What is the occupation of Steven Yeun?")
    # execute_query("When was Lady Gaga born?")
    # execute_query("Did Lady Gaga star in A Star Is Born (2018 film)?")
    # execute_query("How many films are based on books?")
    # execute_query("How many films starring Meryl Streep won an academy award?")
    # execute_query("How many actress are also model?")
    # execute_query("Have Lady Gaga and Bradley Cooper ever starred in a film together?")

    # g = rdflib.Graph()
    # g.parse("ontology.nt", format="nt")
    # query_string = "SELECT DISTINCT ?film WHERE {" \
    #                f" ?film <https://example.org/based_on> ?yes ." \
    #                "}"
    # results = g.query(query_string)
    # results = list(results)
    # results = get_name_from_URI(results)
    # print(", ".join(results))

    parse_cmd_line()
