import csv
import io
import json
import logging
import re
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from resume_checker.resume_checker import analyze_file, iter_resumes
from resume_checker.skills_db import ALL_SKILLS, SKILL_GROUPS, suggest

log = logging.getLogger("resumelens")

BASE = Path(__file__).parent / "frontend"

# ---------- limits ----------
MAX_UPLOAD_BYTES = 25 * 1024 * 1024     # per uploaded file (a ZIP counts as one file)
MAX_RESUMES = 100                       # resumes per request (after unzipping)
MAX_SKILLS = 150
MAX_SKILL_LEN = 60

app = FastAPI(title="ResumeLens")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    # Always answer with JSON so the frontend can show a real message.
    log.exception("Unhandled error on %s", request.url.path)
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


# ---------- helpers ----------
def parse_skills(raw: str) -> list[str]:
    seen, out = set(), []
    for s in re.split(r"[,\n;]", raw):
        s = s.strip()[:MAX_SKILL_LEN]
        if s and s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    if not out:
        raise HTTPException(400, "Add at least one skill")
    if len(out) > MAX_SKILLS:
        raise HTTPException(400, f"Too many skills (max {MAX_SKILLS})")
    return out


def safe_name(name: str | None) -> str:
    name = Path((name or "resume").replace("\\", "/")).name
    return name or "resume"


def load_resumes(files: list[UploadFile]) -> list[tuple[str, bytes | None, str | None]]:
    """Read uploads (expanding ZIPs). Returns [(name, data, error)]; never raises for one bad file."""
    items = []
    for f in files:
        name = safe_name(f.filename)
        raw = f.file.read(MAX_UPLOAD_BYTES + 1)
        if len(raw) > MAX_UPLOAD_BYTES:
            items.append((name, None, f"File is larger than {MAX_UPLOAD_BYTES // 1024 // 1024} MB"))
            continue
        try:
            for n, data, err in iter_resumes(name, raw):
                items.append((n, data, err))
        except ValueError as e:
            items.append((name, None, str(e)))
        if len(items) > MAX_RESUMES:
            raise HTTPException(413, f"Too many resumes in one request (max {MAX_RESUMES})")
    if not items:
        raise HTTPException(400, "No PDF or DOCX resumes found in the upload")
    return items


def csv_safe(v):
    """Stop spreadsheet apps from running a cell as a formula."""
    v = "" if v is None else str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


def file_part(name: str) -> str:
    return re.sub(r"[^\w.\- ]", "_", safe_name(name))[:80]


# ---------- pages ----------
@app.get("/")
def home():
    return FileResponse(BASE / "index.html")


@app.get("/check-resume")
def check_page():
    return FileResponse(BASE / "check-resume.html")


@app.get("/about")
def about_page():
    return FileResponse(BASE / "about.html")


@app.get("/health")
def health():
    return {"ok": True}


# ---------- skill search ----------
@app.get("/api/suggest")
def api_suggest(q: str = ""):
    skills, groups = suggest(q[:80])
    return {"skills": skills, "groups": groups}


@app.get("/api/groups")
def api_groups():
    return {"total": len(ALL_SKILLS), "groups": SKILL_GROUPS}


# ---------- analysis ----------
# Plain `def` (not async): FastAPI runs these in a thread pool, so slow PDF
# parsing does not freeze the whole server.
@app.post("/api/analyze")
def api_analyze(files: list[UploadFile] = File(...), skills: str = Form(...)):
    wanted = parse_skills(skills)
    results = []
    for name, data, err in load_resumes(files):
        if err:
            results.append({"filename": name, "error": err})
        else:
            results.append(analyze_file(name, data, wanted))
    results.sort(key=lambda r: r.get("match_percent", -1), reverse=True)
    return {"results": results}


# ---------- shortlist zip: original resumes whose names the client says passed ----------
@app.post("/api/shortlist")
def api_shortlist(files: list[UploadFile] = File(...), names: str = Form(...)):
    try:
        wanted = {str(n) for n in json.loads(names)}
    except (ValueError, TypeError):
        raise HTTPException(400, "Invalid list of names")
    if not wanted:
        raise HTTPException(400, "No resumes selected")
    buf, used, count = io.BytesIO(), set(), 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data, err in load_resumes(files):
            if err or data is None or name not in wanted:
                continue
            arc, n = name, 1
            while arc in used:                       # same file name twice
                n += 1
                arc = f"{n}_{name}"
            used.add(arc)
            z.writestr(arc, data)
            count += 1
    if not count:
        raise HTTPException(404, "None of the selected resumes were found in the upload")
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=shortlisted_resumes.zip"})


# ---------- zip report ----------
class ReportIn(BaseModel):
    results: list[dict] = Field(default_factory=list, max_length=500)


def _skills(r: dict, key: str) -> list[str]:
    return [str(m.get("skill", "")) for m in r.get(key, []) if isinstance(m, dict)]


@app.post("/api/report-zip")
def api_report_zip(payload: ReportIn):
    results = payload.results
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("report.json", json.dumps(results, indent=2))

        rows = io.StringIO()
        w = csv.writer(rows)
        w.writerow(["resume", "match_percent", "verdict", "matched", "missing"])
        for r in results:
            w.writerow([csv_safe(r.get("filename", "")), r.get("match_percent", ""),
                        csv_safe(r.get("verdict", r.get("error", ""))),
                        csv_safe("; ".join(_skills(r, "matched"))),
                        csv_safe("; ".join(_skills(r, "missing")))])
        z.writestr("summary.csv", rows.getvalue())

        for i, r in enumerate(results, 1):
            fname = str(r.get("filename", "resume"))
            lines = [f"Resume: {fname}"]
            if "error" in r:
                lines.append(f"Error: {r['error']}")
            else:
                lines += [f"Match: {r.get('match_percent', 0)}% ({r.get('verdict', '')})", "",
                          "Matched: " + ", ".join(_skills(r, "matched")),
                          "Missing: " + ", ".join(_skills(r, "missing")), "", "Suggestions:"]
                lines += [f"- {t}" for t in r.get("suggestions", [])]
            z.writestr(f"reports/{i:02d}_{file_part(fname)}.txt", "\n".join(lines))
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=resumelens_report.zip"})


app.mount("/css", StaticFiles(directory=BASE / "css"), name="css")
app.mount("/js", StaticFiles(directory=BASE / "js"), name="js")
