import sys
from dbconnector import grant_connection
from casestructure import Case, Note


def build_cases(query):
    with grant_connection() as dbconnect:
        for row in dbconnect.get_case(query):
            case = Case(*row)
            for note in ['signif_note', 'sig_note_m1', 'sig_note_m2',
                         'sig_note_p1', 'sig_note_p2', 'htreb', 'hmid',
                         'hbass']:
                if case.features[note] is not None:
                    nquery = "SELECT * FROM NOTEBASE WHERE NID = " + \
                             str(case.features[note])
                    case.features[note] = Note(*dbconnect.get_note(nquery)
                                               .fetchone())
            for notes in ['other_notes', 'hother']:
                # TO BE TESTED
                if case.features[notes] is not None:
                    notelist = list(eval(case.features[notes]))
                    newlist = []
                    for n in notelist:
                        query = "SELECT * FROM NOTEBASE WHERE NID = " + str(n)
                        newlist.append(Note(*dbconnect.execute_query(query).
                                            fetchone()))
                    case.features[notes] = newlist
            yield case


def process_input():
    pass


def retrieve_cases(inp_case):
    fav_cases = {}
    query = "SELECT * FROM CASEBASE"
    for case in build_cases(query):
        fav_cases.update({similarity(inp_case, case): case})
    for ele in reversed(sorted(fav_cases.items())):
        print(ele)
        if(ele[0] > 0.8):
            yield ele


def similarity(inp_case, case):
    return case.features['id']
#     s_value = 0.2
#     for note, w in {'sig_note_m1':0.9, 'sig_note_m2':0.5,\
#                       'sig_note_p1':0.9, 'sig_note_p2':0.5}.items():
#         if inp_case.features[note].features['tone'] == case.features[note].
#                                                        features['tone']:
#             s_value = s_value + w * (1-s_value)
#     print(s_value)
#     return s_value


def modify_case():
    pass


def main():
    inp_case = process_input()
    for case in retrieve_cases(inp_case):
        modify_case()
        #print("This one : ", case)

if __name__ == '__main__':
    sys.exit(main())

#all_cases = dict(enumerate(build_cases()))
#for x in all_cases.keys():
#    print('{} :\n{}'.format(x,all_cases[x]))
