(() => {
  "use strict";
  const data = JSON.parse(document.getElementById("ossnet-data").textContent);
  const NS = "http://www.w3.org/2000/svg";
  const fmt = new Intl.NumberFormat("en-US");
  const pct = (x) => (x == null ? "n/a" : `${Math.round(x * 100)}%`);
  const CHAR_W = 6.6; // approximate width of a 12px label character

  function el(tag, attrs, parent) {
    const node = document.createElementNS(NS, tag);
    for (const k in attrs) node.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(node);
    return node;
  }

  function label(parent, x, y, str, cls, anchor = "start") {
    const t = el("text", { x, y, class: cls, "text-anchor": anchor }, parent);
    t.textContent = str;
    return t;
  }

  // ---------- tooltip ----------
  const tip = document.createElement("div");
  tip.className = "tooltip";
  tip.hidden = true;
  document.body.appendChild(tip);

  function showTip(x, y, title, rows) {
    tip.replaceChildren();
    if (title) {
      const t = document.createElement("div");
      t.className = "tt-title";
      t.textContent = title;
      tip.appendChild(t);
    }
    for (const r of rows) {
      const row = document.createElement("div");
      row.className = "tt-row";
      if (r.key) {
        const k = document.createElement("i");
        k.className = "tt-key";
        k.style.background = `var(${r.key})`;
        row.appendChild(k);
      }
      const v = document.createElement("strong");
      v.textContent = r.value;
      row.appendChild(v);
      if (r.label) {
        const l = document.createElement("span");
        l.textContent = r.label;
        row.appendChild(l);
      }
      tip.appendChild(row);
    }
    tip.hidden = false;
    const w = tip.offsetWidth, h = tip.offsetHeight, pad = 14;
    let left = x + pad, top = y + pad;
    if (left + w > window.innerWidth - 8) left = x - w - pad;
    if (top + h > window.innerHeight - 8) top = y - h - pad;
    tip.style.left = `${Math.max(8, left)}px`;
    tip.style.top = `${Math.max(8, top)}px`;
  }

  function hideTip() {
    tip.hidden = true;
  }

  // Hover and keyboard focus show the same readout; `lift` marks respond.
  function bindTip(target, content, lift) {
    const on = () => lift && lift.classList.add("hover-lift");
    const off = () => {
      if (lift) lift.classList.remove("hover-lift");
      hideTip();
    };
    target.addEventListener("pointermove", (e) => {
      on();
      showTip(e.clientX, e.clientY, ...content());
    });
    target.addEventListener("pointerleave", off);
    target.addEventListener("focus", () => {
      on();
      const b = target.getBoundingClientRect();
      showTip(b.left + b.width / 2, b.top, ...content());
    });
    target.addEventListener("blur", off);
  }

  // ---------- scales & frame ----------
  function niceTicks(max, integer, target = 4) {
    if (!(max > 0)) max = 1;
    const raw = max / target;
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const f = raw / mag;
    let step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * mag;
    if (integer) step = Math.max(1, Math.round(step));
    const top = Math.ceil(max / step - 1e-9) * step;
    const ticks = [];
    for (let v = 0; v <= top + step / 2; v += step) ticks.push(Math.round(v * 1e6) / 1e6);
    return ticks;
  }

  function frame(fig, height, margin) {
    fig.replaceChildren();
    const width = Math.max(260, Math.floor(fig.clientWidth));
    const svg = el("svg", { viewBox: `0 0 ${width} ${height}`, width, height });
    fig.appendChild(svg);
    return {
      svg, width, height,
      x0: margin.left, x1: width - margin.right, y0: margin.top, y1: height - margin.bottom,
    };
  }

  function legend(fig, items) {
    const box = document.createElement("div");
    box.className = "legend";
    for (const item of items) {
      const span = document.createElement("span");
      const sw = document.createElement("i");
      if (item.dot) sw.className = "dot";
      sw.style.background = `var(${item.color})`;
      span.appendChild(sw);
      span.appendChild(document.createTextNode(item.text));
      box.appendChild(span);
    }
    fig.insertBefore(box, fig.firstChild);
  }

  function yAxis(f, ticks, y, format) {
    const grid = el("g", { class: "grid" }, f.svg);
    const axis = el("g", { class: "axis" }, f.svg);
    for (const t of ticks) {
      const yy = Math.round(y(t)) + 0.5;
      if (t !== 0) el("line", { x1: f.x0, x2: f.x1, y1: yy, y2: yy }, grid);
      label(axis, f.x0 - 6, yy + 4, format(t), "tick", "end");
    }
    const base = Math.round(y(0)) + 0.5;
    el("line", { class: "baseline", x1: f.x0, x2: f.x1, y1: base, y2: base }, f.svg);
  }

  // One label per year, skipping years that would crowd each other.
  function yearTicks(f, periods, xAt, minGap = 44) {
    const axis = el("g", { class: "axis" }, f.svg);
    let lastX = -Infinity;
    periods.forEach((p, i) => {
      const year = String(p).slice(0, 4);
      if (i > 0 && String(periods[i - 1]).slice(0, 4) === year) return;
      const x = xAt(i);
      if (x - lastX < minGap) return;
      label(axis, x, f.y1 + 17, year, "tick", "middle");
      lastX = x;
    });
  }

  // Column with a 4px rounded data end, square at the baseline.
  function column(x, y, w, h, r) {
    r = Math.max(0, Math.min(r, w / 2, h));
    return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
  }

  // ---------- charts ----------
  function activityChart(fig) {
    const rows = data.timeline;
    if (!rows.length) return;
    const f = frame(fig, 230, { top: 10, right: 78, bottom: 28, left: 38 });
    legend(fig, [
      { color: "--series-1", text: "Returning contributors" },
      { color: "--series-2", text: "Newcomers" },
    ]);
    const n = rows.length, band = (f.x1 - f.x0) / n;
    const w = Math.max(1, Math.min(24, band - 2));
    const ticks = niceTicks(Math.max(...rows.map((r) => r.contributors), 1), true);
    const y = (v) => f.y1 - (v / ticks[ticks.length - 1]) * (f.y1 - f.y0);
    yAxis(f, ticks, y, (v) => fmt.format(v));
    const marks = el("g", {}, f.svg);
    rows.forEach((r, i) => {
      const x = f.x0 + i * band + (band - w) / 2;
      const back = r.contributors - r.newcomers;
      const g = el("g", r.inProgress ? { opacity: 0.55 } : {}, marks);
      const mid = y(back);
      if (back > 0) el("path", { d: column(x, mid, w, y(0) - mid, r.newcomers ? 0 : 4), class: "s1" }, g);
      if (r.newcomers) {
        const bottom = back > 0 ? mid - 2 : y(0);
        const top = y(r.contributors);
        if (bottom - top > 0) el("path", { d: column(x, top, w, bottom - top, 4), class: "s2" }, g);
      }
      const hit = el("rect", {
        x: f.x0 + i * band, y: f.y0, width: band, height: f.y1 - f.y0, class: "hit", tabindex: 0,
        "aria-label": `${r.period}: ${r.contributors} contributors, ${r.newcomers} new`,
      }, f.svg);
      bindTip(hit, () => [r.period + (r.inProgress ? " (in progress)" : ""), [
        { value: fmt.format(r.contributors), label: "contributors" },
        { key: "--series-2", value: fmt.format(r.newcomers), label: "newcomers" },
        { key: "--series-1", value: fmt.format(back), label: "returning" },
        { value: fmt.format(r.commits), label: "commits" },
      ]], g);
    });
    yearTicks(f, rows.map((r) => r.period), (i) => f.x0 + (i + 0.5) * band);
    // Direct labels beside the last column when its segments leave room.
    const last = rows[n - 1], back = last.contributors - last.newcomers;
    const yBack = (y(0) + y(back)) / 2, yNew = (y(back) + y(last.contributors)) / 2;
    const lx = f.x1 + 8;
    if (back > 0 && last.newcomers > 0 && Math.abs(yBack - yNew) >= 14) {
      label(f.svg, lx, yBack + 4, "returning", "label");
      label(f.svg, lx, yNew + 4, "new", "label");
    }
  }

  function lineChart(fig, key, name) {
    const rows = data.timeline;
    if (!rows.length) return;
    const vals = rows.map((r) => r[key]);
    const f = frame(fig, 190, { top: 14, right: 40, bottom: 28, left: 34 });
    const n = rows.length;
    const x = (i) => (n === 1 ? (f.x0 + f.x1) / 2 : f.x0 + (i / (n - 1)) * (f.x1 - f.x0));
    const ticks = niceTicks(Math.max(...vals, 1), true);
    const y = (v) => f.y1 - (v / ticks[ticks.length - 1]) * (f.y1 - f.y0);
    yAxis(f, ticks, y, (v) => fmt.format(v));
    const d = vals.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
    el("path", { d, class: "line" }, f.svg);
    const end = n - 1;
    el("circle", { cx: x(end), cy: y(vals[end]), r: 4, class: "s1 ring" }, f.svg);
    label(f.svg, x(end) + 9, y(vals[end]) + 4, fmt.format(vals[end]), "label strong");
    yearTicks(f, rows.map((r) => r.period), x);
    const cross = el("line", { class: "crosshair", y1: f.y0, y2: f.y1, visibility: "hidden" }, f.svg);
    const dot = el("circle", { r: 4, class: "s1 ring", visibility: "hidden" }, f.svg);
    const hit = el("rect", { x: f.x0, y: 0, width: f.x1 - f.x0, height: f.y1, class: "hit" }, f.svg);
    hit.addEventListener("pointermove", (e) => {
      const box = f.svg.getBoundingClientRect();
      const px = (e.clientX - box.left) * (f.width / box.width);
      const i = n === 1 ? 0 : Math.max(0, Math.min(n - 1, Math.round(((px - f.x0) / (f.x1 - f.x0)) * (n - 1))));
      for (const [k, v] of [["x1", x(i)], ["x2", x(i)]]) cross.setAttribute(k, v);
      dot.setAttribute("cx", x(i));
      dot.setAttribute("cy", y(vals[i]));
      cross.setAttribute("visibility", "visible");
      dot.setAttribute("visibility", "visible");
      showTip(e.clientX, e.clientY, rows[i].period, [{ key: "--series-1", value: fmt.format(vals[i]), label: name }]);
    });
    hit.addEventListener("pointerleave", () => {
      cross.setAttribute("visibility", "hidden");
      dot.setAttribute("visibility", "hidden");
      hideTip();
    });
  }

  function cohortChart(fig) {
    // Tiny cohorts swing between 0% and 100%; keep them in the table only.
    const big = data.cohorts.filter((r) => r.observed >= 10);
    const rows = big.length ? big : data.cohorts;
    if (!rows.length) {
      fig.textContent = "Not enough history to follow newcomers into their second year yet.";
      return;
    }
    const f = frame(fig, 210, { top: 20, right: 12, bottom: 28, left: 40 });
    const band = (f.x1 - f.x0) / rows.length, w = Math.max(1, Math.min(24, band - 2));
    const ticks = niceTicks(Math.max(...rows.map((r) => r.rate || 0), 0.05), false);
    const y = (v) => f.y1 - (v / ticks[ticks.length - 1]) * (f.y1 - f.y0);
    yAxis(f, ticks, y, pct);
    let peak = 0;
    rows.forEach((r, i) => { if ((r.rate || 0) > (rows[peak].rate || 0)) peak = i; });
    rows.forEach((r, i) => {
      const x = f.x0 + i * band + (band - w) / 2;
      const small = r.observed < 10;
      const g = el("g", {}, f.svg);
      const h = y(0) - y(r.rate || 0);
      if (h > 0) el("path", { d: column(x, y(r.rate), w, h, 4), class: small ? "so" : "s1" }, g);
      if (i === peak || i === rows.length - 1) {
        label(f.svg, x + w / 2, y(r.rate || 0) - 6, pct(r.rate), "label", "middle");
      }
      const hit = el("rect", {
        x: f.x0 + i * band, y: f.y0, width: band, height: f.y1 - f.y0, class: "hit", tabindex: 0,
        "aria-label": `${r.year}: ${pct(r.rate)} of ${r.observed} newcomers stayed`,
      }, f.svg);
      bindTip(hit, () => [`Joined in ${r.year}` + (small ? " (few newcomers)" : ""), [
        { key: "--series-1", value: pct(r.rate), label: "stayed" },
        { value: `${fmt.format(r.stayed)} of ${fmt.format(r.observed)}`, label: "newcomers" },
        { value: `${pct(r.lo)}–${pct(r.hi)}`, label: "95% interval" },
      ]], g);
    });
    yearTicks(f, rows.map((r) => r.year), (i) => f.x0 + (i + 0.5) * band, 40);
    const note = document.createElement("p");
    note.className = "caption";
    if (rows.length < data.cohorts.length) {
      note.textContent = "Years with fewer than 10 newcomers are only in the table.";
    } else if (rows.some((r) => r.observed < 10)) {
      note.textContent = "Gray columns: years with fewer than 10 newcomers.";
    }
    if (note.textContent) fig.appendChild(note);
  }

  // Stay rates with 95% intervals, one row per group.
  function dotPlot(fig, rows) {
    if (!rows.length) {
      fig.textContent = "Not enough newcomers to compare.";
      return;
    }
    const width = Math.max(260, Math.floor(fig.clientWidth));
    const longest = Math.max(...rows.map((r) => r.label.trim().length)) * CHAR_W + 24;
    const stacked = longest > width * 0.42; // narrow screens: labels above the dots
    const rowH = stacked ? 46 : 30;
    const f = frame(fig, rows.length * rowH + 32, {
      top: 4, right: 96, bottom: 28, left: stacked ? 8 : Math.ceil(longest),
    });
    const ticks = niceTicks(Math.max(...rows.map((r) => r.hi || 0), 0.05), false);
    const x = (v) => f.x0 + (v / ticks[ticks.length - 1]) * (f.x1 - f.x0);
    const grid = el("g", { class: "grid" }, f.svg);
    const axis = el("g", { class: "axis" }, f.svg);
    for (const t of ticks) {
      const xx = Math.round(x(t)) + 0.5;
      el("line", { x1: xx, x2: xx, y1: f.y0, y2: f.y1 }, grid);
      label(axis, xx, f.y1 + 17, pct(t), "tick", "middle");
    }
    rows.forEach((r, i) => {
      const top = f.y0 + i * rowH;
      const cy = stacked ? top + 32 : top + rowH / 2;
      const lx = stacked ? f.x0 + (r.indent ? 12 : 0) : (r.indent ? 16 : 0);
      label(f.svg, lx, stacked ? top + 14 : cy + 4, r.label.trim(), r.indent ? "label" : "label strong");
      const g = el("g", {}, f.svg);
      if (r.lo != null) el("line", { x1: x(r.lo), x2: x(r.hi), y1: cy, y2: cy, class: "whisker" }, g);
      el("circle", { cx: x(r.rate), cy, r: 5, class: "s1 ring" }, g);
      label(f.svg, f.x1 + 10, cy + 4, `${pct(r.rate)} of ${fmt.format(r.n)}`, "label");
      const hit = el("rect", {
        x: 0, y: top, width: f.width, height: rowH, class: "hit", tabindex: 0,
        "aria-label": `${r.label.trim()}: ${pct(r.rate)} of ${r.n} stayed`,
      }, f.svg);
      bindTip(hit, () => [r.label.trim(), [
        { key: "--series-1", value: pct(r.rate), label: "stayed" },
        { value: `${fmt.format(r.stayed)} of ${fmt.format(r.n)}`, label: "newcomers" },
        { value: `${pct(r.lo)}–${pct(r.hi)}`, label: "95% interval" },
      ]], g);
    });
  }

  function networkChart(fig) {
    const net = data.network;
    if (!net.nodes.length) {
      fig.textContent = "No contributors in the last 12 months.";
      return;
    }
    const width = Math.max(260, Math.floor(fig.clientWidth));
    const height = Math.round(Math.min(560, Math.max(300, width * 0.62)));
    const f = frame(fig, height, { top: 14, right: 14, bottom: 14, left: 14 });
    const sizes = [0, 0, 0];
    let other = 0;
    for (const n of net.nodes) {
      if (n.community != null && n.community < 3) sizes[n.community] += 1;
      else other += 1;
    }
    const items = sizes
      .map((s, i) => ({ color: `--series-${i + 1}`, text: `Community ${i + 1} (${s})`, dot: true, s }))
      .filter((it) => it.s > 0);
    if (other) items.push({ color: "--other", text: `Other (${other})`, dot: true });
    legend(fig, items);
    if (net.shown < net.total) {
      const note = document.createElement("p");
      note.className = "caption";
      note.textContent = `Showing the ${net.shown} most active of ${net.total} people.`;
      fig.appendChild(note);
    }
    const px = (v) => f.x0 + v * (f.x1 - f.x0), py = (v) => f.y0 + v * (f.y1 - f.y0);
    const byId = new Map(net.nodes.map((n) => [n.id, n]));
    const maxW = Math.max(...net.edges.map((e) => e.weight), 1e-9);
    const edges = el("g", {}, f.svg);
    for (const e of net.edges) {
      const a = byId.get(e.source), b = byId.get(e.target), t = Math.sqrt(e.weight / maxW);
      el("line", {
        x1: px(a.x), y1: py(a.y), x2: px(b.x), y2: py(b.y), class: "edge",
        "stroke-width": (0.6 + 2.2 * t).toFixed(2), "stroke-opacity": (0.16 + 0.5 * t).toFixed(2),
      }, edges);
    }
    const maxC = Math.max(...net.nodes.map((n) => n.commits));
    const radius = (n) => 3.5 + 10 * Math.sqrt(n.commits / maxC);
    const cls = (n) => (n.community != null && n.community < 3 ? `s${n.community + 1}` : "so");
    const marks = el("g", {}, f.svg), hits = el("g", {}, f.svg);
    for (const n of [...net.nodes].sort((a, b) => a.commits - b.commits)) {
      const dot = el("circle", { cx: px(n.x), cy: py(n.y), r: radius(n).toFixed(1), class: `${cls(n)} ring` }, marks);
      const hit = el("circle", { cx: px(n.x), cy: py(n.y), r: Math.max(12, radius(n) + 4), class: "hit" }, hits);
      bindTip(hit, () => [n.id, [
        { value: fmt.format(n.commits), label: "commits, last 12 months" },
        { value: n.community != null && n.community < 3 ? `Community ${n.community + 1}` : "Other", label: "" },
        ...(n.core ? [{ value: "Core", label: "part of the 80% group" }] : []),
      ]], dot);
    }
    // Label the people outside the main group, if any.
    const loose = net.nodes.filter((m) => !m.main);
    if (loose.length && loose.length < net.nodes.length) {
      const top = Math.min(...loose.map((m) => py(m.y)));
      label(f.svg, f.x0, top - 12, "Not connected to the main group", "tick");
    }
    // Name the core, biggest first: try right, left, above, below; skip if
    // every spot collides with an earlier label.
    const placed = [];
    for (const n of net.nodes.filter((m) => m.core).sort((a, b) => b.commits - a.commits)) {
      const r = radius(n), w = n.id.length * CHAR_W, cx = px(n.x), cy = py(n.y);
      const spots = [[cx + r + 4, cy + 4, "start"], [cx - r - 4, cy + 4, "end"],
        [cx, cy - r - 5, "middle"], [cx, cy + r + 13, "middle"]];
      for (const [x, y, anchor] of spots) {
        const x0 = anchor === "start" ? x : anchor === "end" ? x - w : x - w / 2;
        const box = { x0, x1: x0 + w, y0: y - 12, y1: y + 3 };
        if (box.x0 < 0 || box.x1 > f.width || box.y0 < 0 || box.y1 > f.height) continue;
        if (placed.some((p) => box.x0 < p.x1 && box.x1 > p.x0 && box.y0 < p.y1 && box.y1 > p.y0)) continue;
        placed.push(box);
        label(f.svg, x, y, n.id, "label halo", anchor);
        break;
      }
      if (placed.length >= 12) break;
    }
  }

  function sparkline(div) {
    const vals = data.timeline.map((r) => r[div.dataset.spark]);
    if (vals.length < 2) return;
    const w = Math.max(100, Math.floor(div.clientWidth)), h = 30;
    const max = Math.max(...vals), min = Math.min(...vals, 0);
    const x = (i) => 2 + (i / (vals.length - 1)) * (w - 8);
    const y = (v) => h - 4 - ((v - min) / (max - min || 1)) * (h - 8);
    const svg = el("svg", { viewBox: `0 0 ${w} ${h}`, width: w, height: h });
    div.replaceChildren(svg);
    el("path", { d: vals.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(""), class: "line" }, svg);
    el("circle", { cx: x(vals.length - 1), cy: y(vals[vals.length - 1]), r: 3, class: "s1" }, svg);
  }

  const charts = [
    ["chart-activity", activityChart],
    ["chart-truck", (f) => lineChart(f, "truckFactor", "truck factor")],
    ["chart-core", (f) => lineChart(f, "core80", "people making 80% of commits")],
    ["chart-network", networkChart],
    ["chart-cohorts", cohortChart],
    ["chart-ties", (f) => dotPlot(f, data.ties)],
    ["chart-peers", (f) => dotPlot(f, data.peers)],
  ];

  function render() {
    hideTip();
    for (const [id, draw] of charts) {
      const fig = document.getElementById(id);
      if (fig) draw(fig);
    }
    document.querySelectorAll("[data-spark]").forEach(sparkline);
  }

  const main = document.querySelector("main");
  let lastWidth = -1;
  new ResizeObserver(() => {
    if (main.clientWidth !== lastWidth) {
      lastWidth = main.clientWidth;
      render();
    }
  }).observe(main);
})();
