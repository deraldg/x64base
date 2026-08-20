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
    # R85. The splitter's arity rule, both sides of it. wxSplitterWindow holds
    # exactly two panes, so a document meaning three panes means two splitters --
    # and a checker that only ever sees the passing case has not checked anything.
    'N11_splitter_three_panes': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'SP', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'splitter', 'FLOW': 'row', 'PROVENANCE': 'authored', 'PROPS': 'MinPane = 120'},
        {'RECKIND': 'OBJ', 'OBJID': 'A', 'PARENT': 'SP', 'ORDINAL': '1', 'KIND': 'list', 'PROVENANCE': 'authored', 'PROPS': 'Weight = 0'},
        {'RECKIND': 'OBJ', 'OBJID': 'B', 'PARENT': 'SP', 'ORDINAL': '2', 'KIND': 'list', 'PROVENANCE': 'authored', 'PROPS': 'Weight = 1'},
        {'RECKIND': 'OBJ', 'OBJID': 'C', 'PARENT': 'SP', 'ORDINAL': '3', 'KIND': 'list', 'PROVENANCE': 'authored', 'PROPS': 'Weight = 1'},
    ],
    # R85. The shape measured from src/gui/wx/main_frame.cpp:700 --
    # SplitVertically(area_panel, splitter, 220) with SetMinimumPaneSize(120),
    # and gravity 0.0 because that file never calls SetSashGravity.
    'P7_splitter_ok': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'measured', 'PROPS': 'SourceFile = "src/gui/wx/main_frame.cpp"'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'measured'},
        {'RECKIND': 'OBJ', 'OBJID': 'WORK', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'splitter', 'FLOW': 'row',
         'PROVENANCE': 'measured', 'PROPS': 'MinPane = 120\nWeight = 1\nFill = true',
         'ORIGIN': 'origin_width = 220',
         'NOTES': 'work_splitter->SplitVertically(area_panel, splitter, 220); root_sizer->Add(work_splitter, 1, wxEXPAND ...) main_frame.cpp:700,703'},
        {'RECKIND': 'OBJ', 'OBJID': 'AREAP', 'PARENT': 'WORK', 'ORDINAL': '1', 'KIND': 'list',
         'PROVENANCE': 'measured', 'PROPS': 'Weight = 0', 'NOTES': 'first pane holds its size: gravity 0.0'},
        {'RECKIND': 'OBJ', 'OBJID': 'MAIN', 'PARENT': 'WORK', 'ORDINAL': '2', 'KIND': 'list',
         'PROVENANCE': 'measured', 'PROPS': 'Weight = 1', 'NOTES': 'second pane absorbs the resize'},
    ],
    # R85.1. This IS the P7 that shipped for one afternoon, kept as a refusal.
    # Built and run under Xvfb it renders a sash at 119 while saying 220. The
    # document is not malformed and every field is legal -- it is simply not
    # going to get what it asked for, and that is what the checker now says.
    'N12_splitter_origin_no_weight': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'authored', 'PROPS': 'SourceFile = "NEG"'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'SP', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'splitter', 'FLOW': 'row',
         'PROVENANCE': 'authored', 'PROPS': 'MinPane = 120', 'ORIGIN': 'origin_width = 220',
         'NOTES': 'no Weight: measured 220 asked, 119 rendered'},
        {'RECKIND': 'OBJ', 'OBJID': 'A', 'PARENT': 'SP', 'ORDINAL': '1', 'KIND': 'list', 'PROVENANCE': 'authored'},
        {'RECKIND': 'OBJ', 'OBJID': 'B', 'PARENT': 'SP', 'ORDINAL': '2', 'KIND': 'list', 'PROVENANCE': 'authored'},
    ],
    # R85.2. The shipped frame is not one splitter, it is two: a vertical sash
    # at 220 whose SECOND pane is itself a horizontal splitter at 500
    # (main_frame.cpp:697-703). P7 flattened that to two list boxes, which
    # proved the control renders but never proved a pane may BE a splitter.
    # Transcribed here so the recursion is a fixture and not an assumption.
    'P8_splitter_nested': [
        {'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'measured', 'PROPS': 'SourceFile = "src/gui/wx/main_frame.cpp"'},
        {'RECKIND': 'OBJ', 'OBJID': 'F1', 'ORDINAL': '1', 'KIND': 'form', 'FLOW': 'column', 'PROVENANCE': 'measured',
         'ORIGIN': 'origin_width = 1000\norigin_height = 700',
         'NOTES': 'stated because the inner sash sits at 500: a frame shorter than '
                  'that cannot show the position the document names, and the '
                  'default 620x460 would have clamped it silently'},
        {'RECKIND': 'OBJ', 'OBJID': 'WORK', 'PARENT': 'F1', 'ORDINAL': '1', 'KIND': 'splitter', 'FLOW': 'row',
         'PROVENANCE': 'measured', 'PROPS': 'MinPane = 120\nWeight = 1\nFill = true',
         'ORIGIN': 'origin_width = 220',
         'NOTES': 'work_splitter->SplitVertically(area_panel, splitter, 220); '
                  'root_sizer->Add(work_splitter, 1, wxEXPAND|...) main_frame.cpp:700,703'},
        {'RECKIND': 'OBJ', 'OBJID': 'AREAP', 'PARENT': 'WORK', 'ORDINAL': '1', 'KIND': 'list',
         'PROVENANCE': 'measured', 'NOTES': 'area_panel'},
        {'RECKIND': 'OBJ', 'OBJID': 'INNER', 'PARENT': 'WORK', 'ORDINAL': '2', 'KIND': 'splitter', 'FLOW': 'column',
         'PROVENANCE': 'measured', 'PROPS': 'MinPane = 120',
         'ORIGIN': 'origin_height = 500',
         'NOTES': 'splitter->SplitHorizontally(notebook_, log_, 500) main_frame.cpp:697. '
                  'No Weight and none needed: a pane of a splitter already fills'},
        {'RECKIND': 'OBJ', 'OBJID': 'NBK', 'PARENT': 'INNER', 'ORDINAL': '1', 'KIND': 'list',
         'PROVENANCE': 'measured',
         'NOTES': 'notebook_; a list stands in so this fixture tests the sash and '
                  'not the pageset'},
        {'RECKIND': 'OBJ', 'OBJID': 'LOG', 'PARENT': 'INNER', 'ORDINAL': '2', 'KIND': 'text',
         'PROVENANCE': 'measured', 'PROPS': 'ReadOnly = true\nMultiline = true',
         'NOTES': 'log_ = wxTextCtrl(wxTE_MULTILINE|wxTE_READONLY|wxTE_RICH2)'},
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
