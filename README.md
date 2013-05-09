meloCBR
=======

A python project to build a system that could effetively harmonize a given
melody. The methodology followed is Case Based Reasoning to with support from a
database of Bach compositions.

----very early developmental phase-----

1. In fact there can be difference of opinions as to what note qualifies as
   bass or mid or trebble. The system assigns in the order it receives in. So
there can be times when the two notes played are mid and bass and the system
assigns them to trebble and mid.
2. While inserting a case in the database, in casemaker.py, the note variables are being
   converted to null values whereas the othernotes and hother lists, if empty,
will be replaced with 'None'. Correspondingly, in main.py, while retrieving,
these two varialbes are checked for inquality with 'None'. Changes will have to
be made in both the modules if null is to be used. However, since the values
stored in the database are string values, it shouldnt matter. That and I feel
that this will be easier to handle in other scenarios (evaluating the string
for being None).
3. Isolation level could have been used for the connection object. But I
   thought it better to have a wrapper commit hook instead. Keeps tighter
control over when the transactions would be commited, since it is not desirable
to commit the databse if there is an error midway while inserting cases from a
piece.


Lessons learnt:
1. Use ORM.
