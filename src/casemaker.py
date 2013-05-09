from __future__ import division  # for Python 2.x tru division
import sys
import re
from dbconnector import grant_connection
from casestructure import Case, Note


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


def insert_case(case, commit=False):
    """
    The commit is provided as a hook so that when called from another module,
    this function will have a way to commit the insertions.
    """
    with grant_connection(commit) as dbcon:
        for note in ['signif_note', 'htreb', 'hmid', 'hbass']:
            if case.features[note] is not None:
                insert_note(case.features[note], dbcon)
                case.features[note] = case.features[note].features['id']
            else:
                case.features[note] = 'null'
        for notes in ['other_notes', 'hother']:
            if case.features[notes] is not None:
                for note in case.features[notes]:
                    insert_note(note, dbcon)
                    n = case.features[notes].index(note)
                    case.features[notes][n] = note.features['id']
        for note in ['sig_note_m1', 'sig_note_m2', 'sig_note_p1',
                     'sig_note_p2']:
            if case.features[note] is not None:
                case.features[note] = case.features[note].features['id']
            else:
                case.features[note] = 'null'
        query = ("INSERT INTO CASEBASE VALUES ({id}, '{key}', {dos}, "
                 "{cadence}, {signif_note}, '{other_notes}', {sig_note_m1}, "
                 "{sig_note_m2}, {sig_note_p1}, {sig_note_p2}, {htreb}, "
                 "{hmid}, {hbass}, '{hother}')".format(**case.features))
        dbcon.execute(query)


def insert_note(note, note_con):
    """
    This function needs the same connection object as the one for inserting
    cases as all the insertions have to be commited.
    """
    query = ("INSERT INTO NOTEBASE VALUES ({id}, {tone}, {degree}, "
             "{duration}, {pos_beat}, {pos_meas})".format(**note.features))
    note_con.execute(query)


def build_case(piece):
    """
    bpm is beat per measure
    btdrn is beat duration
    carry will be used if a note's duration is longer than the beat duartion
    these values are not being considered for now
    """
    query = "SELECT * FROM " + piece + " WHERE ID > 4"
    with grant_connection() as qdb:
        nquery = "SELECT Key, Time_Sig FROM METATABLE WHERE Table_Name = '"\
                 + piece + "'"
        # start position is also required from the query ( = received -1 )
        pos_meas = 0
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
        for row in get_next_beat(query):
            case = [case_num, 'M', 1.0, 0]
            sig_note_flag = False
            other_notes = []
            hother = []
            if row[1] is not None:
                pos_beat = 1
                for ntgrp in row[1].split(','):
                    match = re.search(r'(\w+)(\d)', ntgrp)
                    note = match.group(1)
                    duration = int(match.group(2))
                    # following code is not being used for now
                    if btdrn / duration > 1:
                        carry.append((note, 1 / (1 / duration - 1 / btdrn)))
                        duration = btdrn
                    # --------------------
                    try:
                        degree = scale.diatonic[note]
                    except KeyError:
                        print('Warning : Case :' + str(case_num) + ' '
                              + note + ' is not in the diatonic scale')
                        degree = 0
                    if not sig_note_flag:
                        case.append(Note(note_num, scale.chromatic[note],
                                         degree, duration, pos_beat,
                                         pos_meas + 1))
                        sig_note_flag = True
                    else:
                        other_notes.append(Note(note_num,
                                                scale.chromatic[note],
                                                degree, duration, 2,
                                                pos_meas + 1))
                    note_num += 1
                if len(other_notes) == 0:
                    case.append(None)
                else:
                    case.append(other_notes)
            else:
                case.extend([None, None])
            if row[2] is not None:
                #pdb.set_trace()
                harmony = {'t': None, 'm': None, 'b': None}
                pos_beat = 1
                next_note = 't'
                # 't' : trebble, 'm' : mid, 'b' : bass
                switch_other = False
                for ntgrp in row[2].split(','):
                    match = re.search(r'(\w+)(\d)', ntgrp)
                    note = match.group(1)
                    duration = int(match.group(2))
                    try:
                        degree = scale.diatonic[note]
                    except KeyError:
                        print('Warning : Case : ' + str(case_num) + '. '
                              + note + ' is not in the diatonic scale')
                        degree = 0
                    if switch_other:
                        hother.append(Note(note_num, scale.chromatic[note],
                                           degree, duration, 2, pos_meas + 1))
                        switch_other = False
                        if next_note == 't':
                            next_note = 'm'
                        else:
                            next_note = 'b'
                    else:
                        harmony[next_note] = Note(note_num,
                                                  scale.chromatic[note],
                                                  degree, duration, pos_beat,
                                                  pos_meas + 1)
                        if duration == btdrn and next_note == 't':
                            next_note = 'm'
                        elif duration == btdrn and next_note == 'm':
                            next_note = 'b'
                        else:
                            switch_other = True
                    note_num += 1
                case.extend([harmony['t'], harmony['m'], harmony['b']])
                if len(hother) == 0:
                    case.append(None)
                else:
                    case.append(hother)
            else:
                case.extend([None, None, None, None])
            pos_meas = (pos_meas + 1) % btdrn
            case_num += 1
            yield case


def get_case(piece):
    """
    To account for notes ahead of the current note, a list called 'window'
    will be used which will act as a buffer for cases.
    """
    next_case = build_case(piece)
    window = [None, None, None, next(next_case), next(next_case)]
    while True:
        try:
            case = next(next_case)
        except StopIteration:
            case = None
        window.pop(0)
        window.append(case)
        this = window[2]
        if this is None:
            raise StopIteration
        for p, c in [(1, 6), (0, 7), (3, 8), (4, 9)]:
            if window[p] is None:
                this.insert(c, None)
            else:
                this.insert(c, window[p][4])
        yield Case(*this)


def populate_db():
    """
    The cases had to be collected in a list so that all the other connections
    to the database could be closed.
    """
    piece = 'bwv1p6'
    cases = [case for case in get_case(piece)]
    for case in cases:
        insert_case(case, True)


if __name__ == '__main__':
    sys.exit(populate_db())
