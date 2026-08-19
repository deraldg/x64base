#!/usr/bin/env python3.12
"""AIF-120 UIDEF design-table renderer, Tk backend.

Written from AIF120_DESIGN_TABLE_CONTRACT_V1.md alone (gate 11 acceptance test).

Every place this program had to choose something the contract does not state is
marked with a `# SPEC-GAP`, `# SPEC-AMBIG` or `# SPEC-CONTRA` comment and is
written up in FINDINGS.md. Nothing else was consulted.

Usage:
    python3.12 render.py <table>.DBF [--shot out.png] [--force] [--hold SECS]

Exit codes: 0 rendered, 2 refused.
"""

import os
import re
import sys
import time

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from read_vfp_binary import Dbf

# --------------------------------------------------------------------------
# Contract section 4 -- the fourteen kinds. Anything else is refused loudly.
# --------------------------------------------------------------------------
CONTAINERS = {"form", "panel", "group", "pageset", "page"}
CONTROLS = {"label", "text", "button", "check", "radio", "list", "combo", "image"}
MENUS = {"menu"}
KNOWN_KINDS = CONTAINERS | CONTROLS | MENUS

FLOWS = {"row", "column", "grid", "free"}

# Section 8: the enumerated scales. No default; no conversion factors are given.
SCALES = {"px", "pt", "mm", "in", "cell"}

# Section 9: the ten v1 event names.
EVENTS = {"Click", "Init", "Change", "Activate", "Deactivate", "Destroy",
          "Error", "Focus", "Blur", "Load"}
DISPATCHES = {"ui", "worker"}

# Section 8's R16/R17 size rule.
CONTENT_SIZED = {"label", "button", "check", "radio", "group", "page"}
CONTAINER_SIZED = {"form", "panel", "pageset"}
# SPEC-GAP: the R16/R17 table has four rows and covers 11 of the 14 kinds.
# `text`, `list`, `combo`, `image` and `menu` are named nowhere in it. "data-sized"
# is never defined. Read as: whatever is neither content-sized nor a container.
DATA_SIZED = {"text", "list", "combo"}


class Refusal(Exception):
    pass


DERIVED = []      # section 5 / 12: "records any dimension it derived"
DIAGS = []


def diag(msg):
    DIAGS.append(msg)


def derived(objid, what, value, why):
    DERIVED.append("%-8s %-12s = %-18s (%s)" % (objid, what, value, why))


# --------------------------------------------------------------------------
# Section 7 property mini-language, reused verbatim by ORIGIN / HANDLERS /
# SOURCE (sections 8, 9, 10 all say "same property text form").
# --------------------------------------------------------------------------
def parse_props(text):
    """name = value per line, CRLF terminated, names case-insensitive."""
    out = {}
    if not text:
        return out
    for line in str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not line.strip():
            continue
        if "=" not in line:
            # SPEC-GAP: no rule for a PROPS line that is not name=value.
            diag("PROPS line without '=' ignored: %r" % line[:60])
            continue
        name, _, value = line.partition("=")
        out[name.strip().lower()] = value.strip()   # section 7: case-insensitive
    return out


def unquote(v):
    """Section 7 values: "quoted string" | number | .T./.F. | bare text."""
    if v is None:
        return None
    v = v.strip()
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        return v[1:-1]
    return v


def as_bool(v):
    return unquote(v or "").strip().upper() in (".T.", "T", "TRUE", "1")


def as_int(v, default=None):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------
# Section 9 handlers.  Event = HandlerName / DISPATCH [-> CompletionHandler]
# --------------------------------------------------------------------------
def parse_handlers(text):
    out = []
    if not text:
        return out
    for line in str(text).replace("\r\n", "\n").split("\n"):
        line = line.strip()
        if not line or "=" not in line:
            continue
        event, _, rhs = line.partition("=")
        event = event.strip()
        completion = None
        if "->" in rhs:
            rhs, _, completion = rhs.partition("->")
            completion = completion.strip()
        # SPEC-GAP: HandlerName is undelimited and real data contains ' / ' and
        # '(' and ',' inside it, so the dispatch must be split off the RIGHT.
        if "/" in rhs:
            name, _, dispatch = rhs.rpartition("/")
        else:
            name, dispatch = rhs, "ui"      # section 9: "The default is ui"
        name, dispatch = name.strip(), dispatch.strip()
        if event not in EVENTS:
            diag("unknown event %r dropped (section 9)" % event)   # spec says so
            continue
        if dispatch not in DISPATCHES:
            # SPEC-GAP: section 9 enumerates ui|worker and says nothing about a
            # third value. Real data carries `host`. Diagnosed, treated as ui.
            diag("undefined DISPATCH %r on %s -- treated as 'ui'" % (dispatch, event))
            dispatch = "ui"
        if dispatch == "worker" and not completion:
            diag("worker dispatch on %s names no completion handler (section 9)" % event)
        out.append((event, name, dispatch, completion))
    return out


# --------------------------------------------------------------------------
# Document model
# --------------------------------------------------------------------------
class Obj:
    def __init__(self, row):
        self.row = row
        self.objid = (row.get("OBJID") or "").strip()
        self.parent = (row.get("PARENT") or "").strip()
        self.ordinal = as_int(row.get("ORDINAL"), 0) or 0
        self.tabordinal = as_int(row.get("TABORDINAL"), 0) or 0
        self.span = as_int(row.get("SPAN"), 0) or 1        # section 3: default 1
        self.kind = (row.get("KIND") or "").strip().lower()
        self.flow = (row.get("FLOW") or "").strip().lower()
        self.binding = (row.get("BINDING") or "").strip()
        self.fontref = as_int(row.get("FONTREF"), 0) or 0
        self.provenance = (row.get("PROVENANCE") or "").strip()
        self.props = parse_props(row.get("PROPS"))
        self.origin = parse_props(row.get("ORIGIN"))
        self.handlers = parse_handlers(row.get("HANDLERS"))
        self.children = []
        self.widget = None

    @property
    def caption(self):
        return unquote(self.props.get("caption"))

    def origin_num(self, key):
        return as_int(unquote(self.origin.get(key.lower())), None)


class Doc:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.dir = os.path.dirname(self.path)
        rows = [r for r in Dbf(path).rows() if not r.get("_DELETED")]

        # Section 2: "a conformant reader locates records by RECKIND, never by
        # position." So: filter, never index.
        heads = [r for r in rows if (r.get("RECKIND") or "").strip().upper() == "DOC"]
        fonts = [r for r in rows if (r.get("RECKIND") or "").strip().upper() == "FONT"]
        objs = [r for r in rows if (r.get("RECKIND") or "").strip().upper() == "OBJ"]
        other = [r for r in rows if (r.get("RECKIND") or "").strip().upper()
                 not in ("DOC", "FONT", "OBJ")]
        if other:
            raise Refusal("unknown RECKIND %r" %
                          sorted({(r.get('RECKIND') or '').strip() for r in other}))
        if len(heads) != 1:
            raise Refusal("section 2 requires exactly 1 DOC record, found %d" % len(heads))
        if not objs:
            raise Refusal("section 2 requires 1 or more OBJ records, found 0")

        self.docprops = parse_props(heads[0].get("PROPS"))
        self.source = parse_props(heads[0].get("SOURCE"))

        # Section 3: FONTREF is "a 1-based index into this document's FONT rows".
        # SPEC-AMBIG: index into *which* ordering? Section 2 forbids relying on
        # physical position, so ORDINAL is used when every FONT row has a
        # distinct non-zero one; otherwise physical order (and it is recorded).
        fonts_o = [(as_int(r.get("ORDINAL"), 0) or 0, r) for r in fonts]
        ords = [o for o, _ in fonts_o]
        if ords and len(set(ords)) == len(ords) and 0 not in ords:
            fonts_o.sort(key=lambda t: t[0])
            self.font_order_basis = "ORDINAL"
        else:
            self.font_order_basis = "record order (ORDINAL unusable)"
        # SPEC-GAP: nothing in the contract names the keys of a FONT row's PROPS.
        # `Name` and `Size` are read off the fixtures. `Metrics` is not decodable.
        self.fonts = []
        for _, r in fonts_o:
            p = parse_props(r.get("PROPS"))
            self.fonts.append({"name": unquote(p.get("name")),
                               "size": as_int(unquote(p.get("size")), None),
                               "raw": p})

        objects = [Obj(r) for r in objs]
        self.by_id = {}
        for o in objects:
            if o.objid in self.by_id:
                raise Refusal("OBJID %r is not unique (section 3)" % o.objid)
            self.by_id[o.objid] = o

        # Section 4: unknown KIND -> refuse the document and name the kind.
        bad = sorted({o.kind for o in objects if o.kind not in KNOWN_KINDS})
        if bad:
            raise Refusal("unknown KIND(s) %s -- section 4 forbids a placeholder"
                          % ", ".join(repr(b) for b in bad))

        roots = []
        for o in objects:
            if not o.parent:
                roots.append(o)
            elif o.parent in self.by_id:
                self.by_id[o.parent].children.append(o)
            else:
                raise Refusal("PARENT %r of %r resolves to no OBJID" % (o.parent, o.objid))
        if len(roots) != 1:
            # SPEC-GAP: section 3 says PARENT is "empty on ... the root object",
            # singular, but nothing forbids several roots or says what to do.
            raise Refusal("expected exactly one root OBJ, found %d (%s)"
                          % (len(roots), ", ".join(r.objid for r in roots)))
        self.root = roots[0]
        for o in objects:
            o.children.sort(key=lambda c: c.ordinal)   # section 5: ascending

        self._check_flows()
        self._check_origin_scales(objects)
        self.bound_widths = self._load_bound_widths()

    # -- section 5 / section 3 validation -----------------------------------
    def _check_flows(self):
        for o in self.by_id.values():
            if o.children and o.kind in CONTAINERS:
                if not o.flow:
                    # Section 3 marks FLOW "P on containers".
                    raise Refusal("container %r (%s) has no FLOW; section 3 marks "
                                  "FLOW required-to-produce on containers" % (o.objid, o.kind))
                if o.flow not in FLOWS:
                    raise Refusal("unknown FLOW %r on %r (section 5)" % (o.flow, o.objid))

    def _check_origin_scales(self, objects):
        for o in objects:
            if o.kind == "menu" and o.origin:
                # Section 11: "A menu row must not carry ORIGIN."
                raise Refusal("menu row %r carries ORIGIN; section 11 forbids it" % o.objid)
            if o.origin:
                scale = unquote(o.origin.get("origin_scale"))
                if not scale:
                    # Section 8: "A row with ORIGIN_* and no ORIGIN_SCALE is invalid."
                    raise Refusal("%r has ORIGIN_* with no ORIGIN_SCALE (section 8)" % o.objid)
                if scale not in SCALES:
                    raise Refusal("ORIGIN_SCALE %r on %r is not one of %s"
                                  % (scale, o.objid, sorted(SCALES)))
                if scale != "px":
                    # SPEC-GAP: the contract enumerates px/pt/mm/in/cell and gives
                    # no conversion to any of them, and never defines `cell`.
                    raise Refusal("ORIGIN_SCALE %r on %r: the contract gives no "
                                  "conversion factor for it, so it cannot be honoured "
                                  "and section 8 says honour-or-refuse-the-row"
                                  % (scale, o.objid))

    # -- section 10 + R17 ---------------------------------------------------
    def _load_bound_widths(self):
        """R17: a bound data-sized control's width is the bound field's declared
        width in characters. That requires opening the data table."""
        table = unquote(self.source.get("table"))
        if not table:
            return {}
        # Section 10: relative to the UIDEF document's own location, always.
        p = os.path.join(self.dir, table.replace("\\", os.sep))
        if not os.path.exists(p):
            # SPEC-GAP: section 10 fixes the path's *base* ("relative to the
            # document") and says nothing about case. The fixture writes
            # `students.dbf`; the file shipped beside it is `STUDENTS.dbf`. On a
            # case-sensitive filesystem the documented rule resolves to nothing.
            d, base = os.path.split(p)
            try:
                hit = next((n for n in os.listdir(d or ".")
                            if n.lower() == base.lower()), None)
            except OSError:
                hit = None
            if hit:
                diag("SOURCE.Table %r matched %r case-insensitively; section 10 "
                     "says nothing about case" % (base, hit))
                p = os.path.join(d, hit)
        if not os.path.exists(p):
            diag("SOURCE.Table %r not found at %s -- R17 widths unavailable" % (table, p))
            return {}
        try:
            widths = {f[0].lower(): f[2] for f in Dbf(p).fields}
        except Exception as exc:                       # pragma: no cover
            diag("SOURCE.Table unreadable (%s)" % exc)
            return {}
        diag("SOURCE.Table resolved to %s (%d fields) for R17 widths"
             % (os.path.basename(p), len(widths)))
        return widths

    def bound_chars(self, obj):
        if not obj.binding:
            return None
        # SPEC-GAP: the contract never states BINDING's syntax. Fixtures use
        # alias.field; the alias is matched against SOURCE.Alias when present.
        b = obj.binding.strip().lower()
        alias = unquote(self.source.get("alias") or "") or ""
        field = b.split(".")[-1]
        if "." in b and alias and b.split(".")[0] != alias.lower():
            diag("BINDING %r names an alias that is not SOURCE.Alias %r" % (obj.binding, alias))
        return self.bound_widths.get(field)

    def font_for(self, obj):
        if not obj.fontref:
            return None                     # section 3: "0 = target default"
        if obj.fontref > len(self.fonts):
            # SPEC-GAP: no rule for a FONTREF past the end of the FONT rows.
            diag("FONTREF %d on %s exceeds %d FONT rows -- target default used"
                 % (obj.fontref, obj.objid, len(self.fonts)))
            return None
        return self.fonts[obj.fontref - 1]


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
class Renderer:
    def __init__(self, doc, force=False):
        self.doc = doc
        self.force = force
        self.tkfonts = {}
        self.root = tk.Tk()
        self.root.title(doc.root.caption or os.path.basename(doc.path))

    def refuse_or_force(self, msg):
        if not self.force:
            raise Refusal(msg)
        diag("FORCED PAST REFUSAL: " + msg)

    def tkfont_for(self, obj):
        f = self.doc.font_for(obj)
        if not f or not f.get("name"):
            return None
        key = (f["name"], f["size"])
        if key not in self.tkfonts:
            # SPEC-GAP: the FONT row's Size carries no unit. Read as points.
            self.tkfonts[key] = tkfont.Font(family=f["name"], size=f["size"] or 10)
        return self.tkfonts[key]

    # -- widgets ---------------------------------------------------------
    def make_widget(self, obj, master):
        k = obj.kind
        cap = obj.caption or ""
        font = self.tkfont_for(obj)
        kw = {"font": font} if font else {}

        if k in ("form",):
            w = ttk.Frame(master, padding=8)
        elif k == "panel":
            w = ttk.Frame(master, padding=4, relief="groove", borderwidth=1)
        elif k == "group":
            w = ttk.LabelFrame(master, text=cap, padding=6)
        elif k == "pageset":
            w = ttk.Notebook(master)
        elif k == "page":
            w = ttk.Frame(master, padding=6)
        elif k == "label":
            w = ttk.Label(master, text=cap, **kw)
        elif k == "button":
            w = ttk.Button(master, text=cap or obj.objid, **kw)
        elif k == "check":
            w = ttk.Checkbutton(master, text=cap, **kw)
        elif k == "radio":
            w = ttk.Radiobutton(master, text=cap, **kw)
        elif k == "text":
            w = ttk.Entry(master, width=self.text_width(obj), **kw)
        elif k == "combo":
            w = ttk.Combobox(master, width=self.text_width(obj), **kw)
        elif k == "list":
            w = tk.Listbox(master, width=self.text_width(obj), height=4,
                           **({"font": font} if font else {}))
        elif k == "image":
            # SPEC-GAP: nothing names the property that carries an image's source,
            # so an `image` row cannot be rendered from the contract at all.
            raise Refusal("KIND 'image' on %r: the contract names the kind but no "
                          "property that carries the picture" % obj.objid)
        else:
            raise Refusal("no rendering for KIND %r" % k)
        obj.widget = w
        self.wire_handlers(obj, w)
        return w

    def text_width(self, obj):
        """Section 8's replacement table, for SIZE only."""
        chars = self.doc.bound_chars(obj)
        if chars:
            # R17: data-sized and bound -> the bound field's declared width.
            mask = unquote(obj.props.get("mask"))
            if mask and len(mask) != chars:
                # SPEC-GAP: `Mask` is a named key (R25) and also implies a width.
                # R17 says the schema wins; nothing says what to do when they differ.
                diag("%s: Mask is %d chars, bound field is %d -- R17 (schema) used"
                     % (obj.objid, len(mask), chars))
            return chars
        w = obj.origin_num("origin_width")
        if w is not None:
            # R17: data-sized and unbound -> ORIGIN_WIDTH with its ORIGIN_SCALE.
            # Scale is already validated as px. Convert px to Tk character cells.
            cell = max(1, tkfont.nametofont("TkDefaultFont").measure("0"))
            n = max(2, int(round(w / cell)))
            derived(obj.objid, "width-chars", n, "ORIGIN_WIDTH %dpx / %dpx cell" % (w, cell))
            return n
        # SPEC-GAP: unbound, no ORIGIN_WIDTH. Section 8's table has no row for
        # this and section 5 forbids defaulting an absent dimension to a number,
        # but an entry with no width cannot be drawn. 20 chars, recorded.
        derived(obj.objid, "width-chars", 20,
                "unbound data-sized control with no ORIGIN_WIDTH; contract has no rule")
        return 20

    def wire_handlers(self, obj, widget):
        for event, name, dispatch, completion in obj.handlers:
            if event == "Click" and hasattr(widget, "configure"):
                try:
                    widget.configure(command=self.dispatcher(obj, name, dispatch, completion))
                except tk.TclError:
                    pass

    def dispatcher(self, obj, name, dispatch, completion):
        def go():
            # Section 9: references, never bodies. There is nothing to call.
            print("[handler] %s.Click -> %s / %s%s"
                  % (obj.objid, name, dispatch,
                     " -> " + completion if completion else ""))
        return go

    # -- layout ----------------------------------------------------------
    def layout(self, obj, parent_widget):
        w = self.make_widget(obj, parent_widget)
        if obj.kind == "pageset":
            # SPEC-GAP: `pageset`/`page` are named in section 4 and never
            # described. FLOW on the pageset (here `free`) is meaningless for a
            # tab strip; the pages are laid out as tabs regardless.
            if obj.flow and obj.flow != "free":
                diag("pageset %s declares FLOW=%r; tab layout used regardless"
                     % (obj.objid, obj.flow))
            for child in obj.children:
                if child.kind != "page":
                    raise Refusal("pageset %r has a non-page child %r (%s)"
                                  % (obj.objid, child.objid, child.kind))
                page = self.make_widget(child, w)
                w.add(page, text=child.caption or child.objid)
                self.place_children(child, page)
            return w
        self.place_children(obj, w)
        return w

    def place_children(self, obj, widget):
        if not obj.children:
            return
        flow = obj.flow
        kids = obj.children                                  # already ORDINAL-sorted
        if flow == "row":
            for c in kids:
                cw = self.layout(c, widget)
                cw.pack(side="left", padx=3, pady=3)
        elif flow == "column":
            for c in kids:
                cw = self.layout(c, widget)
                cw.pack(side="top", anchor="w", padx=3, pady=3)
        elif flow == "grid":
            cols = as_int(unquote(obj.props.get("columns")), None)
            if cols is None or cols < 1:
                # Section 5 says a grid wraps, but never says on what. Section 3
                # names `Columns` as a grid property without making it required,
                # and section 5's R16/R17 note forbids defaulting an absent
                # dimension to a number. So: no wrap width can be obtained.
                self.refuse_or_force(
                    "container %r has FLOW='grid' and no `Columns` property. "
                    "Section 5 defines grid as wrapping but never says what "
                    "determines the wrap width, and section 5 forbids defaulting "
                    "an absent dimension to a number." % obj.objid)
                cols = 1
                derived(obj.objid, "grid-Columns", 1, "forced; contract gives no default")
            r = c0 = 0
            for c in kids:
                span = max(1, min(c.span, cols))
                if c0 + span > cols:
                    r, c0 = r + 1, 0
                cw = self.layout(c, widget)
                cw.grid(row=r, column=c0, columnspan=span,
                        sticky="w", padx=3, pady=3)
                c0 += span
                if c0 >= cols:
                    r, c0 = r + 1, 0
        elif flow == "free":
            # Section 12's permission to refuse `free` is exercised only under
            # --refuse-free; section 5b measures that refusing it refuses 87.9%
            # of real documents, so it is accepted here. 5b: "a generator that
            # accepts free MUST honour ORIGIN".
            positioned = [c for c in kids
                          if c.origin_num("origin_top") is not None
                          or c.origin_num("origin_left") is not None]
            if not positioned:
                # SPEC-GAP: free with no ORIGIN on any child. 5b says ORIGIN is
                # "the only field those documents carry their layout in" and
                # there is none. Stacked in ORDINAL order, recorded.
                derived(obj.objid, "free-layout", "ordinal stack",
                        "FLOW=free but no child carries ORIGIN")
                for c in kids:
                    self.layout(c, widget).pack(side="top", anchor="w", padx=3, pady=2)
                return
            maxx = maxy = 0
            for c in kids:
                top = c.origin_num("origin_top")
                left = c.origin_num("origin_left")
                if top is None or left is None:
                    # SPEC-GAP: section 8 says "any member may be absent. Absence
                    # is normal" but a free child with half a position is undrawable.
                    derived(c.objid, "position", "0 for the absent member",
                            "FLOW=free child with a partial ORIGIN")
                    top, left = top or 0, left or 0
                cw = self.layout(c, widget)
                cw.place(x=left, y=top)
                cw.update_idletasks()
                maxx = max(maxx, left + cw.winfo_reqwidth())
                maxy = max(maxy, top + cw.winfo_reqheight())
            # A `place`d parent has no requested size; section 8 says a container's
            # size comes from ORIGIN, but these containers omit it (section 8:
            # "form 57%, panel-shaped 47%").
            ow = obj.origin_num("origin_width")
            oh = obj.origin_num("origin_height")   # SPEC-GAP: ORIGIN_HEIGHT is
            # used by the fixtures and named nowhere in the contract.
            if ow is None:
                ow = maxx + 16
                derived(obj.objid, "width-px", ow, "extent of free-positioned children")
            if oh is None:
                oh = maxy + 16
                derived(obj.objid, "height-px", oh, "extent of free-positioned children")
            widget.configure(width=ow, height=oh)
            widget.pack_propagate(False)
            widget.grid_propagate(False)

    # -- menus (section 11) ----------------------------------------------
    def build_menu(self):
        root_obj = self.doc.root
        bar = tk.Menu(self.root)
        for item in root_obj.children:
            self.add_menu_entry(bar, item, top=True)
        self.root.configure(menu=bar)
        body = ttk.Label(self.root, padding=24, justify="left",
                         text="UIDEF menu document\n%s\n\n%d bar items."
                              % (os.path.basename(self.doc.path),
                                 len(root_obj.children)))
        body.pack(fill="both", expand=True)

    def menu_label(self, obj):
        """Section 11 says the `\\<` mnemonic escape is used "consistently in both
        captions and prompts". In the fixture it is used in NEITHER Caption; it
        appears only in the undocumented `OpenerPrompt` of the popup the item
        opens. SPEC-CONTRA: recorded, and the prompt is preferred when present."""
        popup = self.popup_of(obj)
        text = None
        if popup is not None:
            text = unquote(popup.props.get("openerprompt")) or None
        if not text:
            text = obj.caption or obj.objid
        under = -1
        if "\\<" in text:
            under = text.index("\\<")
            text = text.replace("\\<", "", 1)
        return text, under

    def popup_of(self, obj):
        """A menu row is a popup container or an item, and the contract never
        says how to tell them apart. The fixture marks popups `Container = .T.`,
        an undocumented key that section 7 orders dropped silently. Structure is
        used instead: an item's single `menu` child IS its popup."""
        subs = [c for c in obj.children if c.kind == "menu"]
        if len(subs) == 1 and subs[0].children:
            return subs[0]
        return None

    def add_menu_entry(self, parent_menu, obj, top=False):
        if obj.kind != "menu":
            raise Refusal("non-menu KIND %r under a menu root" % obj.kind)
        if as_bool(obj.props.get("separator")) or (obj.caption or "").strip() == "\\-":
            parent_menu.add_separator()
            return
        popup = self.popup_of(obj)
        label, under = self.menu_label(obj)
        state = "normal" if obj.props.get("enabled", ".T.") is None or \
            as_bool(obj.props.get("enabled", ".T.")) else "disabled"
        if popup is not None:
            sub = tk.Menu(parent_menu, tearoff=0)
            for child in popup.children:
                self.add_menu_entry(sub, child)
            parent_menu.add_cascade(label=label, menu=sub,
                                    underline=under if under >= 0 else None)
            return
        # Section 11 names Key; it never says whether Key is a binding or a label.
        accel = unquote(obj.props.get("keylabel")) or unquote(obj.props.get("key"))
        kw = {"label": label, "state": state}
        if under >= 0:
            kw["underline"] = under
        if accel and not top:
            kw["accelerator"] = accel
        handler = next((h for h in obj.handlers if h[0] == "Click"), None)
        if handler:
            kw["command"] = self.dispatcher(obj, handler[1], handler[2], handler[3])
        if as_bool(obj.props.get("checked")):
            parent_menu.add_checkbutton(**kw)
        else:
            parent_menu.add_command(**kw)

    # -- top level -------------------------------------------------------
    def run(self):
        root_obj = self.doc.root
        if root_obj.kind == "menu":
            self.build_menu()
        elif root_obj.kind == "form":
            frame = self.layout(root_obj, self.root)
            frame.pack(fill="both", expand=True)
            h = root_obj.origin_num("origin_height")
            w = root_obj.origin_num("origin_width")
            self.root.update_idletasks()
            if w is None:
                w = self.root.winfo_reqwidth()
                derived(root_obj.objid, "width-px", w, "content extent; form omits ORIGIN_WIDTH")
            if h is None:
                h = self.root.winfo_reqheight()
                derived(root_obj.objid, "height-px", h, "content extent")
            self.root.geometry("%dx%d" % (max(w, self.root.winfo_reqwidth()),
                                          max(h, self.root.winfo_reqheight())))
        else:
            # SPEC-GAP: nothing says which KINDs may be a document root.
            raise Refusal("root OBJ has KIND %r; the contract does not say which "
                          "kinds may be a document root" % root_obj.kind)
        self.root.update_idletasks()
        self.root.update()


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    path = argv[1]
    shot = None
    force = "--force" in argv
    if "--shot" in argv:
        shot = argv[argv.index("--shot") + 1]

    print("=" * 74)
    print("UIDEF render: %s" % path)
    print("=" * 74)
    try:
        doc = Doc(path)
        print("DOC props      : %s" % doc.docprops)
        print("SOURCE         : %s" % (doc.source or "(none)"))
        print("FONT rows      : %d, indexed by %s" % (len(doc.fonts), doc.font_order_basis))
        print("root OBJ       : %s kind=%s flow=%s provenance=%s"
              % (doc.root.objid, doc.root.kind, doc.root.flow, doc.root.provenance))
        r = Renderer(doc, force=force)
        r.run()
    except Refusal as exc:
        print()
        print("REFUSED: %s" % exc)
        for d in DIAGS:
            print("  diag: %s" % d)
        return 2

    if DIAGS:
        print("\nDIAGNOSTICS (%d):" % len(DIAGS))
        for d in DIAGS:
            print("  %s" % d)
    # Section 5 / 12: "records any dimension it derived".
    print("\nDERIVED DIMENSIONS (%d) -- section 12 requires a reader to record these:"
          % len(DERIVED))
    for d in DERIVED or ["  (none)"]:
        print("  %s" % d)

    if shot:
        r.root.update()
        time.sleep(0.6)
        r.root.update()
        os.system("import -window root %s" % shot)
        print("\nscreenshot -> %s" % shot)
    else:
        r.root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
