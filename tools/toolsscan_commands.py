# /tools/scan_commands.py
# Run locally to reproduce the tables and files
import os, re, zipfile
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

ROOT_ZIP = "ccode_homegrown_20251119-112734.zip"
EXTRACT_DIR = Path("repo_extract")

if not EXTRACT_DIR.exists():
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ROOT_ZIP, 'r') as z:
        z.extractall(EXTRACT_DIR)

TEXT_EXTS = {".py",".js",".ts",".tsx",".java",".c",".cpp",".cc",".cs",".rb",".go",".rs",".m",".mm",".swift",
             ".kt",".kts",".php",".pl",".r",".lua",".hs",".scala",".sql",".md",".txt",".yaml",".yml",".json"}

files: List[Path] = [p for p in EXTRACT_DIR.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXTS]

FOXPRO_SET = {
    "SCAN","ENDSCAN","FOR","ENDFOR","IF","ELSE","ENDIF","CASE","ENDCASE","DO","WITH","ENDWITH","REPLACE",
    "SELECT","INSERT","UPDATE","DELETE","LOCATE","SEEK","INDEX","INDEX ON","APPEND","BROWSE","USE","CLOSE",
    "SET","SUM","AVERAGE","COUNT","GROUP BY","ORDER BY","WHERE","UNION","JOIN","SUBSTR","LEFT","RIGHT",
    "TRANSFORM","TYPE","IIF","INLIST","BETWEEN","NVL","VAL","STR","DTOC","CTOD","DATE","DATETIME","SQLEXEC"
}

UPPER_COMMAND_KEY = re.compile(r'["\']([A-Z][A-Z0-9_ ]{1,40})["\']\s*:\s*([A-Za-z_][A-Za-z0-9_\.]*)')
ELIF_TOKEN_EQ   = re.compile(r'(?:elif|if)\s+[^#\n]*?([A-Za-z_][A-Za-z0-9_\.]*)\s*==\s*["\']([A-Z][A-Z0-9_ ]+)["\']')
CASE_STRING     = re.compile(r'case\s+["\']([A-Z][A-Z0-9_ ]+)["\']', re.IGNORECASE)
DECORATOR_CMD   = re.compile(r'@(?:command|foxpro_?command|cmd|register_?command)\b')
DEF_LINE        = re.compile(r'^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*:', re.MULTILINE)

def summarize_docstring(text: str, start_idx: int) -> str:
    fwd = text[start_idx:start_idx+2000]
    m = re.search(r'("""|\'\'\')(.{0,500}?)(\1)', fwd, flags=re.DOTALL)
    if m: return re.sub(r'\s+', ' ', m.group(2)).strip()[:300]
    back = text[max(0, start_idx-800):start_idx]
    comments = "\n".join([ln.strip() for ln in back.splitlines() if ln.strip().startswith("#")])
    comments = re.sub(r'#\s*', '', comments)
    return re.sub(r'\s+', ' ', comments).strip()[:300]

def find_nearby_terms(text: str, idx: int, terms, window=1000):
    lo, hi = max(0, idx-window), min(len(text), idx+window)
    region = text[lo:hi]
    hits = [t for t in terms if re.search(rf'\b{re.escape(t)}\b', region, flags=re.IGNORECASE)]
    return ", ".join(sorted(set(hits)))

def extract_snippet(text: str, idx: int, radius=240) -> str:
    lo, hi = max(0, idx-radius), min(len(text), idx+radius)
    return text[lo:hi].replace("\t", "    ")

def classify_flavor(cmd_name: str, file_path: Path, text: str, idx: int) -> str:
    u = cmd_name.upper().strip()
    if u in FOXPRO_SET: return "foxpro"
    if any(token in u for token in FOXPRO_SET): return "foxpro"
    region = text[max(0, idx-800):min(len(text), idx+800)]
    if re.search(r'homegrown', region, flags=re.IGNORECASE) or 'homegrown' in str(file_path).lower(): return "homegrown"
    if re.match(r'^(HG|HOMEGROWN|X_)[\W_]*', u): return "homegrown"
    return "unknown"

rows: List[Dict[str, Any]] = []
for fp in files:
    try:
        text = fp.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    for m in DECORATOR_CMD.finditer(text):
        after = text[m.end(): m.end()+1200]
        mdef = DEF_LINE.search(after)
        if not mdef: continue
        func_name = mdef.group(1)
        back = text[m.start(): m.end()+200]
        mcmd = re.search(r'@(?:command|foxpro_?command|cmd|register_?command)\s*\(\s*["\']([^"\']+)["\']', back)
        cmd = (mcmd.group(1) if mcmd else func_name).strip()
        start = m.start()
        rows.append({
            "command": cmd,
            "flavor": classify_flavor(cmd, fp, text, start),
            "source_type": "decorator",
            "file": str(fp.relative_to(EXTRACT_DIR)),
            "line": text.count("\n", 0, start) + 1,
            "definition": f"{func_name}({mdef.group(2)})",
            "doc_or_comment": summarize_docstring(text, start),
            "nearby_tags": find_nearby_terms(text, start, ["helper","helpers","example","examples"]),
            "snippet": extract_snippet(text, start)
        })

    for m in UPPER_COMMAND_KEY.finditer(text):
        cmd, handler, start = m.group(1).strip(), m.group(2).strip(), m.start()
        rows.append({
            "command": cmd,
            "flavor": classify_flavor(cmd, fp, text, start),
            "source_type": "mapping",
            "file": str(fp.relative_to(EXTRACT_DIR)),
            "line": text.count("\n", 0, start) + 1,
            "definition": handler,
            "doc_or_comment": summarize_docstring(text, start),
            "nearby_tags": find_nearby_terms(text, start, ["helper","helpers","example","examples"]),
            "snippet": extract_snippet(text, start)
        })

    for m in ELIF_TOKEN_EQ.finditer(text):
        left, cmd, start = m.group(1), m.group(2).strip(), m.start()
        rows.append({
            "command": cmd,
            "flavor": classify_flavor(cmd, fp, text, start),
            "source_type": "condition",
            "file": str(fp.relative_to(EXTRACT_DIR)),
            "line": text.count("\n", 0, start) + 1,
            "definition": left,
            "doc_or_comment": summarize_docstring(text, start),
            "nearby_tags": find_nearby_terms(text, start, ["helper","helpers","example","examples"]),
            "snippet": extract_snippet(text, start)
        })

    for m in CASE_STRING.finditer(text):
        cmd, start = m.group(1).strip(), m.start()
        rows.append({
            "command": cmd,
            "flavor": classify_flavor(cmd, fp, text, start),
            "source_type": "case",
            "file": str(fp.relative_to(EXTRACT_DIR)),
            "line": text.count("\n", 0, start) + 1,
            "definition": "case",
            "doc_or_comment": summarize_docstring(text, start),
            "nearby_tags": find_nearby_terms(text, start, ["helper","helpers","example","examples"]),
            "snippet": extract_snippet(text, start)
        })

df = pd.DataFrame(rows).sort_values(["command","file","line","source_type"]) if rows else pd.DataFrame(
    columns=["command","flavor","source_type","file","line","definition","doc_or_comment","nearby_tags","snippet"]
)
df = df.drop_duplicates(subset=["command","file","line","source_type"], keep="first")
df.to_csv("implemented_commands_catalog.csv", index=False)
df.to_json("implemented_commands_catalog.json", orient="records", indent=2)

summary_rows = []
for cmd, grp in df.groupby("command"):
    flavors = ", ".join(sorted(set(grp["flavor"])))
    files_list = ", ".join(sorted(set(grp["file"])))
    src_types = ", ".join(sorted(set(grp["source_type"])))
    near = ", ".join(sorted(set([t for t in (",".join(grp["nearby_tags"]).split(",")) if t.strip()])))
    summary_rows.append({
        "command": cmd,
        "flavors_detected": flavors,
        "source_types": src_types,
        "files": files_list,
        "helpers_or_examples_nearby": near
    })
summary_df = pd.DataFrame(summary_rows).sort_values("command")
summary_df.to_csv("implemented_commands_summary.csv", index=False)
print("Detailed rows:", len(df), "Unique commands:", len(summary_df))
