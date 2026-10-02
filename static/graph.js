/* graph.js -- Implicit Assumption Graph view for the MP schema scanner.
 *
 * Self-contained interactive SVG renderer (no external library, so it
 * survives the single-file PyInstaller build). Draws explicit edges from
 * the schema immediately, then -- on demand -- runs the SME agent over the
 * deduplicated flagged patterns and adds the discovered implicit edges,
 * logging every step for provenance.
 */
(function () {
  const $ = (id) => document.getElementById(id);
  const SVGNS = "http://www.w3.org/2000/svg";

  // selection mirrors app.js so the graph uses the same inputs
  const sel = { schemaFile: null, tracesFile: null,
                exampleSchema: null, exampleTraces: null };
  let graph = null;          // {roots,nodes,edges,patterns,stats}
  let patterns = [];
  let view = { k: 1, x: 0, y: 0 };   // zoom/pan transform
  let lastDims = null;             // natural {W,H} for export

  const EDGE_STYLE = {
    requires:    { color: "#374151", dash: "",        w: 1.5, arrow: true  },
    mutex:       { color: "#cc0000", dash: "5,4",     w: 1.5, arrow: false },
    conditional: { color: "#9ca3af", dash: "2,3",     w: 1.3, arrow: true  },
    ordering:    { color: "#1f6feb", dash: "",        w: 1.3, arrow: true  },
    implicit:    { color: "#e8730c", dash: "6,3",     w: 2.6, arrow: true  },
    emergent:    { color: "#7b2ff7", dash: "6,3",     w: 2.6, arrow: true  },
    proposed:    { color: "#0d9488", dash: "5,3",     w: 2.2, arrow: true  },
  };
  const ROOT_FILL = ["#fff3cd","#d1ecf1","#d4edda","#e2d9f3","#f8d7da",
                     "#ffe5d0","#d6d8db","#e7f0d4","#fde2e4","#cfe8ef"];

  // ---- input mirroring (attach to the same controls app.js uses) ----
  function wire() {
    const sf = $("schema-file"), tf = $("traces-file");
    if (sf) sf.addEventListener("change", (e) => {
      sel.schemaFile = e.target.files[0] || null; sel.exampleSchema = null; });
    if (tf) tf.addEventListener("change", (e) => {
      sel.tracesFile = e.target.files[0] || null; sel.exampleTraces = null; });
    document.querySelectorAll(".example-btn").forEach((b) =>
      b.addEventListener("click", () => {
        sel.exampleSchema = b.dataset.schema;
        sel.exampleTraces = b.dataset.traces || null;
        sel.schemaFile = null; sel.tracesFile = null;
      }));
    const build = $("btn-build-graph");
    if (build) build.addEventListener("click", buildGraph);
    const run = $("btn-complete-sme");
    if (run) run.addEventListener("click", completeWithSME);
    const png = $("btn-export-png");
    if (png) png.addEventListener("click", exportPNG);
    const dot = $("btn-export-dot");
    if (dot) dot.addEventListener("click", exportDOT);
  }

  function formData() {
    const fd = new FormData();
    if (sel.schemaFile) fd.append("schema_file", sel.schemaFile);
    else if (sel.exampleSchema) fd.append("example_schema", sel.exampleSchema);
    if (sel.tracesFile) fd.append("traces_file", sel.tracesFile);
    else if (sel.exampleTraces) fd.append("example_traces", sel.exampleTraces);
    return fd;
  }

  // ---------------------------- build ---------------------------------
  async function buildGraph() {
    const status = $("graph-status");
    if (!sel.schemaFile && !sel.exampleSchema) {
      status.textContent = "Choose a schema first (above)."; return;
    }
    status.textContent = "Building graph...";
    $("graph-panel").classList.remove("hidden");
    try {
      const resp = await fetch("/api/assumption_graph",
                               { method: "POST", body: formData() });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "build failed");
      graph = data;
      patterns = data.patterns || [];
      view = { k: 1, x: 0, y: 0 };
      render();
      logReset();
      const n = patterns.length;
      status.textContent =
        `${graph.nodes.length} states, ${graph.edges.length} explicit edges, ` +
        `${graph.stats.trace_count} traces -> ${n} review pattern${n===1?"":"s"}.`;
      $("btn-complete-sme").disabled = (n === 0);
      $("btn-complete-sme").title = n === 0
        ? "Load a .gry trace file to discover implicit edges" : "";
      renderPatterns();
    } catch (e) {
      status.textContent = "Error: " + e.message;
    }
  }

  // ------------------------- SME completion ---------------------------
  async function completeWithSME() {
    if (!patterns.length) return;
    const btn = $("btn-complete-sme");
    btn.disabled = true;
    const domain = ($("sme-domain") || {}).value || "Systems Architecture";
    const apiKey = ($("sme-api-key") || {}).value || "";
    const model = ($("sme-model") || {}).value ||
                  "meta-llama/llama-3.1-8b-instruct:free";
    const valid = graph.nodes.map((n) => n.id);
    let added = 0;
    for (let i = 0; i < patterns.length; i++) {
      const p = patterns[i];
      $("graph-status").textContent =
        `SME reviewing pattern ${i + 1}/${patterns.length} (${p.id})...`;
      try {
        const resp = await fetch("/api/sme_pattern", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pattern: p, trace: p.witness_text,
            domain, api_key: apiKey, model, valid_states: valid }),
        });
        const d = await resp.json();
        if (!resp.ok) throw new Error(d.error || "sme error");
        const edges = d.new_edges || [];
        // de-dup against existing edges
        for (const e of edges) {
          if (!graph.edges.some((x) =>
                x.src === e.src && x.dst === e.dst && x.type === e.type)) {
            graph.edges.push(e); added++;
          }
        }
        logEntry(p, d.parsed, edges);
      } catch (e) {
        logError(p, e.message);
      }
      render();
    }
    $("graph-status").textContent =
      `SME pass complete: ${added} implicit/emergent edge${added===1?"":"s"} added.`;
    btn.disabled = false;
  }

  // ----------------------------- render -------------------------------
  function render() {
    // Prefer the real Graphviz engine (viz.js, WASM) for layout quality;
    // fall back to the built-in column renderer if it isn't available
    // (e.g. offline with no vendored copy).
    if (window.Viz) renderGraphviz(); else renderFallback();
  }

  function renderGraphviz() {
    const host = $("graph-svg-wrap");
    try {
      const viz = new Viz();
      viz.renderSVGElement(buildDot(true)).then(function (svgEl) {
        host.innerHTML = "";
        svgEl.classList.add("iag-gv");
        host.appendChild(svgEl);
        const vb = svgEl.getAttribute("viewBox");
        if (vb) { const p = vb.split(/[\s,]+/).map(Number); lastDims = { W: p[2], H: p[3] }; }
        // wire edge -> provenance using the ids we baked into the DOT
        graph.edges.forEach(function (e, i) {
          const el = svgEl.querySelector("#e" + i);
          if (el) {
            el.style.cursor = "pointer";
            el.addEventListener("click", function (ev) { ev.stopPropagation(); showProv(e); });
          }
        });
      }).catch(function (err) { console.warn("viz.js failed, fallback:", err); renderFallback(); });
    } catch (e) { renderFallback(); }
  }

  function renderFallback() {
    const host = $("graph-svg-wrap");
    host.innerHTML = "";
    if (!graph) return;
    const roots = graph.roots;
    const COLW = 210, ROWH = 46, PADX = 30, PADY = 56, NODEW = 150, NODEH = 26;
    const byRoot = {};
    roots.forEach((r) => (byRoot[r] = []));
    graph.nodes.forEach((n) => { (byRoot[n.root] || (byRoot[n.root] = [])).push(n); });
    const maxRows = Math.max(1, ...roots.map((r) => byRoot[r].length));
    const W = PADX * 2 + roots.length * COLW;
    const H = PADY + maxRows * ROWH + 30;
    lastDims = { W, H };

    const pos = {};
    roots.forEach((r, ci) => {
      byRoot[r].forEach((n, ri) => {
        pos[n.id] = { x: PADX + ci * COLW + (COLW - NODEW) / 2,
                      y: PADY + ri * ROWH, w: NODEW, h: NODEH };
      });
    });

    const svg = document.createElementNS(SVGNS, "svg");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("class", "iag-svg");
    svg.style.width = W + "px"; svg.style.height = H + "px";

    // arrowhead markers per edge color
    const defs = document.createElementNS(SVGNS, "defs");
    Object.entries(EDGE_STYLE).forEach(([t, s]) => {
      const m = document.createElementNS(SVGNS, "marker");
      m.setAttribute("id", "arw-" + t); m.setAttribute("markerWidth", "8");
      m.setAttribute("markerHeight", "8"); m.setAttribute("refX", "7");
      m.setAttribute("refY", "3"); m.setAttribute("orient", "auto");
      const pa = document.createElementNS(SVGNS, "path");
      pa.setAttribute("d", "M0,0 L7,3 L0,6 Z"); pa.setAttribute("fill", s.color);
      m.appendChild(pa); defs.appendChild(m);
    });
    svg.appendChild(defs);

    const g = document.createElementNS(SVGNS, "g");
    g.setAttribute("transform",
      `translate(${view.x},${view.y}) scale(${view.k})`);
    svg.appendChild(g);

    // root column headers
    roots.forEach((r, ci) => {
      const t = document.createElementNS(SVGNS, "text");
      t.setAttribute("x", PADX + ci * COLW + COLW / 2);
      t.setAttribute("y", 28); t.setAttribute("text-anchor", "middle");
      t.setAttribute("class", "iag-col"); t.textContent = r.replace(/_/g, " ");
      g.appendChild(t);
    });

    // edges
    const edgeLayer = document.createElementNS(SVGNS, "g");
    g.appendChild(edgeLayer);
    graph.edges.forEach((e, i) => {
      const a = pos[e.src], b = pos[e.dst];
      if (!a || !b) return;
      const s = EDGE_STYLE[e.type] || EDGE_STYLE.requires;
      const ax = a.x + a.w, ay = a.y + a.h / 2;
      const bx = b.x, by = b.y + b.h / 2;
      const a2 = (bx >= ax) ? ax : a.x, b2 = (bx >= ax) ? bx : b.x + b.w;
      const mx = (a2 + b2) / 2;
      const path = document.createElementNS(SVGNS, "path");
      path.setAttribute("d", `M${a2},${ay} C${mx},${ay} ${mx},${by} ${b2},${by}`);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", s.color);
      path.setAttribute("stroke-width", s.w);
      if (s.dash) path.setAttribute("stroke-dasharray", s.dash);
      if (s.arrow) path.setAttribute("marker-end", "url(#arw-" + e.type + ")");
      path.setAttribute("class", "iag-edge");
      path.dataset.idx = i;
      path.addEventListener("click", (ev) => { ev.stopPropagation(); showProv(e); });
      path.addEventListener("mouseenter", () => path.classList.add("hot"));
      path.addEventListener("mouseleave", () => path.classList.remove("hot"));
      edgeLayer.appendChild(path);
    });

    // nodes
    graph.nodes.forEach((n, ci) => {
      const p = pos[n.id]; if (!p) return;
      const grp = document.createElementNS(SVGNS, "g");
      grp.setAttribute("class", "iag-node"); grp.dataset.id = n.id;
      const rect = document.createElementNS(SVGNS, "rect");
      rect.setAttribute("x", p.x); rect.setAttribute("y", p.y);
      rect.setAttribute("width", p.w); rect.setAttribute("height", p.h);
      rect.setAttribute("rx", 5);
      const fill = ROOT_FILL[graph.roots.indexOf(n.root) % ROOT_FILL.length];
      rect.setAttribute("fill", n.reachable === false ? "#f3f4f6" : fill);
      rect.setAttribute("stroke", n.reachable === false ? "#cc0000" : "#9aa0a6");
      if (n.reachable === false) rect.setAttribute("stroke-dasharray", "4,2");
      grp.appendChild(rect);
      const t = document.createElementNS(SVGNS, "text");
      t.setAttribute("x", p.x + p.w / 2); t.setAttribute("y", p.y + p.h / 2 + 4);
      t.setAttribute("text-anchor", "middle"); t.setAttribute("class", "iag-lbl");
      t.textContent = n.label + (n.reachable === false ? "  (unreachable)" : "");
      grp.appendChild(t);
      grp.addEventListener("mouseenter", () => highlight(n.id, edgeLayer, true));
      grp.addEventListener("mouseleave", () => highlight(n.id, edgeLayer, false));
      g.appendChild(grp);
    });

    // pan/zoom
    svg.addEventListener("wheel", (ev) => {
      ev.preventDefault();
      const f = ev.deltaY < 0 ? 1.1 : 0.9;
      view.k = Math.max(0.3, Math.min(3, view.k * f));
      g.setAttribute("transform",
        `translate(${view.x},${view.y}) scale(${view.k})`);
    }, { passive: false });
    let drag = null;
    svg.addEventListener("mousedown", (ev) => { drag = { x: ev.clientX, y: ev.clientY, ox: view.x, oy: view.y }; });
    window.addEventListener("mousemove", (ev) => {
      if (!drag) return;
      view.x = drag.ox + (ev.clientX - drag.x);
      view.y = drag.oy + (ev.clientY - drag.y);
      g.setAttribute("transform",
        `translate(${view.x},${view.y}) scale(${view.k})`);
    });
    window.addEventListener("mouseup", () => { drag = null; });

    host.appendChild(svg);
  }

  function highlight(id, edgeLayer, on) {
    graph.edges.forEach((e, i) => {
      const el = edgeLayer.querySelector(`[data-idx="${i}"]`);
      if (!el) return;
      if (on) el.classList.toggle("dim", !(e.src === id || e.dst === id));
      else el.classList.remove("dim");
    });
  }

  function showProv(e) {
    const box = $("graph-prov");
    const pr = e.provenance || {};
    let html = `<div class="prov-h">${e.src} &rarr; ${e.dst}` +
               `<span class="etag tag-${e.type}">${e.type}</span></div>`;
    if (pr.source === "schema") {
      html += `<div class="prov-row"><b>From schema:</b> ${pr.kind}</div>` +
              `<pre>${esc(pr.rule || "")}</pre>`;
    } else if (pr.source === "sme") {
      html += `<div class="prov-row"><b>Discovered by SME</b> ` +
              `(verdict: ${pr.verdict}, model: ${esc(pr.model||"")})</div>`;
      if (pr.pattern_id) html += `<div class="prov-row">pattern ${pr.pattern_id}</div>`;
      if (pr.witness) html += `<pre>${esc(traceStr(pr.witness))}</pre>`;
      if (pr.gadget) html += `<div class="prov-row"><b>gadget:</b></div><pre>${esc(pr.gadget)}</pre>`;
      if (pr.raw) html += `<details><summary>SME verdict text</summary><pre>${esc(pr.raw)}</pre></details>`;
    }
    box.innerHTML = html;
    box.classList.remove("hidden");
  }

  // ------------------------- patterns + log ---------------------------
  function renderPatterns() {
    const box = $("graph-patterns");
    if (!patterns.length) { box.innerHTML =
      "<em>No flagged patterns (add a .gry trace file to discover implicit edges).</em>"; return; }
    let h = `<h4>Review worklist — ${patterns.length} distinct patterns</h4>` +
            `<table class="pat-tbl"><tr><th>#</th><th>shape</th>` +
            `<th>present</th><th>missing</th><th>traces</th></tr>`;
    patterns.forEach((p) => {
      h += `<tr><td>${p.id}</td><td>${p.shape}</td><td>${esc(p.positive)}</td>` +
           `<td>${esc(p.negatives.join(" | "))}</td><td>${p.trace_count}</td></tr>`;
    });
    box.innerHTML = h + "</table>";
  }

  function logReset() { $("graph-log").innerHTML =
    "<h4>SME process log</h4><div class='log-empty'>Run \"Complete with SME\" to populate.</div>"; }
  function logLine(html, cls) {
    const log = $("graph-log");
    const empty = log.querySelector(".log-empty"); if (empty) empty.remove();
    const d = document.createElement("div");
    d.className = "log-row " + (cls || ""); d.innerHTML = html; log.appendChild(d);
  }
  function logEntry(p, parsed, edges) {
    const v = parsed ? parsed.verdict : "?";
    let s = `<b>${p.id}</b> [${esc(p.positive)} !&rarr; ${esc(p.negatives.join("|"))}] ` +
            `&rArr; <span class="v-${v}">${v}</span>`;
    if (edges && edges.length)
      s += " — added " + edges.map((e) => `${e.src}&rarr;${e.dst}`).join(", ");
    else
      s += " — no edge";
    if (v === "gap" && parsed && parsed.reject)
      s += ` <code>${esc(parsed.reject.slice(0, 90))}</code>`;
    logLine(s, "v-" + v);
  }
  function logError(p, msg) { logLine(`<b>${p.id}</b> — error: ${esc(msg)}`, "v-err"); }

  // ----------------------------- utils --------------------------------
  function esc(s) { return String(s == null ? "" : s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
  function traceStr(st) { return Object.keys(st).sort()
    .map((k) => k + "=" + st[k]).join(", "); }

  // --------------------------- exports --------------------------------
  function buildDot(withIds) {
    const q = (x) => '"' + String(x).replace(/"/g, '\\"') + '"';
    const ST = { requires:["black","solid"], mutex:["#cc0000","dashed"],
      conditional:["#9ca3af","dotted"], ordering:["#1f6feb","solid"],
      implicit:["#e8730c","bold"], emergent:["#7b2ff7","bold"],
      proposed:["#0d9488","dashed"] };
    let d = "digraph IAG {\n  rankdir=LR;\n  bgcolor=\"white\";\n" +
      "  node [shape=box, style=\"rounded,filled\", fontname=Helvetica, fontsize=10, color=\"#9aa0a6\"];\n" +
      "  edge [fontname=Helvetica, fontsize=8];\n";
    const byRoot = {};
    graph.nodes.forEach((n) => { (byRoot[n.root] || (byRoot[n.root] = [])).push(n); });
    let ci = 0;
    for (const r in byRoot) {
      d += "  subgraph cluster_" + (ci++) + " {\n    label=" + q(r.replace(/_/g, " ")) +
           "; style=filled; color=\"#e9ecef\"; fontsize=11;\n";
      byRoot[r].forEach((n) => {
        const unr = n.reachable === false;
        const fill = unr ? "#f3f4f6" : "#eef3f8";
        const ex = unr ? ', color="#cc0000", style="rounded,filled,dashed"' : "";
        d += "    " + q(n.id) + " [label=" + q(n.label) + ', fillcolor="' + fill + '"' + ex + "];\n";
      });
      d += "  }\n";
    }
    graph.edges.forEach((e, i) => {
      const s2 = ST[e.type] || ST.requires;
      let a = 'color="' + s2[0] + '"';
      if (s2[1] === "dashed") a += ", style=dashed";
      else if (s2[1] === "dotted") a += ", style=dotted";
      else if (s2[1] === "bold") a += ", penwidth=2.4";
      if (e.type === "mutex") a += ", dir=none";
      if (withIds) a += ", id=" + q("e" + i);
      d += "  " + q(e.src) + " -> " + q(e.dst) + " [" + a + "];\n";
    });
    // embedded legend (shows in-graph and in PNG/DOT exports)
    const L = [["#374151","requires"], ["#cc0000","mutex (no arrow)"],
      ["#9ca3af","conditional"], ["#1f6feb","ordering (before)"],
      ["#e8730c","implicit (SME)"], ["#7b2ff7","emergent (gadget)"],
      ["#0d9488","proposed REJECT (gap)"]];
    d += '  subgraph cluster_legend {\n    label="Legend"; labelloc="t"; ' +
         'fontsize=11; style=filled; color="#f7f7f9";\n';
    d += '    _legend [shape=plaintext, label=<' +
         '<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="1">';
    L.forEach(function (it) {
      d += '<TR><TD ALIGN="LEFT"><FONT COLOR="' + it[0] +
           '">&#9472;&#9472;&#9472; ' + it[1] + '</FONT></TD></TR>';
    });
    d += '<TR><TD ALIGN="LEFT"><FONT COLOR="#cc0000">' +
         '&#9633; unreachable state</FONT></TD></TR>';
    d += '</TABLE>>];\n  }\n';
    return d + "}\n";
  }

  function exportPNG() {
    const svg = document.querySelector("#graph-svg-wrap svg");
    if (!svg) { $("graph-status").textContent = "Build the graph first."; return; }
    let W, H; const vb = svg.getAttribute("viewBox");
    if (vb) { const p = vb.split(/[\s,]+/).map(Number); W = p[2]; H = p[3]; }
    else if (lastDims) { W = lastDims.W; H = lastDims.H; }
    else { W = svg.clientWidth || 1000; H = svg.clientHeight || 700; }
    const scale = 2, clone = svg.cloneNode(true);
    if (svg.classList.contains("iag-svg")) {           // reset our own pan/zoom
      const g = clone.querySelector("g");
      if (g) g.setAttribute("transform", "translate(0,0) scale(1)");
    }
    clone.setAttribute("width", W); clone.setAttribute("height", H);
    clone.setAttribute("viewBox", "0 0 " + W + " " + H);
    const style = document.createElementNS(SVGNS, "style");
    style.textContent = ".iag-col{font:600 12px Helvetica,Arial,sans-serif;fill:#333;}" +
      ".iag-lbl{font:11px Helvetica,Arial,sans-serif;fill:#1f2937;}";
    clone.insertBefore(style, clone.firstChild);
    const xml = new XMLSerializer().serializeToString(clone);
    const url = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(xml)));
    const img = new Image();
    img.onload = function () {
      const c = document.createElement("canvas");
      c.width = W * scale; c.height = H * scale;
      const ctx = c.getContext("2d");
      ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, c.width, c.height);
      ctx.scale(scale, scale); ctx.drawImage(img, 0, 0);
      const a = document.createElement("a");
      a.href = c.toDataURL("image/png"); a.download = "assumption_graph.png"; a.click();
      $("graph-status").textContent = "Saved assumption_graph.png";
    };
    img.onerror = function () {
      $("graph-status").textContent = "PNG export failed; use Download DOT + Graphviz.";
    };
    img.src = url;
  }

  function exportDOT() {
    if (!graph) { $("graph-status").textContent = "Build the graph first."; return; }
    const blob = new Blob([buildDot(false)], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "assumption_graph.dot"; a.click();
    $("graph-status").textContent =
      "Saved assumption_graph.dot (render: dot -Tpng assumption_graph.dot -o iag.png)";
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", wire);
  else wire();
})();
