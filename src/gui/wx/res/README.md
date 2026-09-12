# `src/gui/wx/res` -- the application icon

The x64base mark, as the windowed GUI's icon. Added by AIF-120 R91.

## What is here

| file | what it is |
| --- | --- |
| `x64base.ico` | GENERATED. Seven sizes -- 16, 24, 32, 48, 64, 128, 256 |
| `x64base_16.xpm` | GENERATED. ASCII, compiled in on non-MSW targets |
| `x64base_32.xpm` | GENERATED |
| `x64base_48.xpm` | GENERATED |
| `x64base.rc` | MSW resource script; names the `.ico` as `x64base_icon` |
| `app_icon.hpp` | `app_icon_bundle()` -- the accessor both platforms call |
| `make_icons.py` | the recipe that produces the four generated files |

**Nothing here is loaded from disk at run time.** On MSW the icon is a linked
resource; everywhere else it is compiled in as XPM. An icon read from a file is
an icon that can go missing, and a missing icon fails silently -- the window
gets the toolkit default and nobody learns the product shipped without its face
on.

## Provenance

The source is **image 5 of the 2026-07-12 identity intake**:

    dottalkpp/docs/media/x64base_identity_2026_07_12/05-x64-smiling-database-site-icon.jpg
    784x1168, 154,237 bytes
    sha256 b6247e565d1c3d01e32127385162ca5ebdc3c56234cfc73e15981b7ed6ed46e5

That intake records it as *"the project-owner-selected site icon ... the
database-shaped mark whose internal lines read as a smiling face"*, and it
requires that derivatives retain a pointer back to it. This file is that
pointer. **The intake itself is preserved byte-for-byte and is not edited by
anything here.**

The intake also said the website *"may publish a byte-identical copy under a
public asset name"*, and it did:

    D:\dev\x64base-site\public\images\brand\x64base-smiling-database-site-icon.jpg

Both copies md5 to `2583240a08db7ea29ddc1842b66bf030`. So the mark this
directory derives from and the mark x64base.com serves are the same bytes, and
"the x64base.com smiling database" resolves to one file rather than two that
might drift.

Two things the intake says that this directory does not overrule:

- the set *"remains subject to later brand, trademark, accessibility, and design
  review"*
- the intake *"records file identity and requested use; it does not manufacture
  an independent copyright, trademark, or runtime claim"*

**Using the site icon as a RUNTIME icon is a new use** beyond what that intake
recorded, authorized in-session by the steward. It is written down here rather
than left implicit, because the intake explicitly declined to make a runtime
claim on its own.

### The site has no square version either

Worth writing down, because it is the reason this directory had to derive one
rather than reuse one. Searched across `x64base-site`, `x64base-lean-site` and
`dottalk-webui`: **no square icon asset exists anywhere in the estate.** The
only other candidate, `x64base-site/public/favicon.svg`, is the older `64`
monospace tile and is dead -- the site's `app/layout.tsx` overrides it.

What that file declares is the finding:

    icons: {
      icon:     [{ url: ".../x64base-smiling-database-site-icon.jpg",
                   type: "image/jpeg" }],
      shortcut: [".../x64base-smiling-database-site-icon.jpg"],
      apple:    [".../x64base-smiling-database-site-icon.jpg"]
    }

x64base.com serves the **raw 784x1168 portrait JPEG** as its favicon, its
shortcut icon and its apple-touch icon. All three of those want a square image;
a browser given a 2:3 portrait will letterbox or squash it, `apple-touch-icon`
is specified square, and it is 154 KB fetched for a 16 px slot.

**Reported, not fixed** -- this lane does no web work. But the four files
generated here are exactly what that declaration wants, and `x64base.ico` in
particular is what a `/favicon.ico` should be. If the site wants them it can
take them; the recipe is in this directory and runs from anywhere.

## The derivation, and why it needs one

The intake image is a **784x1168 portrait canvas** carrying a square icon tile.
An application icon must be square, so the tile has to be cropped out -- which
is a decision, and a decision that is worth measuring rather than eyeballing.

The tile sits a few luminance levels above the field behind it. Blurring away
the canvas texture (Gaussian, sigma 5) and comparing a column band inside the
tile against the left and right margins at the same row isolates it at

    x 102..682     (581 wide)
    y 281..878     (598 tall)

The vertical extent runs 17 px longer because the tile casts a drop shadow
downward. Cropping to the shadow would push the tile off centre, so the box is
squared on the tile and centred on it:

    CROP = (100, 288, 684, 872)     584 x 584

`make_icons.py` carries that box and reproduces all four generated files
byte-for-byte. Verified 2026-08-20: regenerating from the intake into a clean
directory gives four identical md5s.

## The `.ico` layout, and why it is spliced

The file carries **DIB frames below 256 and a PNG frame at 256**. That is the
conventional layout, and it is what every icon editor and every older shell path
expects. All-PNG is legal on Vista and later and is what a single Pillow save
produces, but a file that only works on the newer path is a file that fails
somewhere nobody is testing.

Pillow writes one encoding per call, so `make_icons.py` writes both and splices
the directory. Verified 2026-08-20 by DECODING rather than by arithmetic -- all
seven frames come back at their declared size, and the mark occupies 27.7%,
25.6% and 25.3% of the 16, 32 and 256 frames, so the artwork survives every
downscale rather than turning into a dark square.

That check is worth keeping. A first pass at predicting the frame sizes from
width, height and depth was wrong by a factor of five, and had the file actually
been malformed the arithmetic would have said so for the wrong reason. Decoding
the frames answers the question the arithmetic was only guessing at.

`x64base.rc` compiles: `llvm-windres -i x64base.rc -O coff` produces a COFF
object with `.rsrc$01` and `.rsrc$02` sections carrying the icon, and it does so
**from a different working directory** -- the resource compiler resolves
`x64base.ico` against the directory of the `.rc`, not against the cwd, which is
what a CMake build out of tree needs. That is as far as this can be verified off
Windows -- see "What is NOT proven" below.

## Regenerating

On the host, through the repo venv:

```powershell
$py12 = "D:\code\ccode\.venv312\Scripts\python.exe"
& $py12 src\gui\wx\res\make_icons.py
```

In the Linux sandbox, `python3 src/gui/wx/res/make_icons.py`.

Requires Pillow. Rerun it if the intake image is ever replaced, and commit the
regenerated files with the change rather than editing them by hand -- they are
output, and hand-edited output drifts from the recipe that claims to produce it.

**It is deterministic.** Verified 2026-08-20: run in the Linux container
(Pillow 12.2.0) and on the host-side working tree (Pillow 12.3.0), the four
generated files come out with identical md5s.

    7e3e37c993e084cd574073f9be6431c4  x64base.ico
    9fe5f92f5c04d86f61f8b48cdd1cddd9  x64base_16.xpm
    b9bf163250f7a69fd4d4b8a3dd60ecf2  x64base_32.xpm
    25cf6c5694b028d73725c855c7247b37  x64base_48.xpm

The recipe holds both encodings in memory rather than writing temporary files.
That is not tidiness: a mounted working tree refuses `unlink`, so a `finally`
block that removes a temp file is a recipe that cannot run where this repository
is routinely read from.

## What is NOT proven

**The MSW path has never been run.** The resource script compiles and the `.ico`
decodes, but `wxIconBundle("x64base_icon", nullptr)` has not been executed on
Windows by this lane. What HAS been run, under Xvfb with wxWidgets 3.2.4:

    bundle icons: 3
      [0] 16x16 ok=1
      [1] 32x32 ok=1
      [2] 48x48 ok=1
    frame icon after SetIcons: 32x32 ok=1

That is the XPM path -- the one every non-MSW target takes -- proven end to end
from `app_icon_bundle()` through `wxTopLevelWindow::SetIcons()`.

## What was NOT done

The tile's rounded corners sit on the intake's own dark navy, and that navy is
kept: the icon is opaque and square, exactly as the artwork was supplied. Giving
it a transparent rounded-rect alpha would look better on a light taskbar, but it
means inventing a corner radius the source does not state, and that is a brand
decision rather than a build one. It belongs to the design review the intake
already says this set is subject to.
