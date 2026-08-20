#!/usr/bin/env python3
"""Author the sixteen NEGATIVE and PROPERTY fixtures the lane's refusals are measured on. R75.

Written because they did not exist anywhere durable. FRAMEDEMO, FLOWDEMO, FONTDEMO
and AUTHORED each have an author script and regenerate byte-identically apart from
the DBF header's date stamp. These sixteen did not: they were built ad hoc during
R66 and R70 and lived only in the session container that made them.

Every refusal count in R66, R70 and R73 -- "6 of 18 refused", N1_editable_grid,
P2_order_ok -- rests on these files. The cited-paths gate never saw the gap because
the rulings cite them by BARE NAME and the gate matches PATHS: evidence cited by
name is outside what that gate can reach.

    python author_cases.py            # all sixteen
    python author_cases.py N5_ordinal_spec
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uidef

CASES = {
    'N1_editable_grid': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'G1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'grid', 'BINDING': 'students.lname', 'PROVENANCE': 'authored', 'PROPS': 'ReadOnly = .F.'},
    ],
    'N2_tree_children': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'T1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'tree', 'BINDING': 'students', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'L1', 'PARENT': 'T1', 'ORDINAL': '1', 'KIND': 'label', 'PROVENANCE': 'authored', 'PROPS': 'Caption = "x"'},
    ],
    'N3_statusbar_bound': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'B1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'statusbar', 'BINDING': 'students.lname', 'PROVENANCE': 'authored'},
    ],
    'N4_shows_bogus': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'B1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'statusbar', 'PROVENANCE': 'authored', 'PROPS': 'Shows = "rows gpa"'},
    ],
    'N5_ordinal_spec': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'G1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'grid', 'BINDING': '#2,#3', 'PROVENANCE': 'authored'},
    ],
    'N6_join_no_relation': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'G1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'grid', 'BINDING': 'students.lname,enroll.grade', 'PROVENANCE': 'authored'},
    ],
    'N7_spec_on_control': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'T1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'text', 'BINDING': 'students.lname,enroll.grade', 'PROVENANCE': 'authored'},
    ],
    'N8_tree_field': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'T1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'tree', 'BINDING': 'students.lname', 'PROVENANCE': 'authored'},
    ],
    'N9_star_ok': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'G1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'grid', 'BINDING': '*', 'PROVENANCE': 'authored'},
    ],
    'N10_alias_star_ok': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'G1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'grid', 'BINDING': 'enroll.*', 'PROVENANCE': 'authored'},
    ],
    'P1_order_bad': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'G1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'grid', 'BINDING': 'students.lname', 'PROVENANCE': 'authored', 'PROPS': 'Order = "lname"'},
    ],
    'P2_order_ok': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'G1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'grid', 'BINDING': 'students.lname', 'PROVENANCE': 'authored', 'PROPS': 'Order = "cnx"'},
    ],
    'P3_rowlimit_zero': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'G1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'grid', 'BINDING': 'students.lname', 'PROVENANCE': 'authored', 'PROPS': 'RowLimit = 0'},
    ],
    'P4_rowlimit_big': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'G1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'grid', 'BINDING': 'students.lname', 'PROVENANCE': 'authored', 'PROPS': 'RowLimit = 500'},
    ],
    'P5_widths_mismatch': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'G1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'grid', 'BINDING': 'students.lname,students.fname', 'PROVENANCE': 'authored', 'PROPS': 'ColumnWidths = "90"'},
    ],
    'P6_widths_ok': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"', 'SOURCE': 'Alias = students\nTable = STUDENTS.DBF\nAlias = enroll\nTable = ENROLL.DBF\nRelation = students -> enroll ON SID'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'G1', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'grid', 'BINDING': 'students.lname,students.fname', 'PROVENANCE': 'authored', 'PROPS': 'ColumnWidths = "90,120"'},
    ],
}


def main(only=None):
    made = 0
    for stem, rows in sorted(CASES.items()):
        if only and stem != only:
            continue
        n, rlen, hlen = uidef.write(stem + '.DBF', stem + '.FPT', rows)
        print('%-22s records=%d rlen=%d hlen=%d' % (stem + '.DBF', n, rlen, hlen))
        made += 1
    if only and not made:
        print('no such case: %s' % only)
        return 2
    print('%d fixture(s) authored' % made)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
