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
import sys
import tempfile
import traceback

from flask import Flask, request, jsonify, render_template, send_from_directory

from scanner import scan


# Path resolution: behave correctly whether running as a script
# (python app.py) or as a frozen PyInstaller --onefile bundle.
#   - In frozen mode, templates/static/examples that we bundled live
#     under sys._MEIPASS (the temp extraction dir).
#   - We *also* look for an examples/ folder alongside the .exe so end
#     users can drop their own .mp/.gry files there without rebuilding.
def _resource_root() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def _example_search_dirs() -> list[str]:
    if getattr(sys, "frozen", False):
        beside_exe = os.path.join(
            os.path.dirname(sys.executable), "examples"
        )
        bundled = os.path.join(sys._MEIPASS, "examples")  # type: ignore[attr-defined]
        return [d for d in (beside_exe, bundled) if os.path.isdir(d)]
    return [os.path.join(_resource_root(), "examples")]


HERE = _resource_root()

app = Flask(
    __name__,
    template_folder=os.path.join(HERE, "templates"),
    static_folder=os.path.join(HERE, "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1 GB upload cap


# Examples discovery ---------------------------------------------------

def _list_examples():
    """Pair every example .mp with .gry files for the same model.

    Walks every directory returned by _example_search_dirs(). Earlier
    dirs win on name collisions, so a user .mp in beside-exe examples/
    shadows a bundled one of the same name.
    """
    schemas: dict[str, str] = {}
    traces: dict[str, str] = {}
    for d in _example_search_dirs():
        for f in os.listdir(d):
            full = os.path.join(d, f)
            if f.endswith(".mp") and f not in schemas:
                schemas[f] = full
            elif f.endswith(".gry") and f not in traces:
                traces[f] = full

    out = []
    for s, s_path in sorted(schemas.items()):
        stem = s[:-3]
        matching = sorted(
            (g, t_path) for g, t_path in traces.items()
            if g.startswith(stem.split("_")[0])
        )
        out.append({
            "schema": s,
            "schema_path": s_path,
            "traces": [
                {"name": g, "path": t_path} for g, t_path in matching
            ],
        })
    return out


def _find_example(name: str) -> str | None:
    """Resolve an example filename against the search dirs."""
    name = os.path.basename(name)
    for d in _example_search_dirs():
        cand = os.path.join(d, name)
        if os.path.isfile(cand):
            return cand
    return None


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
            name = request.form["example_schema"]
            resolved = _find_example(name)
            if resolved is None:
                return jsonify(
                    {"error": f"example schema not found: {name}"}
                ), 400
            schema_path = resolved
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
            resolved = _find_example(request.form["example_traces"])
            if resolved is not None:
                gry_path = resolved

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


# Launcher: standalone mode -------------------------------------------

def _pick_free_port(preferred: int = 5000) -> int:
    """Return preferred if free, else any free port the OS picks."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _open_browser(url: str, delay: float = 0.8) -> None:
    """Open the user's default browser to `url` after a short delay
    (gives the server time to bind)."""
    import threading
    import webbrowser

    def _go():
        try:
            webbrowser.open_new(url)
        except Exception:
            pass

    t = threading.Timer(delay, _go)
    t.daemon = True
    t.start()


def main() -> None:
    port = _pick_free_port(5000)
    url = f"http://127.0.0.1:{port}"
    print(f"MP Schema Gap Scanner")
    print(f"  serving on {url}")
    print(f"  press Ctrl+C to quit")
    _open_browser(url)
    # Prefer waitress (production-quality, no dev warnings) when
    # available; fall back to Flask dev server otherwise.
    try:
        from waitress import serve
        serve(app, host="127.0.0.1", port=port, threads=4, _quiet=True)
    except ImportError:
        app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
