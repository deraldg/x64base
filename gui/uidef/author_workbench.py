#!/usr/bin/env python3
"""Author the Workbench. Layout is data; host supplies actions.

The catalog is an invocation input, not a UIDEF SOURCE work area. These unbound
controls render immutable service results, following author_mainframe.py.
"""
import sys
import uidef


def main(stem='WORKBENCH'):
    rows = [dict(RECKIND='DOC', OBJID='DOC', PROVENANCE='authored',
                 NOTES='Saved catalogs and a private, serialized live engine session.')]

    def obj(oid, parent, kind, ordinal, caption='', flow='', weight=0, pairs=()):
        props = [('Weight', str(weight)), ('Fill', '.T.')]
        if caption:
            props.append(('Caption', '"' + caption + '"'))
        props.extend(pairs)
        rows.append(dict(RECKIND='OBJ', OBJID=oid, PARENT=parent, KIND=kind,
                         ORDINAL=ordinal, FLOW=flow, PROVENANCE='authored',
                         PROPS=uidef.props(props)))

    obj('WB', '', 'form', 1, 'ArcticTalk Workbench', 'column')
    rows[-1]['ORIGIN'] = uidef.props([('ORIGIN_WIDTH', '1280'), ('ORIGIN_HEIGHT', '880'),
                                    ('ORIGIN_SCALE', 'px')])
    # R18: container -> opener item -> submenu container.
    obj('MENUBAR', 'WB', 'menu', 0, pairs=[('Container', '.T.')])
    menus = [
        ('File', [('New workspace...', 'session.new', 'Ctrl+N'),
                  ('Open tables...', 'session.open_workspace', 'Ctrl+O'),
                  ('Load workspace...', 'session.load_workspace', 'Ctrl+L'),
                  ('Save image...', 'session.save', 'Ctrl+S'),
                  ('Open image file...', 'image.open', ''),
                  ('-', '', ''), ('Exit', 'view.exit', 'Alt+F4')]),
        ('Workspace', [('New child...', 'session.child', ''),
                       ('Switch to selected workspace', 'session.switch', ''),
                       ('Close current workspace', 'session.close', ''),
                       ('Refresh', 'session.refresh', 'F5')]),
        ('Table', [('Select highlighted area', 'session.area', ''),
                   ('Browse selected table', 'table.refresh', ''),
                   ('Edit field...', 'table.edit', ''),
                   ('Commit table', 'table.commit', ''),
                   ('Rollback table', 'table.rollback', '')]),
        ('View', [('Saved catalogs', 'view.catalogs', ''),
                  ('Live session', 'view.live', ''),
                  ('Database images', 'view.images', ''),
                  ('Paths and defaults', 'paths.show', ''),
                  ('Command input', 'view.command', 'Ctrl+K')]),
        ('Tools', [('Show native paths', 'paths.refresh', ''),
                   ('Run initialization', 'paths.init', ''),
                   ('Run script...', 'session.run_script', 'Ctrl+R')]),
        ('Help', [('Workbench help', 'view.help', 'F1'), ('About', 'view.about', '')]),
        ('Record', [('First record', 'table.first', ''), ('Previous record', 'table.back', ''),
                    ('Next record', 'table.forward', ''), ('Last record', 'table.last', ''),
                    ('Go to record...', 'table.go', ''), ('-', '', ''),
                    ('Filter...', 'table.filter', ''), ('Index order...', 'table.order', ''),
                    ('Seek key...', 'table.seek', ''), ('Show/hide deleted', 'table.deleted', ''),
                    ('-', '', ''), ('Append blank...', 'table.append', ''),
                    ('Delete selected record...', 'table.delete', ''), ('Recall selected record...', 'table.recall', ''),
                    ('Set field NULL...', 'table.null', '')]),
    ]
    for mi, (caption, items) in enumerate(menus):
        opener, container = 'M%d' % mi, 'MC%d' % mi
        obj(opener, 'MENUBAR', 'menu', mi, caption, pairs=[('Mnemonic', '0')])
        obj(container, opener, 'menu', 0, pairs=[('Container', '.T.')])
        for ii, (label, handler, key) in enumerate(items):
            obj('MI%d_%d' % (mi, ii), container, 'menu', ii, '' if label == '-' else label,
                pairs=[('Separator', '.T.')] if label == '-' else ([('Key', key)] if key else []))
            if handler:
                rows[-1]['HANDLERS'] = 'Click = ' + handler + ' / host'
    obj('MAIN', 'WB', 'pageset', 1, flow='free', weight=1)
    obj('SAVED', 'MAIN', 'page', 1, 'Saved catalogs', 'column')
    obj('HEADER', 'SAVED', 'panel', 1, flow='column')
    obj('INTRO', 'HEADER', 'label', 1,
        'Saved workspaces / database images | Select a saved version, then load its definition or hydrate its image')
    obj('TOOLS', 'SAVED', 'panel', 2, flow='row')
    obj('PATH_BOX', 'TOOLS', 'panel', 1, flow='column', weight=1)
    obj('PATH', 'PATH_BOX', 'text', 1, weight=1)
    for oid, caption, ordinal, handler in (
            ('CHOOSE', 'Choose catalog...', 2, 'catalog.choose'),
            ('REFRESH', 'Refresh', 3, 'catalog.refresh'),
            ('INSPECT_IMG', 'Inspect image...', 4, 'image.inspect'),
            ('OPEN_IMG', 'Open image file...', 5, 'image.open')):
        obj(oid, 'TOOLS', 'button', ordinal, caption)
        rows[-1]['HANDLERS'] = 'Click = ' + handler + ' / host'
    obj('CAT_ACTIONS', 'SAVED', 'panel', 3, flow='row')
    for ordinal, (oid, caption, action) in enumerate((
            ('CAT_HYDRATE', 'Hydrate to RAM...', 'hydrate'),
            ('CAT_LOAD', 'Load definition...', 'load')), 1):
        obj(oid, 'CAT_ACTIONS', 'button', ordinal, caption)
        rows[-1]['HANDLERS'] = 'Click = catalog.' + action + ' / host'
    obj('CAT_NOTE', 'SAVED', 'label', 4, 'Select a saved workspace.')
    obj('BODY', 'SAVED', 'panel', 5, flow='row', weight=1)
    obj('NAV', 'BODY', 'panel', 1, flow='column', weight=3)
    obj('NAV_LABEL', 'NAV', 'label', 1, 'Workspace catalog')
    obj('FILTER_BOX', 'NAV', 'panel', 2, flow='column')
    obj('FILTER', 'FILTER_BOX', 'text', 1)
    obj('HISTORY_BOX', 'NAV', 'panel', 3, flow='column')
    obj('HISTORY', 'HISTORY_BOX', 'check', 1, 'Include superseded records')
    obj('LIST_BOX', 'NAV', 'panel', 4, flow='column', weight=1)
    obj('WORKSPACES', 'LIST_BOX', 'list', 1, weight=1)
    obj('DETAILS', 'BODY', 'pageset', 2, flow='free', weight=7)
    for ordinal, (oid, caption) in enumerate((('IDENTITY', 'Workspace'),
                                            ('MEMBERS', 'MINIDB contents'),
                                            ('POSTURE', 'Saved definition')), 1):
        obj(oid, 'DETAILS', 'page', ordinal, caption, 'column')
        obj(oid + '_V', oid, 'grid', 1, weight=1,
            pairs=[('ReadOnly', '.T.')])
    obj('LIVE', 'MAIN', 'page', 2, 'Live session', 'column')
    obj('LIVE_HEADER', 'LIVE', 'panel', 1, flow='column')
    obj('LIVE_NOTE', 'LIVE_HEADER', 'label', 1,
        'Live x64base session | Open table copy makes a copy | Commands operate on the paths you choose')
    obj('LIVE_TOOLS', 'LIVE', 'panel', 2, flow='column')
    obj('WS_ACTIONS', 'LIVE_TOOLS', 'panel', 1, flow='row')
    for ordinal, (oid, caption, action) in enumerate((
            ('NEW_ROOT', 'New workspace...', 'new'),
            ('OPEN_WS', 'Open...', 'open_workspace'),
            ('LOAD_WS', 'Load...', 'load_workspace'),
            ('NEW_CHILD', 'New child...', 'child'),
            ('SWITCH_WS', 'SWITCH workspace', 'switch')), 1):
        obj(oid, 'WS_ACTIONS', 'button', ordinal, caption)
        rows[-1]['HANDLERS'] = 'Click = session.' + action + ' / host'
    obj('AREA_ACTION', 'LIVE_TOOLS', 'panel', 2, flow='row')
    for ordinal, (oid, caption, action) in enumerate((
            ('OPEN_COPY', 'Open table copy...', 'open'),
            ('CLOSE_WS', 'Close current', 'close'),
            ('SELECT_AREA', 'SELECT area', 'area'),
            ('LIVE_REFRESH', 'Refresh', 'refresh')), 1):
        obj(oid, 'AREA_ACTION', 'button', ordinal, caption)
        rows[-1]['HANDLERS'] = 'Click = session.' + action + ' / host'
    obj('RECURSE_BOX', 'LIVE', 'panel', 3, flow='row')
    obj('RECURSION', 'RECURSE_BOX', 'check', 1, 'Save and close include nested workspaces')
    obj('SAVE_IMG', 'RECURSE_BOX', 'button', 2, 'Save image...')
    rows[-1]['HANDLERS'] = 'Click = session.save / host'
    obj('OPEN_L_IMG', 'RECURSE_BOX', 'button', 3, 'Open image file...')
    rows[-1]['HANDLERS'] = 'Click = image.open / host'
    obj('LIVE_PATHS', 'RECURSE_BOX', 'button', 4, 'Paths and defaults...')
    rows[-1]['HANDLERS'] = 'Click = paths.show / host'
    obj('LIVE_CURRENT', 'LIVE', 'panel', 4, flow='column')
    obj('CURRENT_NOTE', 'LIVE_CURRENT', 'label', 1, 'Starting engine session...')
    obj('COMMAND_ROW', 'LIVE', 'panel', 5, flow='row')
    obj('COMMAND_BOX', 'COMMAND_ROW', 'panel', 1, flow='column', weight=1)
    obj('COMMAND_TEXT', 'COMMAND_BOX', 'text', 1)
    obj('COMMAND_RUN', 'COMMAND_ROW', 'button', 2, 'Run command')
    rows[-1]['HANDLERS'] = 'Click = session.command / host'
    obj('SCRIPT_RUN', 'COMMAND_ROW', 'button', 3, 'Run script...')
    rows[-1]['HANDLERS'] = 'Click = session.run_script / host'
    obj('LIVE_BODY', 'LIVE', 'panel', 6, flow='row', weight=1)
    obj('LIVE_LISTBOX', 'LIVE_BODY', 'panel', 1, flow='column', weight=3)
    obj('NAV_FIND', 'LIVE_LISTBOX', 'panel', 1, flow='column')
    obj('NAV_QUERY', 'NAV_FIND', 'text', 1)
    obj('NAV_NOTE', 'LIVE_LISTBOX', 'label', 2, caption='Click to browse; Enter to SWITCH or SELECT.')
    obj('NAV_TREEBOX', 'LIVE_LISTBOX', 'panel', 3, flow='column', weight=1)
    obj('LIVE_TREE', 'NAV_TREEBOX', 'tree', 1, weight=1)
    obj('LIVE_DETAILS', 'LIVE_BODY', 'pageset', 2, flow='free', weight=7)
    for ordinal, (oid, caption) in enumerate((('LIVE_WS', 'Workspace'),
                                            ('LIVE_AREAS', 'Tables'),
                                            ('LIVE_LOG', 'Engine response')), 1):
        obj(oid, 'LIVE_DETAILS', 'page', ordinal, caption, 'column')
        if oid == 'LIVE_AREAS':
            obj('AREA_TOOLS', oid, 'panel', 1, flow='row')
            obj('AREA_ALLBOX', 'AREA_TOOLS', 'panel', 1, flow='column')
            obj('AREA_ALL', 'AREA_ALLBOX', 'check', 1, 'All workspaces')
            obj('AREA_NESTBOX', 'AREA_TOOLS', 'panel', 2, flow='column')
            obj('AREA_NEST', 'AREA_NESTBOX', 'check', 1, 'Include nested')
            obj('AREA_FIND', 'AREA_TOOLS', 'panel', 3, flow='column', weight=1)
            obj('AREA_QUERY', 'AREA_FIND', 'text', 1)
            obj('AREA_NOTE', oid, 'panel', 2, flow='column')
            obj('AREA_SCOPE', 'AREA_NOTE', 'label', 1, 'Choose a workspace to browse its tables.')
            obj('AREA_GRID', oid, 'panel', 3, flow='column', weight=1)
            obj('AREA_ROWS', 'AREA_GRID', 'grid', 1, weight=1, pairs=[('ReadOnly', '.T.')])
        else:
            obj(oid + '_V', oid, 'grid', 1, weight=1, pairs=[('ReadOnly', '.T.')])
    obj('LIVE_TABLE', 'LIVE_DETAILS', 'page', 4, 'Table', 'column')
    obj('TABLE_TOOLS', 'LIVE_TABLE', 'panel', 1, flow='row')
    for ordinal, (oid, caption, action) in enumerate((
            ('TABLE_TOP', 'First page', 'top'), ('TABLE_PREV', 'Previous page', 'previous'),
            ('TABLE_NEXT', 'Next page', 'next'), ('TABLE_REFR', 'Refresh', 'refresh'),
            ('TABLE_GOTO', 'Select record', 'select'), ('TABLE_VALUE', 'Open value...', 'value'),
            ('TABLE_IMG', 'Inspect image...', 'image')), 1):
        obj(oid, 'TABLE_TOOLS', 'button', ordinal, caption)
        rows[-1]['HANDLERS'] = 'Click = table.' + action + ' / host'
    obj('EDIT_TOOLS', 'LIVE_TABLE', 'panel', 2, flow='row')
    for ordinal, (oid, caption, action) in enumerate((
            ('EDIT_VALUE', 'Edit value...', 'edit'), ('EDIT_COMMIT', 'Commit table', 'commit'),
            ('EDIT_UNDO', 'Rollback table', 'rollback'), ('STORE_IMG', 'Store image...', 'store_image')), 1):
        obj(oid, 'EDIT_TOOLS', 'button', ordinal, caption)
        rows[-1]['HANDLERS'] = 'Click = table.' + action + ' / host'
    obj('EDIT_NOTE', 'EDIT_TOOLS', 'label', 5, 'Edits stay buffered until Commit.')
    obj('REC_TOOLS', 'LIVE_TABLE', 'panel', 3, flow='row')
    for ordinal, (oid, caption, action) in enumerate((
            ('REC_FIRST', 'First', 'first'), ('REC_BACK', 'Previous record', 'back'),
            ('REC_NEXT', 'Next record', 'forward'), ('REC_LAST', 'Last', 'last'),
            ('REC_GO', 'Go to...', 'go'), ('REC_FILTER', 'Filter...', 'filter'),
            ('REC_ORDER', 'Order...', 'order'), ('REC_SEEK', 'Seek...', 'seek')), 1):
        obj(oid, 'REC_TOOLS', 'button', ordinal, caption)
        rows[-1]['HANDLERS'] = 'Click = table.' + action + ' / host'
    obj('ROW_TOOLS', 'LIVE_TABLE', 'panel', 4, flow='row')
    for ordinal, (oid, caption, action) in enumerate((
            ('REC_APPEND', 'Append blank...', 'append'), ('REC_DELETE', 'Delete...', 'delete'),
            ('REC_RECALL', 'Recall...', 'recall'), ('REC_DELETED', 'Show/hide deleted', 'deleted'),
            ('FIELD_NULL', 'Set NULL...', 'null')), 1):
        obj(oid, 'ROW_TOOLS', 'button', ordinal, caption)
        rows[-1]['HANDLERS'] = 'Click = table.' + action + ' / host'
    obj('TABLE_NOTE', 'LIVE_TABLE', 'panel', 5, flow='column')
    obj('TABLE_STAT', 'TABLE_NOTE', 'label', 1, 'Type BROWSE or select this page to inspect the selected table.')
    obj('TABLE_DATA', 'LIVE_TABLE', 'panel', 6, flow='row', weight=1)
    obj('TABLE_ROWS', 'TABLE_DATA', 'panel', 1, flow='column', weight=6)
    obj('TABLE_GRID', 'TABLE_ROWS', 'grid', 1, weight=1, pairs=[('ReadOnly', '.T.')])
    obj('FIELD_PANE', 'TABLE_DATA', 'panel', 2, flow='column', weight=4)
    obj('FIELD_NOTE', 'FIELD_PANE', 'label', 1, 'Record view (F2 to edit)')
    obj('TABLE_FIELDS', 'FIELD_PANE', 'panel', 2, flow='column', weight=1)
    obj('FIELD_GRID', 'TABLE_FIELDS', 'grid', 1, weight=1, pairs=[('ReadOnly', '.T.')])
    obj('IMAGES', 'MAIN', 'page', 3, 'Database images', 'column')
    obj('IMAGE_HEAD', 'IMAGES', 'panel', 1, flow='column')
    obj('IMAGE_NOTE', 'IMAGE_HEAD', 'label', 1,
        'Select an image to hydrate or export. Nested images follow live DTX objects.')
    obj('IMAGE_ENTRY', 'IMAGES', 'panel', 2, flow='row')
    for ordinal, (oid, caption, action) in enumerate((
            ('IMG_SAVED', 'Choose saved image...', 'saved'),
            ('IMG_OPEN', 'Open image file...', 'open'),
            ('IMG_LIVE', 'View live tables', 'tables')), 1):
        obj(oid, 'IMAGE_ENTRY', 'button', ordinal, caption)
        rows[-1]['HANDLERS'] = 'Click = image.' + action + ' / host'
    obj('IMAGE_TOOLS', 'IMAGES', 'panel', 3, flow='row')
    for ordinal, (oid, caption, handler) in enumerate((
            ('HYD', 'Hydrate in new workspace...', 'image.hydrate'),
            ('HYDR_CHILD', 'Hydrate under current workspace...', 'image.child'),
            ('EXPORT_IMG', 'Export selected image...', 'image.export')), 1):
        obj(oid, 'IMAGE_TOOLS', 'button', ordinal, caption)
        rows[-1]['HANDLERS'] = 'Click = ' + handler + ' / host'
    obj('IMAGE_BODY', 'IMAGES', 'panel', 4, flow='row', weight=1)
    obj('IMAGE_LIST', 'IMAGE_BODY', 'panel', 1, flow='column', weight=4)
    obj('IMG_LIST_V', 'IMAGE_LIST', 'list', 1, weight=1)
    obj('IMAGE_INFO', 'IMAGE_BODY', 'panel', 2, flow='column', weight=6)
    obj('IMG_INFO_V', 'IMAGE_INFO', 'grid', 1, weight=1, pairs=[('ReadOnly', '.T.')])
    obj('FOOTER', 'WB', 'panel', 2, flow='column')
    obj('STATUS', 'FOOTER', 'label', 1, 'Loading the default workspace catalog...')
    obj('PATHS_PAGE', 'MAIN', 'page', 4, 'Paths and defaults', 'column')
    obj('PATHS_INTRO', 'PATHS_PAGE', 'label', 1,
        'Native SET PATH settings | DBF, INDEXES and LMDB follow SWITCH | Changes apply to this session')
    obj('PATHS_TOOLS', 'PATHS_PAGE', 'panel', 2, flow='row')
    for ordinal, (oid, caption, action) in enumerate((
            ('PATH_EDIT', 'Set selected path...', 'edit'),
            ('PATH_RESET', 'Reset paths', 'reset'),
            ('PATH_INIT', 'Run INIT', 'init'),
            ('PATH_REFRESH', 'Refresh', 'refresh'),
            ('PATH_CATALOG', 'Use default catalog', 'catalog')), 1):
        obj(oid, 'PATHS_TOOLS', 'button', ordinal, caption)
        rows[-1]['HANDLERS'] = 'Click = paths.' + action + ' / host'
    obj('PATHS_NOTE', 'PATHS_PAGE', 'panel', 3, flow='column')
    obj('PATH_CAT', 'PATHS_NOTE', 'label', 1, 'Default catalog: WORKSPACES/WORKSPACES.dbf')
    obj('PATHS_GRID', 'PATHS_PAGE', 'panel', 4, flow='column', weight=1)
    obj('PATHS_ROWS', 'PATHS_GRID', 'grid', 1, weight=1, pairs=[('ReadOnly', '.T.')])
    # Modal is a form property (R144). Layout and accept/cancel identities are
    # authored here; host code supplies values, validation and system pickers.
    for prefix, title, field, note in (
        ('NEW', 'New workspace', 'Workspace name', 'Create and switch to an empty workspace.'),
        ('HYD', 'Hydrate saved image to RAM', 'New workspace name', 'Tables and indexes go into RAM; memo sidecars remain on disk.'),
        ('OPEN', 'Open workspace tables', 'Table directory', 'Open tables from this directory into the current workspace.'),
        ('LOAD', 'Load workspace definition', 'Workspace definition (.dtschema or .dtschemas)', 'Choose where its tables live. Locations saved in the definition take priority.'),
        ('SAVE', 'Save database image', 'New image file (.minidb)', 'Save committed tables. Existing files are never replaced.'),
        ('RUN', 'Run script', 'Script file (.dts)', 'Choose the exact script to run. Starts in SET PATH SCRIPTS.'),
        ('OP', 'Table operation', 'Value', 'Acts on the selected table.')):
        form = prefix + '_FORM'
        obj(form, '', 'form', 10, title, 'column', pairs=[('Modal', '.T.')])
        rows[-1]['ORIGIN'] = uidef.props([('ORIGIN_WIDTH', '700'), ('ORIGIN_SCALE', 'px')])
        obj(prefix + '_NOTE', form, 'label', 1, note)
        obj(prefix + '_DEST', form, 'label', 2, 'Destination workspace')
        obj(prefix + '_LABEL', form, 'label', 3, field)
        obj(prefix + '_ROW', form, 'panel', 4, flow='row')
        obj(prefix + '_VALUE', prefix + '_ROW', 'text', 1, weight=1)
        if prefix not in ('NEW', 'HYD', 'OP'):
            obj(prefix + '_PICK', prefix + '_ROW', 'button', 2, 'Browse...')
            rows[-1]['HANDLERS'] = 'Click = workflow.browse / host'
        if prefix == 'SAVE':
            obj('SAVE_NESTED', form, 'check', 5, 'Include nested workspaces')
        if prefix == 'HYD':
            obj('HYD_CHILD', form, 'check', 5, 'Create under the current workspace')
        if prefix == 'OP':
            obj('OP_PICK', 'OP_ROW', 'button', 2, 'Browse index...')
            obj('OP_ORDER', form, 'panel', 5, flow='column')
            obj('OP_TAG_L', 'OP_ORDER', 'label', 1, 'Tag (for CDX/CNX)')
            obj('OP_TAG', 'OP_ORDER', 'text', 2)
            obj('OP_DESC', 'OP_ORDER', 'check', 3, 'Descending')
        if prefix == 'LOAD':
            obj('LOAD_ROOTS', form, 'panel', 5, flow='column')
            for ordinal, (short, caption, action) in enumerate((
                ('DBF', 'Table directory for this load', 'tables'),
                ('IDX', 'Index directory for this load', 'indexes')), 1):
                obj('LD_' + short + '_BOX', 'LOAD_ROOTS', 'panel', ordinal, flow='column')
                obj('LD_' + short + '_LAB', 'LD_' + short + '_BOX', 'label', 1, caption)
                obj('LD_' + short + '_ROW', 'LD_' + short + '_BOX', 'panel', 2, flow='row')
                obj('LD_' + short, 'LD_' + short + '_ROW', 'text', 1, weight=1)
                obj('LD_' + short + '_PICK', 'LD_' + short + '_ROW', 'button', 2, 'Browse...')
                rows[-1]['HANDLERS'] = 'Click = workflow.' + action + ' / host'
        obj(prefix + '_ERROR', form, 'label', 6, ' ')
        obj(prefix + '_ACTIONS', form, 'panel', 7, flow='row')
        obj(prefix + '_OK', prefix + '_ACTIONS', 'button', 1,
            {'NEW': 'Create', 'HYD': 'Hydrate to RAM', 'OPEN': 'Open', 'LOAD': 'Load', 'SAVE': 'Save', 'RUN': 'Run', 'OP': 'Apply'}[prefix],
            pairs=[('DialogResult', 'accept')])
        obj(prefix + '_CANCEL', prefix + '_ACTIONS', 'button', 2, 'Cancel', pairs=[('DialogResult', 'cancel')])
    widths = {name: width for name, kind, width in uidef.FIELDS if kind == 'C'}
    for row in rows:
        for key in ('OBJID', 'PARENT'):
            if len(row.get(key, '')) > widths[key]:
                raise ValueError(key + ' exceeds the design table width: ' + row[key])
    findings = uidef.validate(rows)
    if findings:
        raise ValueError(findings)
    uidef.write(stem + '.DBF', stem + '.FPT', rows)
    print(stem + ': authored ' + str(len(rows)) + ' rows; conformance findings: none')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'WORKBENCH')
