import lmdb

ENV_PATH = 'dottalkpp/data/indexes/STUDENTS.cdx.d'
TAG = b'LNAME'

env = lmdb.open(ENV_PATH, readonly=True, max_dbs=1024)
db = env.open_db(TAG)

print(env.stat())
print(db.stat())

env.close()