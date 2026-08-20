#!/usr/bin/env python3
"""Author a UIDEF document describing src/gui/wx/main_frame.cpp. AIF-120 R78.

THE POINT OF THIS FILE IS THE ROUND TRIP, AND ROUND TRIPS ARE ALLOWED TO FAIL.

Every prior UIDEF document was authored to be describable. This one describes a
screen that already exists, written by hand, with no reference to this language --
2,140 lines of wx that R77 measured at 90% vocabulary coverage. Authoring it is
the test R77 called reconnaissance for: not "does the language have a word", but
"can the language carry the SCREEN".

WHAT IS DROPPED, AND IT IS STRUCTURAL
  The sample's top-level layout is three wxSplitterWindows:

      work_splitter->SplitVertically(area_panel, splitter, 220)
      splitter->SplitHorizontally(notebook_, log_, 500)
      ddict_splitter->SplitHorizontally(objects_grid, detail_notebook, 260)

  UIDEF has no word for a sash (R77 section 3). Each becomes a `panel` with a
  fixed FLOW and the sash position is LOST -- 220, 500 and 260 have nowhere to go.
  So this document renders the same tree with boundaries the user cannot move.
  That is the gap made visible rather than argued.

WHAT ELSE DOES NOT SURVIVE, all recorded in R78
  - CreateStatusBar(4). Four independent fields; `statusbar` renders one string.
  - Every caption. The sample resolves them through gui_text(GuiTextId::X, locale_).
    R33.4 ruled in this lane that a caption should be a reference -- `Caption =
    @FORM_STUDENTS_TITLE` -- and nothing ever implemented it, so the literals below
    are English text the sample does not actually contain.
  - The grids have NO BINDING. The sample fills them from code, and contract 10c
    requires a spec. A grid whose rows come from a handler is not describable.

Run:  python author_mainframe.py            -> MAINFRAME.DBF
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uidef

SOURCE = "\n".join([
    "Alias = workspace",
    "Table = (none -- the sample fills every grid from code)",
])


def main(stem='MAINFRAME'):
    out = [{'RECKIND': 'DOC', 'OBJID': 'DOC', 'PROVENANCE': 'measured',
            'SOURCE': SOURCE,
            'PROPS': uidef.props([('SourceFile', '"src/gui/wx/main_frame.cpp"')])}]

    def obj(oid, parent, kind, ordinal, flow='', binding='', pairs=(), notes='',
            weight=None, fill=None):
        pairs = list(pairs)
        if weight is not None:
            pairs.append(('Weight', str(weight)))
        if fill is not None:
            pairs.append(('Fill', '.T.' if fill else '.F.'))
        out.append({'RECKIND': 'OBJ', 'OBJID': oid, 'PARENT': parent, 'KIND': kind,
                    'ORDINAL': ordinal, 'FLOW': flow, 'BINDING': binding,
                    'PROVENANCE': 'measured', 'NOTES': notes,
                    'PROPS': uidef.props(list(pairs))})

    obj('F1', '', 'form', 1, flow='column',
        pairs=[('Caption', '"DotTalk++ Workspace"')],
        notes='wxFrame, main_frame.cpp:415')

    # ---- toolbar: a horizontal box sizer, which FLOW carries exactly ----------
    obj('TB', 'F1', 'panel', 1, flow='row', weight=0, fill=True,
        notes='toolbar BoxSizer(wxHORIZONTAL); Add(...,0,wxEXPAND)')
    obj('B_OPEN',  'TB', 'button', 1, pairs=[('Caption', '"Open Table"')],
        notes='gui_text(GuiTextId::OpenTable) -- a catalog key, not a literal')
    obj('B_REFR',  'TB', 'button', 2, pairs=[('Caption', '"Refresh"')],
        notes='gui_text(GuiTextId::Refresh)')
    obj('B_CLOSE', 'TB', 'button', 3, pairs=[('Caption', '"Close Area"')],
        notes='gui_text(GuiTextId::CloseArea)')
    obj('L_CMD',   'TB', 'label',  4, pairs=[('Caption', '"Command"')],
        notes='gui_text(GuiTextId::Command)')
    obj('T_CMD',   'TB', 'text',   5, weight=1,
        notes='wxTE_PROCESS_ENTER; toolbar->Add(command_, 1, ...)')
    obj('B_RUN',   'TB', 'button', 6, pairs=[('Caption', '"Run"')],
        notes='gui_text(GuiTextId::Run)')

    # ---- work_splitter: SASH 220 LOST -----------------------------------------
    obj('WORK', 'F1', 'panel', 2, flow='row', weight=1, fill=True,
        notes='was SplitVertically(sash=220); root_sizer->Add(work_splitter,1,wxEXPAND)')

    obj('AREAP', 'WORK', 'panel', 1, flow='column', weight=0, fill=True,
        notes='area_panel -- weight 0 approximates the 220px sash as a fixed pane')
    obj('L_AREAS', 'AREAP', 'label', 1, pairs=[('Caption', '"Areas"')],
        notes='gui_text(GuiTextId::Areas)')
    obj('LB_AREAS', 'AREAP', 'list', 2, weight=1, fill=True,
        notes='area_sizer->Add(areas_, 1, wxEXPAND)')

    # ---- inner splitter: SASH 500 LOST ----------------------------------------
    obj('MAIN', 'WORK', 'panel', 2, flow='column', weight=1, fill=True,
        notes='was SplitHorizontally(sash=500); 500px becomes a 3:1 RATIO -- an\n             approximation the author chooses, not a translation (R79)')

    obj('NB', 'MAIN', 'pageset', 1, flow='free', weight=3, fill=True,
        notes='notebook_, 7 pages; 3 of the 3:1 that approximates sash 500')
    pages = [('P_TAB', 'Tables'), ('P_IDX', 'Indexes'), ('P_REL', 'Relations'),
             ('P_DD', 'DDict'), ('P_WSG', 'Workspace Graph'),
             ('P_BRW', 'Browse'), ('P_STR', 'Structure')]
    for i, (oid, cap) in enumerate(pages, start=1):
        obj(oid, 'NB', 'page', i, flow='column', pairs=[('Caption', '"%s"' % cap)])

    for oid, host in (('G_TAB', 'P_TAB'), ('G_IDX', 'P_IDX'), ('G_REL', 'P_REL'),
                      ('G_BRW', 'P_BRW'), ('G_STR', 'P_STR')):
        obj(oid, host, 'grid', 1, pairs=[('ReadOnly', '.T.')],
            weight=1, fill=True,
            notes='wxGrid EnableEditing(false); rows come from code, so NO BINDING')

    # ---- the DDict page: a toolbar, then a third splitter (SASH 260 LOST) -----
    obj('DD_TB', 'P_DD', 'panel', 1, flow='row', weight=0, fill=True,
        notes='ddict_toolbar')
    obj('DD_REFR', 'DD_TB', 'button', 1, pairs=[('Caption', '"Refresh"')])
    obj('DD_FILT', 'DD_TB', 'text', 2, notes='ddict_filter_')
    obj('DD_STAT', 'DD_TB', 'label', 3, pairs=[('Caption', '"(status)"')],
        weight=1, notes='ddict_toolbar->Add(ddict_status_, 1, ...)')

    obj('DD_SPLIT', 'P_DD', 'panel', 2, flow='column', weight=1, fill=True,
        notes='was SplitHorizontally(sash=260); becomes a 1:1 ratio')
    obj('DD_OBJ', 'DD_SPLIT', 'grid', 1, pairs=[('ReadOnly', '.T.')],
        weight=1, fill=True, notes='ddict_objects_grid_')
    obj('DD_NB', 'DD_SPLIT', 'pageset', 2, flow='free', weight=1, fill=True,
        notes='ddict_detail_notebook_')
    dpages = [('DP_F', 'Fields'), ('DP_T', 'Tags'), ('DP_R', 'Relations'),
              ('DP_E', 'Evidence'), ('DP_S', 'Source')]
    for i, (oid, cap) in enumerate(dpages, start=1):
        obj(oid, 'DD_NB', 'page', i, flow='column', pairs=[('Caption', '"%s"' % cap)])
    for oid, host in (('DG_F', 'DP_F'), ('DG_T', 'DP_T'),
                      ('DG_R', 'DP_R'), ('DG_E', 'DP_E')):
        obj(oid, host, 'grid', 1, pairs=[('ReadOnly', '.T.')],
            weight=1, fill=True)
    obj('DG_SG', 'DP_S', 'grid', 1, pairs=[('ReadOnly', '.T.')],
        weight=0, fill=True, notes='ddict_source_grid_, proportion 0')
    obj('DG_ST', 'DP_S', 'text', 2, weight=1, fill=True,
        notes='ddict_source_sizer->Add(ddict_source_text_, 1, wxEXPAND)')

    obj('LOG', 'MAIN', 'text', 2, weight=1, fill=True,
        notes='log_ wxTextCtrl; 1 of the 3:1')

    # ---- statusbar: FOUR fields collapse to one -------------------------------
    obj('SB', 'F1', 'statusbar', 3,
        pairs=[('Shows', 'status rows recno order')],
        notes='CreateStatusBar(4); UIDEF renders ONE string -- 4 fields NOT EXPRESSIBLE')

    n, rlen, hlen = uidef.write(stem + '.DBF', stem + '.FPT', out)
    print('%s.DBF  records=%d rlen=%d hlen=%d' % (stem, n, rlen, hlen))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'MAINFRAME'))
