"""
app.py -- Flask front-end for the MP schema gap scanner.

Run locally:
    python app.py
    # then visit http://localhost:5000

The web UI accepts a Monterey Phoenix schema (.mp) plus an optional
Gryphon trace file (.gry), runs the symbolic gap detectors (Shapes
A / B / C), and renders the candidate findings with trace evidence
inline. Bundled examples can be loaded with one click.
"""
from __future__ import annotations
import os
import tempfile
import traceback

from flask import Flask, request, jsonify, render_template, send_from_directory

from scanner import scan

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.join(HERE, "examples")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1 GB upload cap


# Examples discovery ---------------------------------------------------

def _list_examples():
    """Pair every example .mp with .gry files for the same model."""
    if not os.path.isdir(EXAMPLES_DIR):
        return []
    files = os.listdir(EXAMPLES_DIR)
    schemas = sorted(f for f in files if f.endswith(".mp"))
    out = []
    for s in schemas:
        stem = s[:-3]
        gry = sorted(
            f for f in files
            if f.endswith(".gry") and f.startswith(stem.split("_")[0])
        )
        out.append({
            "schema": s,
            "schema_path": os.path.join(EXAMPLES_DIR, s),
            "traces": [
                {"name": g, "path": os.path.join(EXAMPLES_DIR, g)}
                for g in gry
            ],
        })
    return out


# Candidate -> JSON ----------------------------------------------------

def _candidate_to_json(c: dict) -> dict:
    out = {
        "shape": c["shape"],
        "rationale": c["rationale"],
        "suggested_reject": c["suggested_reject"],
    }
    if "analogy" in c:
        out["analogy"] = c["analogy"]
    ev = c.get("evidence")
    if ev is not None:
        out["evidence"] = {
            "violation_count": ev["violation_count"],
            "trace_count": ev["trace_count"],
            "violation_rate": ev["violation_rate"],
            "sample": ev["sample"],
        }
    return out


def _result_payload(schema_path, gry_path, schema, cands):
    return {
        "schema": {
            "path": os.path.basename(schema_path),
            "root_count": len(schema.roots),
            "state_count": len(schema.state_root),
            "ordering_count": len(schema.orderings),
            "reject_count": len(schema.rejects),
        },
        "traces": (
            {"path": os.path.basename(gry_path)} if gry_path else None
        ),
        "candidates": {
            shape: [_candidate_to_json(c) for c in cands[shape]]
            for shape in ("A", "B", "C")
        },
        "totals": {
            "A": len(cands["A"]),
            "B": len(cands["B"]),
            "C": len(cands["C"]),
            "all": sum(len(cands[s]) for s in ("A", "B", "C")),
        },
    }


# Routes ---------------------------------------------------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        examples=_list_examples(),
    )


@app.route("/api/scan", methods=["POST"])
def api_scan():
    schema_path = None
    gry_path = None
    tmpfiles = []
    try:
        # Schema: either uploaded file or example name.
        if "schema_file" in request.files and request.files["schema_file"].filename:
            f = request.files["schema_file"]
            fd, schema_path = tempfile.mkstemp(suffix=".mp")
            os.close(fd)
            f.save(schema_path)
            tmpfiles.append(schema_path)
        elif request.form.get("example_schema"):
            name = os.path.basename(request.form["example_schema"])
            cand = os.path.join(EXAMPLES_DIR, name)
            if not os.path.isfile(cand):
                return jsonify({"error": f"example schema not found: {name}"}), 400
            schema_path = cand
        else:
            return jsonify({"error": "no schema provided"}), 400

        # Traces (optional): uploaded or example.
        if "traces_file" in request.files and request.files["traces_file"].filename:
            f = request.files["traces_file"]
            fd, gry_path = tempfile.mkstemp(suffix=".gry")
            os.close(fd)
            f.save(gry_path)
            tmpfiles.append(gry_path)
        elif request.form.get("example_traces"):
            name = os.path.basename(request.form["example_traces"])
            cand = os.path.join(EXAMPLES_DIR, name)
            if os.path.isfile(cand):
                gry_path = cand

        schema, cands = scan(schema_path, gry_path)
        # Sort Shape B with cross-ROOT shared-token first (matches CLI).
        cands["B"].sort(
            key=lambda c: (c.get("analogy") != "shared-token analog",
                           c.get("candidate_state", "")),
        )

        return jsonify(_result_payload(
            request.form.get("example_schema") or
            (request.files["schema_file"].filename
             if "schema_file" in request.files else "uploaded.mp"),
            gry_path,
            schema, cands,
        ))
    except Exception as e:
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500
    finally:
        for p in tmpfiles:
            try:
                os.remove(p)
            except OSError:
                pass


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(HERE, "static"), filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
