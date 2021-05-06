from rdflib import Namespace

OUR_NAMESPACE = Namespace("https://example.org/")
WIKI = Namespace("http://en.wikipedia.org/wiki/")


def get_entity_name_and_relation(relation_type, words_lst, index_start, index_end):
    entity_name = "_".join(words_lst[index_start:index_end])
    relation = OUR_NAMESPACE[relation_type]
    return relation, WIKI[entity_name]


def parse_query(input_string):
    """
    :param input_string: a query to be executed.
    :return: parses the query and returns a tuple of the specified format:
            query#1:  (1, director_relation, film_name)
            query#2:  (2, producer_relation, film_name)
            query#3:  (3, based_on_relation, film_name)
            query#4:  (4, release_date_relation, film_name)
            query#5:  (5, running_time_relation, film_name)
            query#6:  (6, starring_relation, film_name)
            query#7:  (7, starring_relation, film_name, person_name)
            query#8:  (8, born_relation, person_name)
            query#9:  (9, occupation_relation, person_name)
            query#10: (10, based_on_relation)
            query#11: (11, starring_relation, person_name)
            query#12  (12, occupation_relation, occupation1, occupation2)
            query#13  (13, starring_relation, person1, person2)
    """

    # remove question mark:
    input_string = input_string[:-1]
    words_lst = input_string.split()

    if words_lst[0] == "Who":
        # queries 1 or 2 or 6
        if words_lst[1] == "directed":
            # query 1
            return 1, *get_entity_name_and_relation("director", words_lst, 2, len(words_lst))
        elif words_lst[1] == "produced":
            # query 2
            return 2, *get_entity_name_and_relation("producer", words_lst, 2, len(words_lst))
        elif words_lst[1] == "starred" and words_lst[2] == "in":
            # query 6
            return 6, *get_entity_name_and_relation("starring", words_lst, 3, len(words_lst))
    elif words_lst[0] == "Is":
        # query 3
        return 3, *get_entity_name_and_relation("based_on", words_lst, 1, len(words_lst) - 4)
    elif words_lst[0] == "When":
        if words_lst[-1] == "released":
            # query 4
            return 4, *get_entity_name_and_relation("release_date", words_lst, 2, len(words_lst) - 1)
        elif words_lst[-1] == "born":
            # query 8
            return 8, *get_entity_name_and_relation("born", words_lst, 2, len(words_lst) - 1)
    elif words_lst[0] == "How":
        if words_lst[1] == "long":
            # query 5
            return 5, *get_entity_name_and_relation("running_time", words_lst, 3, len(words_lst))
        elif words_lst[1] == "many":
            # queries 10, 11 or 12
            if words_lst[2] == "films" and words_lst[-1] == "books":
                # query 10
                return 10, OUR_NAMESPACE["based_on"]
            elif words_lst[2] == "films" and words_lst[3] == "starring":
                # query 11
                index_of_won = words_lst.index("won")
                return 11, *get_entity_name_and_relation("starring", words_lst, 4, index_of_won)
            elif "are" in words_lst and "also" in words_lst:
                # query 12
                index_of_are = words_lst.index("are")
                occupation1 = " ".join(words_lst[2:index_of_are]).lower()
                occupation2 = " ".join(words_lst[index_of_are + 2:]).lower()
                relation = OUR_NAMESPACE["occupation"]
                return 12, relation, occupation1, occupation2
    elif words_lst[0] == "Did":
        # query 7
        index_of_star = words_lst.index("star")  # must be the verb of the query
        person_name = "_".join(words_lst[1:index_of_star])
        film_name = "_".join(words_lst[index_of_star + 2:])
        relation = OUR_NAMESPACE["starring"]
        return 7, relation, WIKI[film_name], WIKI[person_name]
    elif words_lst[0] == "What":
        # query 9
        return 9, *get_entity_name_and_relation("occupation", words_lst, 5, len(words_lst))
    elif words_lst[0] == "Have":
        # query 13
        index_of_and = words_lst.index("and")
        index_of_ever = words_lst.index("ever")
        person1_name = "_".join(words_lst[1:index_of_and])
        person2_name = "_".join(words_lst[index_of_and + 1:index_of_ever])
        relation = OUR_NAMESPACE["starring"]
        return 13, relation, WIKI[person1_name], WIKI[person2_name]
