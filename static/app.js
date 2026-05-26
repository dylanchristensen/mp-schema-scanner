/* Front-end glue for the MP schema gap scanner. */
(function () {
  const $ = (id) => document.getElementById(id);

  const state = {
    schemaFile: null,
    tracesFile: null,
    exampleSchema: null,
    exampleTraces: null,
  };

  function setSchemaName(name) {
    $("schema-name").textContent = name || "no file";
  }
  function setTracesName(name) {
    $("traces-name").textContent = name || "no file";
  }

  // File pickers (also clear example selection).
  $("schema-file").addEventListener("change", (e) => {
    state.schemaFile = e.target.files[0] || null;
    state.exampleSchema = null;
    setSchemaName(state.schemaFile ? state.schemaFile.name : "");
  });
  $("traces-file").addEventListener("change", (e) => {
    state.tracesFile = e.target.files[0] || null;
    state.exampleTraces = null;
    setTracesName(state.tracesFile ? state.tracesFile.name : "");
  });

  // Drag and drop.
  function wireDrop(zoneId, inputId, onFile) {
    const zone = $(zoneId);
    const input = $(inputId);
    zone.addEventListener("click", () => input.click());
    ["dragenter", "dragover"].forEach((ev) =>
      zone.addEventListener(ev, (e) => {
        e.preventDefault();
        zone.classList.add("dragover");
      })
    );
    ["dragleave", "drop"].forEach((ev) =>
      zone.addEventListener(ev, (e) => {
        e.preventDefault();
        zone.classList.remove("dragover");
      })
    );
    zone.addEventListener("drop", (e) => {
      const f = e.dataTransfer.files[0];
      if (f) onFile(f);
    });
  }
  wireDrop("schema-drop", "schema-file", (f) => {
    state.schemaFile = f;
    state.exampleSchema = null;
    setSchemaName(f.name);
  });
  wireDrop("traces-drop", "traces-file", (f) => {
    state.tracesFile = f;
    state.exampleTraces = null;
    setTracesName(f.name);
  });

  // Example buttons.
  document.querySelectorAll(".example-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.exampleSchema = btn.dataset.schema;
      state.exampleTraces = btn.dataset.traces || null;
      state.schemaFile = null;
      state.tracesFile = null;
      $("schema-file").value = "";
      $("traces-file").value = "";
      setSchemaName(state.exampleSchema + " (example)");
      setTracesName(
        state.exampleTraces ? state.exampleTraces + " (example)" : ""
      );
    });
  });

  // Run scan.
  $("run-btn").addEventListener("click", run);

  async function run() {
    const btn = $("run-btn");
    const status = $("status");
    $("results").classList.add("hidden");
    $("error-panel").classList.add("hidden");

    if (!state.schemaFile && !state.exampleSchema) {
      status.textContent = "Please choose a schema file first.";
      return;
    }
    btn.disabled = true;
    status.textContent = "Scanning...";

    const fd = new FormData();
    if (state.schemaFile) fd.append("schema_file", state.schemaFile);
    else fd.append("example_schema", state.exampleSchema);
    if (state.tracesFile) fd.append("traces_file", state.tracesFile);
    else if (state.exampleTraces)
      fd.append("example_traces", state.exampleTraces);

    try {
      const resp = await fetch("/api/scan", { method: "POST", body: fd });
      const data = await resp.json();
      if (!resp.ok) {
        showError(data);
      } else {
        render(data);
      }
    } catch (e) {
      showError({ error: String(e) });
    } finally {
      btn.disabled = false;
      status.textContent = "";
    }
  }

  function showError(data) {
    $("error-panel").classList.remove("hidden");
    $("error-text").textContent =
      (data.error || "Unknown error") +
      (data.traceback ? "\n\n" + data.traceback : "");
  }

  function el(tag, attrs = {}, ...children) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") e.className = v;
      else if (k === "html") e.innerHTML = v;
      else e.setAttribute(k, v);
    }
    for (const c of children) {
      if (c == null) continue;
      e.append(c.nodeType ? c : document.createTextNode(c));
    }
    return e;
  }

  function fmtRate(r) {
    return (r * 100).toFixed(1) + "%";
  }

  function fmtTraceStates(states) {
    return Object.keys(states)
      .sort()
      .map((k) => k + "=" + states[k])
      .join(", ");
  }

  function render(data) {
    const r = $("results");
    r.classList.remove("hidden");

    // Summary cards.
    const summary = $("summary");
    summary.innerHTML = "";
    const s = data.schema;
    const cards = [
      { label: "Schema", value: s.path, cls: "" },
      { label: "Roots", value: s.root_count, cls: "" },
      { label: "States", value: s.state_count, cls: "" },
      { label: "Orderings", value: s.ordering_count, cls: "" },
      { label: "REJECTs", value: s.reject_count, cls: "" },
      {
        label: "Candidate findings",
        value: data.totals.all,
        cls: data.totals.all > 0 ? "accent" : "",
      },
    ];
    if (data.traces) {
      cards.splice(1, 0, {
        label: "Traces",
        value: data.traces.path,
        cls: "",
      });
    }
    for (const c of cards) {
      summary.append(
        el(
          "div",
          { class: "summary-card " + c.cls },
          el("div", { class: "label" }, c.label),
          el("div", { class: "value" }, String(c.value))
        )
      );
    }

    const findings = $("findings");
    findings.innerHTML = "";
    const shapeNames = {
      A: "Shape A -- vacuous-foreach gaps",
      B: "Shape B -- symmetric REJECT completion",
      C: "Shape C -- optional-event escalation",
    };
    for (const shape of ["A", "B", "C"]) {
      const cands = data.candidates[shape];
      const block = el(
        "div",
        { class: "shape-block" },
        el(
          "h3",
          {},
          shapeNames[shape],
          el("span", { class: "count" }, "(" + cands.length + ")")
        )
      );
      if (cands.length === 0) {
        block.append(
          el(
            "div",
            { class: "evidence-summary" },
            "No candidates."
          )
        );
      } else {
        cands.forEach((c, i) => {
          block.append(renderCandidate(shape, i + 1, c));
        });
      }
      findings.append(block);
    }
  }

  function renderCandidate(shape, idx, c) {
    const div = el("div", { class: "candidate shape-" + shape });
    div.append(el("div", { class: "cid" }, shape + idx));
    div.append(el("div", { class: "rationale" }, c.rationale));
    div.append(
      el(
        "div",
        { class: "rule" },
        "IF " + c.suggested_reject + "; FI;"
      )
    );
    if (c.evidence) {
      const ev = el("div", { class: "evidence" });
      const bar = el("div", { class: "evidence-bar" });
      bar.append(
        el("div", {
          class: "fill",
          style: "width:" + Math.min(100, c.evidence.violation_rate * 100) + "%",
        })
      );
      ev.append(bar);
      ev.append(
        el(
          "div",
          { class: "evidence-summary" },
          el(
            "strong",
            {},
            c.evidence.violation_count + " of " + c.evidence.trace_count
          ),
          " traces violate this proposed rule (" +
            fmtRate(c.evidence.violation_rate) +
            ")"
        )
      );
      if (c.evidence.sample && c.evidence.sample.length) {
        const det = el(
          "details",
          { class: "samples" },
          el(
            "summary",
            {},
            "Show " + c.evidence.sample.length + " sample traces"
          )
        );
        for (const s of c.evidence.sample) {
          det.append(
            el(
              "div",
              { class: "sample" },
              el("span", { class: "tid" }, "#" + s.trace_id),
              fmtTraceStates(s.states)
            )
          );
        }
        ev.append(det);
      }
      div.append(ev);
    }
    return div;
  }
})();
