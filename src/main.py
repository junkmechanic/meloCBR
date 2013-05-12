import sys
from dbconnector import grant_connection
from casestructure import Case, Note
from casemaker import get_case
from operator import itemgetter


def build_cases(query):
    with grant_connection() as dbconnect:
        for row in dbconnect.get_case(query):
            case = Case(*row)
            for note in ['signif_note', 'sig_note_m1', 'sig_note_m2',
                         'sig_note_p1', 'sig_note_p2', 'htreb', 'hmid',
                         'hbass']:
                if case[note] is not None:
                    nquery = "SELECT * FROM NOTEBASE WHERE NID = " + \
                             str(case[note])
                    case[note] = Note(*dbconnect.get_note(nquery).fetchone())
            for notes in ['other_notes', 'hother']:
                if case[notes] != 'None':
                    notelist = eval(case[notes])
                    newlist = []
                    for n in notelist:
                        query = "SELECT * FROM NOTEBASE WHERE NID = " + str(n)
                        newlist.append(Note(*dbconnect.get_note(query).
                                            fetchone()))
                    case[notes] = newlist
            yield case


def retrieve_cases(inp_case):
    fav_cases = {}
    query = """SELECT * FROM CASEBASE INNER JOIN NOTEBASE
            ON CASEBASE.SgnfcntNote = NOTEBASE.NID
            AND NOTEBASE.Tone = """ + str(inp_case['signif_note']['tone'])
    for case in build_cases(query):
        fav_cases.update({case: similarity(inp_case, case)})
    for ele in sorted(fav_cases.items(), key=itemgetter(1), reverse=True):
        if(ele[0] > 0.8):
            print(ele)
            yield ele


def similarity(inp_case, case):
    s_value = 0.5
    for note, w in {'sig_note_m1': 0.6, 'sig_note_m2': 0.3,
                    'sig_note_p1': 0.6, 'sig_note_p2': 0.3}.items():
        if (inp_case[note] is not None) and (case[note] is not None):
            if inp_case[note]['tone'] == case[note]['tone']:
                s_value = s_value + w * (1 - s_value)
    return s_value


def adapt_case(inp_case, case_list):
    if case_list:
        best_case, similarity = case_list[0]
        if similarity > 0.9:
            for key in ['htreb', 'hmid', 'hbass', 'hother']:
                inp_case[key] = best_case[key]
    print(inp_case)


def process_input():
    inp_cases = [case for case in get_case('input1')]
    for case in inp_cases:
        yield case


def main():
    for inp_case in process_input():
        #print(inp_case)
        cases = [case for case in retrieve_cases(inp_case)]
        adapt_case(inp_case, cases)

if __name__ == '__main__':
    sys.exit(main())
