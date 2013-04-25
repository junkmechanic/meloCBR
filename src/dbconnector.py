import sqlite3
from contextlib import contextmanager


class DbConnect(object):

    def __init__(self):
        self.dbcon = sqlite3.connect('../db/DBMeloCBR')
        self.cur = self.dbcon.cursor()
        self.casecur = self.dbcon.cursor()
        self.notecur = self.dbcon.cursor()

    def execute(self, query):
        return(self.cur.execute(query))

    def get_case(self, query):
        return(self.casecur.execute(query))

    def get_note(self, query):
        return(self.notecur.execute(query))

    def close(self):
        self.dbcon.close()


@contextmanager
def grant_connection():
    dbcon = DbConnect()
    try:
        yield dbcon
    finally:
        dbcon.close()
