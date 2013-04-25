import sys
import re
from dbconnector import grant_connection
#from casestructure import Case, Note


class Scale(object):

    tones = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
    major_scale = [(1, 1), (3, 2), (5, 3), (6, 4), (8, 5), (10, 6), (12, 7)]

    def __init__(self, k):
        self.key = k
        self.chromatic = {}
        self.diatonic = {}
        pointer = Scale.tones.index(self.key)
        for i in range(1, 13):
            self.chromatic.update({Scale.tones[pointer]: i})
            i += 1
            pointer = (pointer + 1) % 12
        for t, d in Scale.major_scale:
            for k, v in self.chromatic.items():
                if t == v:
                    self.diatonic[k] = d
                    break


def get_next_beat(query):
    with grant_connection() as dbconnect:
        for row in dbconnect.get_case(query):
            yield row


def build_casebase(piece):
    """
    bpm is beat per measure
    btdrn is beat duration
    both these values are not being considered for the prototype
    """
    query = "SELECT * FROM " + piece + " WHERE ID > 4"
    with grant_connection() as qdb:
        nquery = "SELECT Key, Time_Sig FROM METATABLE WHERE Table_Name = '"\
                 + piece + "'"
        # start position is also required from the query
        pos = 1
        metadata = qdb.execute(nquery).fetchone()
        scale = Scale(metadata[0])
        #bpm = int(metadata[1].split('/')[0])
        #btdrn = int(metadata[1].split('/')[1])
        carry = []
        nquery = "SELECT MAX(ID) FROM CASEBASE"
        case_num = qdb.execute(nquery).fetchone()[0] + 1
        nquery = "SELECT MAX(NID) FROM NOTEBASE"
        note_num = qdb.execute(nquery).fetchone()[0] + 1
        print(scale.chromatic, scale.diatonic)
        case = [case_num, scale.key, 1.0, 1]
        for row in get_next_beat(query):
            sig_note_flag = False
            other_notes = None
            if row[1] is not None:
                for ntgrp in row[1].split(','):
                    match = re.search(r'(\w+)(\d)', ntgrp)
                    note = match.group(1)
                    duration = int(match.group(2))
                    #the number '4' below will be replaced by btdrn
                    factor = 4 / duration
                    if factor > 1:
                        duration = 4
                        carry.append((note, factor - 1))
                    if not sig_note_flag:
                        case
            else:
                melody = None
            if row[2] is not None:
                harmony = row[2].split(',')
            else:
                harmony = None


if __name__ == '__main__':
    piece = 'bwv1p6'
    build_casebase(piece)
    sys.exit()
