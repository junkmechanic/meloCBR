import os
from subprocess import call
from dbconnector import grant_connection


TEMPLATE = """
\\version "2.16.0"

\score
  {{
    \\new PianoStaff
      <<
        \\new Staff
          {{
            \key {key} \major
            \\time 4/4
            \clef "treble"
            \\relative c''
              {{
                {melody}
              }}
          }}
        \\new Staff
          {{
            \key {key} \major
            \\time 4/4
            \clef "bass"
            <<
              \\relative c''
                {{
                  {htreb}
                }}
              \\relative c'
                {{
                  {hmid}
                }}
              \\relative c
                {{
                  {hbass}
                }}
            >>
          }}
      >>
    \midi
      {{
        \\tempo 4 = 80
      }}
    \layout  {{ }}
  }}
"""


class LilyScale:

    tones = ['c', 'des', 'd', 'ees', 'e', 'f', 'ges', 'g', 'aes', 'a', 'bes',
             'b']

    def __init__(self, k):
        self.key = k
        self.chromatic = {}
        pointer = LilyScale.tones.index(self.key)
        for i in range(1, 13):
            self.chromatic.update({i: LilyScale.tones[pointer]})
            pointer = (pointer + 1) % 12


class LilyFile:
    def __init__(self, name, case_list):
        self.name = name
        self.key = self.get_key()
        self.length = 0
        self.content = self.generate_content(case_list)
        self.compile()

    def get_key(self):
        """
        This is lousy because now this module has to connect to the database
        to get the value of the key. But due to lack of foresight the other
        modules have no room for a quick fix and this has to do for now.
        """
        with grant_connection() as qdb:
            nquery = "SELECT Key FROM METATABLE " + \
                     "WHERE Table_Name = '" + self.name + "'"
            key = qdb.execute(nquery).fetchone()[0]
        return key.lower()

    def generate_content(self, case_list):
        scale = LilyScale(self.key)
        filler = ["", "", "", ""]
        notes = ['signif_note', 'htreb', 'hmid', 'hbass']
        init_rests = case_list[0]['signif_note']['pos_meas']
        if(init_rests > 1):
            for i in range(init_rests - 1):
                self.length += 1
                filler = map(lambda s: s + 'r ', filler)
        for case in case_list:
            self.length += 1
            cntr = 0
            for note in notes:
                if case[note]:
                    filler[cntr] += scale.chromatic[case[note]['tone']] + ' '
                else:
                    #filler[cntr] += filler[cntr][-2:]
                    print("Error with case!!")
                    print(case)
                cntr += 1
            if(self.length % 4 == 0):
                filler = list(map(lambda s: s + '| ', filler))
        return TEMPLATE.format(key=self.key, melody=filler[0], htreb=filler[1],
                               hmid=filler[2], hbass=filler[3])

    def compile(self):
        os.chdir('/home/ankur/home/ankur')
        filename = '{}.ly'.format(self.name)
        with open(filename, 'w') as outfile:
            outfile.write(self.content)
        call(['lilypond', filename])
