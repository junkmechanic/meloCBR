from __future__ import division
# the above line is for Python 2.x true division compatability
import sys
import re
from dbconnector import grant_connection
from casestructure import Case, Note
import pdb


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


def insert_case(case):
    with grant_connection() as dbcon:
        #dump case to db
        insert_note()


def insert_note(note):
    with grant_connection() as dbcon:
        query = "INSERT IN NOTEBASE VALUES ({id}, {tone}, {degree}, \
                {duration}, {pos_beat}, {pos_meas})".format(**note.features)


def build_casebase(piece):
    """
    To account for notes ahead of the current note, a list called 'window'
    will be used which will act as a buffer for cases.
    bpm is beat per measure
    btdrn is beat duration
    both these values are not being considered for the prototype
    """
    query = "SELECT * FROM " + piece + " WHERE ID > 4"
    with grant_connection() as qdb:
        nquery = "SELECT Key, Time_Sig FROM METATABLE WHERE Table_Name = '"\
                 + piece + "'"
        # start position is also required from the query
        pos_meas = 1
        metadata = qdb.execute(nquery).fetchone()
        scale = Scale(metadata[0])
        #bpm = int(metadata[1].split('/')[0])
        #btdrn = int(metadata[1].split('/')[1])
        btdrn = 4
        carry = []
        nquery = "SELECT MAX(ID) FROM CASEBASE"
        case_num = qdb.execute(nquery).fetchone()[0] + 1
        nquery = "SELECT MAX(NID) FROM NOTEBASE"
        note_num = qdb.execute(nquery).fetchone()[0] + 1
        case = [case_num, scale.key, 1.0, 0]
        for row in get_next_beat(query):
            sig_note_flag = False
            other_notes = []
            if row[1] is not None:
                pos_beat = 1
                for ntgrp in row[1].split(','):
                    match = re.search(r'(\w+)(\d)', ntgrp)
                    note = match.group(1)
                    duration = int(match.group(2))
                    if btdrn / duration > 1:
                        carry.append((note, 1 / (1 / duration - 1 / btdrn)))
                        duration = btdrn
                    if not sig_note_flag:
                        case.append(Note(note_num, scale.chromatic[note],
                                         scale.diatonic[note], duration,
                                         pos_beat, pos_meas))
                        sig_note_flag = True
                    else:
                        other_notes.append(Note(note_num,
                                                scale.chromatic[note],
                                                scale.diatonic[note],
                                                duration,
                                                pos_beat, pos_meas))
                    note_num += 1
                    pos_beat += 1
                if len(other_notes) == 0:
                    case.append(None)
                else:
                    case.append(other_notes)
            else:
                melody = None
            if row[2] is not None:
                harmony = row[2].split(',')
            else:
                harmony = None
            pos_meas += 1
            #yield Case(**case)


def populate_db():
    piece = 'bwv1p6'
    for case in build_casebase(piece):
        print (case)


if __name__ == '__main__':
    sys.exit(populate_db())
