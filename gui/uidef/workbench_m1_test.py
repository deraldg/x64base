"""M1 target refusal and menu hierarchy checks; compiled lifetime proof is --m1-smoke."""
import tempfile
from pathlib import Path
import author_workbench
import manifest
import uidef
import uidef_wx
import uidef_html
import uidef_text
from _vfp import Dbf


def main():
    with tempfile.TemporaryDirectory(prefix='uidef-m1-') as directory:
        path = Path(directory) / 'workbench'
        author_workbench.main(str(path))
        dbf = str(path.with_suffix('.DBF'))
        rows = list(Dbf(dbf).rows())
        assert len(uidef.modal_forms(rows)) == 7
        src, notes, count = uidef_wx.generate(dbf, dispatch=True)
        assert not notes, notes
        assert count == len(rows) - 1
        for target in (uidef_html.generate, uidef_text.render):
            try:
                target(dbf)
            except ValueError as error:
                assert 'REFUSED Modal' in str(error), str(error)
            else:
                raise AssertionError('Target silently discarded Modal')
        import uidef_tk
        try:
            uidef_tk.build_window(dbf)
        except ValueError as error:
            assert 'REFUSED Modal' in str(error)
        else:
            raise AssertionError('Tk silently discarded Modal')
        m = manifest.manifest(dbf)
        # Tk render refusal above happens before importing its optional GUI
        # runtime; this Python installation has no _tkinter extension.
        for profile in (manifest.PROFILE_MINIMAL, manifest.profile_text(), manifest.profile_html()):
            assert any(level == 'REFUSE' and name.startswith('Modal:') for level, name, _ in manifest.check(m, profile))
        # The same R18 structure must work below the first menu level and carry
        # mnemonic/shortcut semantics; malformed top-level leaves must refuse.
        rows += [dict(RECKIND='OBJ', OBJID='DEEP_ITEM', PARENT='MC0', KIND='menu', ORDINAL=20, PROPS='Caption = Deep\nMnemonic = 1'),
                 dict(RECKIND='OBJ', OBJID='DEEP_MENU', PARENT='DEEP_ITEM', KIND='menu', PROPS='Container = .T.'),
                 dict(RECKIND='OBJ', OBJID='DEEP_LEAF', PARENT='DEEP_MENU', KIND='menu', PROPS='Caption = Run\nKey = Ctrl+R', HANDLERS='Click = session.refresh / host')]
        uidef.write(dbf, str(path.with_suffix('.FPT')), rows)
        src, notes, _ = uidef_wx.generate(dbf, dispatch=True)
        assert not notes and 'AppendSubMenu(w_DEEP_ITEM, "D&eep")' in src and 'Run\\tCtrl+R' in src
        rows[-1]['PARENT'] = 'MENUBAR'
        uidef.write(dbf, str(path.with_suffix('.FPT')), rows)
        try:
            uidef_wx.generate(dbf, dispatch=True)
        except ValueError as error:
            assert 'menubar items must open a submenu' in str(error)
        else:
            raise AssertionError('Malformed hierarchy accepted')
    print('PASS M1 design: seven authored modals; wx nested menu hierarchy, mnemonics and keys; malformed menu refusal; Tk/HTML/text modal refusal')


if __name__ == '__main__':
    main()
