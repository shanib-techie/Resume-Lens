import csv
import io
import json
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from resume_checker.resume_checker import analyze_file, iter_resumes
from resume_checker.skills_db import ALL_SKILLS, SKILL_GROUPS, suggest

BASE = Path(__file__).parent / "frontend"
app = FastAPI(title="ResumeLens")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


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


# ---------- skill search ----------
@app.get("/api/suggest")
def api_suggest(q: str = ""):
    skills, groups = suggest(q)
    return {"skills": skills, "groups": groups}

@app.get("/api/groups")
def api_groups():
    return {"total": len(ALL_SKILLS), "groups": SKILL_GROUPS}


# ---------- analysis ----------
@app.post("/api/analyze")
async def api_analyze(files: list[UploadFile] = File(...), skills: str = Form(...)):
    wanted = [s.strip() for s in skills.replace("\n", ",").split(",") if s.strip()]
    if not wanted:
        raise HTTPException(400, "Add at least one skill")
    results = []
    for f in files:
        for name, data in iter_resumes(f.filename, await f.read()):
            results.append(analyze_file(name, data, wanted))
    results.sort(key=lambda r: r.get("match_percent", -1), reverse=True)
    return {"results": results}


# ---------- shortlist zip: only original resumes at or above the threshold ----------
@app.post("/api/shortlist")
async def api_shortlist(files: list[UploadFile] = File(...), skills: str = Form(...),
                        threshold: float = Form(70)):
    wanted = [s.strip() for s in skills.replace("\n", ",").split(",") if s.strip()]
    if not wanted:
        raise HTTPException(400, "Add at least one skill")
    buf, used, count = io.BytesIO(), set(), 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            for name, data in iter_resumes(f.filename, await f.read()):
                r = analyze_file(name, data, wanted)
                if "error" in r or r["match_percent"] < threshold:
                    continue
                arc, n = name, 1
                while arc in used:                       # same file name twice
                    n += 1
                    arc = f"{n}_{name}"
                used.add(arc)
                z.writestr(arc, data)
                count += 1
    if not count:
        raise HTTPException(404, f"No resume reached {threshold:g}%")
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=shortlisted_resumes.zip"})


# ---------- zip report ----------
@app.post("/api/report-zip")
async def api_report_zip(payload: dict):
    results = payload.get("results", [])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("report.json", json.dumps(results, indent=2))
        rows = io.StringIO()
        w = csv.writer(rows)
        w.writerow(["resume", "match_percent", "verdict", "matched", "missing"])
        for r in results:
            w.writerow([r["filename"], r.get("match_percent", ""), r.get("verdict", r.get("error", "")),
                        "; ".join(m["skill"] for m in r.get("matched", [])),
                        "; ".join(m["skill"] for m in r.get("missing", []))])
        z.writestr("summary.csv", rows.getvalue())
        for i, r in enumerate(results, 1):
            lines = [f"Resume: {r['filename']}"]
            if "error" in r:
                lines.append(f"Error: {r['error']}")
            else:
                lines += [f"Match: {r['match_percent']}% ({r['verdict']})", "",
                          "Matched: " + ", ".join(m["skill"] for m in r["matched"]),
                          "Missing: " + ", ".join(m["skill"] for m in r["missing"]), "", "Suggestions:"]
                lines += [f"- {t}" for t in r["suggestions"]]
            z.writestr(f"reports/{i:02d}_{r['filename']}.txt", "\n".join(lines))
    return Response(buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=resumelens_report.zip"})


app.mount("/css", StaticFiles(directory=BASE / "css"), name="css")
app.mount("/js", StaticFiles(directory=BASE / "js"), name="js")
