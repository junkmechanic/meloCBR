class Case(object):

    cs_features = ('id', 'key', 'dos', 'cadence', 'signif_note', 'other_notes',
                   'sig_note_m1', 'sig_note_m2', 'sig_note_p1', 'sig_note_p2',
                   'htreb', 'hmid', 'hbass', 'hother')

    def __init__(self, *args):
        self.features = dict(zip(self.cs_features, args))

    def __repr__(self):
        rtnstring = 'Case('
        for feature in self.cs_features:
            rtnstring += '{!r}, '.format(self.features[feature])
        rtnstring += ')'
        return(rtnstring)

    def __str__(self):
        rtnstring = ''
        for feature in self.cs_features:
            rtnstring += "{} : {}\n".format(feature, self.features[feature])
        return rtnstring


class Note(object):

    nt_features = ('id', 'tone', 'degree', 'duration', 'pos_beat', 'pos_meas')

    def __init__(self, *args):
        self.features = dict(zip(self.nt_features, args))

    def __repr__(self):
        return("Note({id}, {tone}, {degree}, {duration}, {pos_beat}, "
               "{pos_meas})".format(**self.features))

    def __str__(self):
        rtnstring = ''
        for feature in self.nt_features:
            rtnstring += "{} -> {}  ;".format(feature, self.features[feature])
        return rtnstring
