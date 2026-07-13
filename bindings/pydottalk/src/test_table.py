from pathlib import Path

from table import Table

repo_root = Path(__file__).resolve().parents[3]
t = Table(str(repo_root / "dottalkpp" / "data" / "dbf" / "sandbox" / "STUDENTS.dbf"))
t.open()

print("fields:", t.field_names())
print("count :", t.rec_count())

t.top()
print("first :", t.read())

t.skip(1)
print("next  :", t.read())

print("iter sample:")
for r in t.records(limit=3):
    print(" ", r)

t.close()
