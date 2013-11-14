import sys
from dbconnector import grant_connection
from casestructure import Case, Note
from casemaker import get_case
from operator import itemgetter
from pprint import pprint
from itertools import combinations
from random import randint
from output import LilyFile


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
        if(ele[1] > 0.2):
            #print("For case ID : " + str(inp_case['id']) + " --> "
                  #+ str(ele[0]['id']))
            yield ele


def similarity(inp_case, case):
    #s_value = 0.3
    s = 0
    W = 0
    for note, w in {'sig_note_m1': 0.7, 'sig_note_m2': 0.3,
                    'sig_note_p1': 0.5, 'sig_note_p2': 0.2}.items():
        W += w
        if (inp_case[note] is not None) and (case[note] is not None):
            if inp_case[note]['tone'] == case[note]['tone']:
                #s_value = s_value + w * (1 - s_value)
                s += w
    s_value = s / W
    return s_value


def change_chord(case):

    def major(n):
        return [(n + 4) % 12 if (n + 4) % 12 != 0 else 12,
                (n + 7) % 12 if (n + 7) % 12 != 0 else 12, n]

    def minor(n):
        return [(n + 3) % 12 if (n + 3) % 12 != 0 else 12,
                (n + 7) % 12 if (n + 7) % 12 != 0 else 12, n]

    def diminished(n):
        return [(n + 3) % 12 if (n + 3) % 12 != 0 else 12,
                (n + 6) % 12 if (n + 6) % 12 != 0 else 12, n]

    try:
        otrb, omid, obas = [case[note]['tone'] for note in ['htreb', 'hmid',
                                                            'hbass']]
    except TypeError:
        print("Note wasnt assigned harmony and will be suggested one")
        otrb, omid, obas = ' ', ' ', ' '
    if(case['signif_note']['tone'] in [1, 6, 8]):
        case['htreb']['tone'], case['hmid']['tone'],\
            case['hbass']['tone'] = major(case['signif_note']['tone'])
    elif(case['signif_note']['tone'] in [3, 5, 10]):
        case['htreb']['tone'], case['hmid']['tone'],\
            case['hbass']['tone'] = minor(case['signif_note']['tone'])
    elif(case['signif_note']['tone'] in [12]):
        case['htreb']['tone'], case['hmid']['tone'],\
            case['hbass']['tone'] = diminished(case['signif_note']['tone'])
    print("Note : {0} From {1} to {2}".format(case['signif_note']['tone'],
          (otrb, omid, obas), (case['htreb']['tone'], case['hmid']['tone'],
                               case['hbass']['tone'])))


def adapt_case(inp, case_list=None, notes=None):
    if case_list:
        best_case, similarity = case_list[0]
        pprint("Case " + str(inp['id']) + " : " + str(similarity))
        if similarity < 0.9:
            change_chord(best_case)
        for key in ['htreb', 'hmid', 'hbass', 'hother']:
            inp[key] = best_case[key]
    else:
        for note in ['htreb', 'hmid', 'hbass']:
            inp[note] = inp['signif_note']
        change_chord(inp)
    if notes and (len(notes) == 2):
        change1 = list(set(['htreb', 'hmid', 'hbass']) - set(notes))[0]
        r = randint(0, 1)
        change2 = notes[r]
        inp[change1], inp[change2] = inp[change2], inp[change1]


def verify(inp_case, out_buffer):

    def check_consec(inp, prev, unit):
        if unit == 5:
            d1, d2 = 5, 7
        note_pos = ['htreb', 'hmid', 'hbass', 'signif_note']
        for n1, n2 in combinations(note_pos, 2):
            try:
                diff1 = abs(prev[n1]['tone'] - prev[n2]['tone'])
                diff2 = abs(inp[n1]['tone'] - inp[n2]['tone'])
            except TypeError as e:
                print e
                print inp
            if (diff1 == diff2) and ((diff1 == d1) or (diff1 == d2)):
                return (True, [n1, n2])
        return (False, None)

    consec = True
    round = 1
    while consec is True:
        for unit in [5]:
            consec, notes = check_consec(inp_case, out_buffer[-1], unit)
            if (consec is True) and (notes is not None):
                print("Consecutive " + str(unit) + "ths on " + str(notes))
                adapt_case(inp_case, notes=notes)
        if round > 6:
            break
        else:
            round += 1


def main():
    output_buffer = []
    inp = 'input3_b359'
    for inp_case in get_case(inp):
        cases = [case for case in retrieve_cases(inp_case)]
        adapt_case(inp_case, case_list=cases)
        if len(output_buffer) > 0:
            verify(inp_case, output_buffer)
        output_buffer.append(inp_case)
    #pprint(output_buffer)
    LilyFile(inp, output_buffer)

if __name__ == '__main__':
    sys.exit(main())
