/*
 * Retro Avatar — TP 3 (frontend)
 *
 * This file does NOT need to be modified: it consumes the API defined in the assignment.
 *
 * Where it looks for the API:
 *   - served by the backend (http://localhost:8765) → same origin;
 *   - opened as a file (file://) → http://localhost:8765;
 *   - for any other case, add ?api=http://host:port to the URL (it is remembered).
 */

"use strict";

const API_BASE = (() => {
  try {
    const param = new URLSearchParams(location.search).get("api");
    if (param) localStorage.setItem("apiBase", param);
    const saved = param || localStorage.getItem("apiBase");
    if (saved) return saved.replace(/\/$/, "");
  } catch { /* storage blocked */ }
  return location.protocol.startsWith("http") ? "" : "http://localhost:8765";
})();

/* ------------------------------------------------------------------------ */
/* Options (must match the backend)                                          */
/* ------------------------------------------------------------------------ */

const DEFAULT_OPTIONS = { palette: "gameboy", pixels: 32, dithering: false, frame: 0 };

// Steps that round the colors to the palette: from them on, no step may add colors.
const QUANTIZERS = new Set(["palette_map", "floyd_steinberg"]);

/* ------------------------------------------------------------------------ */
/* State                                                                     */
/* ------------------------------------------------------------------------ */

const state = {
  palettes: [],      // GET /api/palettes
  source: null,      // photo in use: { name, file, url }
  options: { ...DEFAULT_OPTIONS },
  result: null,      // AvatarStepsOut of the last run
  error: null,       // ApiError of the last run
  selected: null,    // index in result.steps of the image on display (null = the last one)
  busy: false,
  again: false,      // the options changed while busy: run once more at the end
  camera: null,      // MediaStream while the camera is open
};

const $ = (sel) => document.querySelector(sel);
const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "style") node.style.cssText = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (v === true) node.setAttribute(k, "");
    else if (v !== false && v != null) node.setAttribute(k, v);
  }
  for (const c of children.flat(Infinity)) if (c != null) node.append(c);
  return node;
};

/* ------------------------------------------------------------------------ */
/* HTTP client                                                               */
/* ------------------------------------------------------------------------ */

class ApiError extends Error {
  constructor(status, code, title, message) {
    super(message);
    this.status = status;
    this.code = code;
    this.title = title;
  }
}

function errorMessage(status, body) {
  const detail = body && body.detail !== undefined ? body.detail : body;
  if (detail && typeof detail === "object" && !Array.isArray(detail) && detail.message) return detail.message;
  if (typeof detail === "string" && detail) return detail;
  if (Array.isArray(detail)) {
    // FastAPI validation errors (422)
    return detail.map((e) => `${(e.loc || []).filter((p) => p !== "body").join(".") || "request"}: ${e.msg}`).join(" · ");
  }
  return `The server responded ${status}.`;
}

function errorTitle(status, code) {
  if (code === "PHOTO_TOO_SMALL") return "Photo too small";
  if (code === "STEP_FAILED") return "A step failed";
  if (code === "UNSUPPORTED_FORMAT") return "Unsupported format";
  if (code === "INVALID_FILE") return "Invalid file";
  if (status === 0) return "No connection to the server";
  if (status === 404) return "Not found";
  if (status === 400 || status === 422) return "Invalid request";
  if (status === 413) return "File too large";
  if (status >= 500) return "Server error";
  return `Error ${status}`;
}

async function api(method, path, { formData } = {}) {
  let response;
  try {
    response = await fetch(API_BASE + path, { method, body: formData });
  } catch {
    const msg = `Could not connect to ${API_BASE || location.origin}. Is the backend running?`;
    throw new ApiError(0, null, errorTitle(0), msg);
  }

  const text = await response.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = text; }

  if (!response.ok) {
    const code = body?.detail?.code ?? null;
    throw new ApiError(response.status, code, errorTitle(response.status, code), errorMessage(response.status, body));
  }
  return body;
}

/* ------------------------------------------------------------------------ */
/* Notifications                                                             */
/* ------------------------------------------------------------------------ */

function toast(kind, title, message) {
  const node = el("div", { class: `toast ${kind}`, role: "status" },
    el("div", {}, el("strong", {}, title), message ? el("p", {}, message) : null));
  const container = $("#toasts");
  container.append(node);
  while (container.children.length > 3) container.firstElementChild.remove();
  setTimeout(() => {
    node.classList.add("leaving");
    setTimeout(() => node.remove(), 250);
  }, kind === "ok" ? 3000 : 6000);
}

/* ------------------------------------------------------------------------ */
/* Server and palettes                                                       */
/* ------------------------------------------------------------------------ */

async function checkServer() {
  const pill = $("#server-status");
  try {
    const r = await fetch(API_BASE + "/api/health");
    if (!r.ok) throw new Error();
    pill.dataset.status = "ok";
    pill.querySelector(".status-text").textContent = "Server connected";
  } catch {
    pill.dataset.status = "error";
    pill.querySelector(".status-text").textContent = "Server disconnected";
  }
}

async function loadPalettes() {
  try {
    state.palettes = await api("GET", "/api/palettes");
  } catch (err) {
    $("#palettes").replaceChildren(el("div", { class: "notice notice-err" }, el("strong", {}, err.title + ". "), err.message));
    return;
  }
  if (!state.palettes.some((p) => p.name === state.options.palette)) state.options.palette = state.palettes[0]?.name;
  renderPalettes();
}

function renderPalettes() {
  $("#palettes").replaceChildren(...state.palettes.map((p) => el("label", { class: "palette-option" },
    el("input", {
      type: "radio", name: "palette", value: p.name, checked: p.name === state.options.palette,
      onchange: () => setOption("palette", p.name),
    }),
    el("span", { class: "palette-name" }, p.label),
    el("span", { class: "palette-kind" }, `${p.colors.length} colors${p.monochrome ? " · ramp" : ""}`),
    el("span", { class: "swatches", "aria-hidden": "true" }, p.colors.map((c) => el("span", { style: `background:${c}` }))),
  )));
}

/* ------------------------------------------------------------------------ */
/* The photo: upload, camera or test image                                   */
/* ------------------------------------------------------------------------ */

const FORMATS = ["image/png", "image/jpeg", "image/webp", "image/bmp"];
const MAX_BYTES = 10 * 1024 * 1024;

function useFile(file) {
  if (!file) return;
  if (!FORMATS.includes(file.type)) {
    toast("err", "Unsupported format", `${file.name} (${file.type || "unknown"}). Use PNG, JPG, WEBP or BMP.`);
    return;
  }
  if (file.size > MAX_BYTES) {
    toast("err", "File too large", "The maximum is 10 MB.");
    return;
  }
  if (state.source) URL.revokeObjectURL(state.source.url);
  state.source = { name: file.name, file, url: URL.createObjectURL(file) };
  state.result = null;
  state.error = null;
  state.selected = null;
  renderSource();
  render();
  run();
}

function renderSource() {
  const source = state.source;
  $("#source").hidden = !source;
  if (!source) return;
  const img = $("#source-img");
  img.onload = () => { $("#source-meta").textContent = `${source.name} · ${img.naturalWidth}×${img.naturalHeight}`; };
  img.src = source.url;
  img.alt = source.name;
  $("#source-meta").textContent = source.name;
}

async function openCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    toast("warn", "No camera", "This browser cannot use the camera here (it needs localhost or https).");
    return;
  }
  try {
    state.camera = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: { ideal: 1280 } }, audio: false });
  } catch (err) {
    toast("warn", "No camera", err.name === "NotAllowedError" ? "Permission to use the camera was denied." : "No camera was found.");
    return;
  }
  $("#camera-video").srcObject = state.camera;
  $("#camera").hidden = false;
}

function closeCamera() {
  state.camera?.getTracks().forEach((track) => track.stop());
  state.camera = null;
  $("#camera-video").srcObject = null;
  $("#camera").hidden = true;
}

function capture() {
  const video = $("#camera-video");
  if (!video.videoWidth) return;
  const canvas = el("canvas", { width: video.videoWidth, height: video.videoHeight });
  const ctx = canvas.getContext("2d");
  ctx.translate(canvas.width, 0);
  ctx.scale(-1, 1); // the same as the mirrored preview
  ctx.drawImage(video, 0, 0);
  closeCamera();
  canvas.toBlob((blob) => blob && useFile(new File([blob], "selfie.png", { type: "image/png" })), "image/png");
}

// Public domain portraits, for those without a photo at hand (credits in README.md).
const SAMPLES = ["samples/vermeer.jpg", "samples/einstein.jpg"];
let nextSample = 0;

async function loadSample() {
  const path = SAMPLES[nextSample];
  nextSample = (nextSample + 1) % SAMPLES.length;
  try {
    // Served next to this page by the backend (also when the page is opened as a file).
    const r = await fetch(`${API_BASE}/${path}`);
    if (!r.ok) throw new Error(`GET /${path} responded ${r.status}`);
    const blob = await r.blob();
    useFile(new File([blob], path.split("/").pop(), { type: blob.type || "image/jpeg" }));
  } catch (err) {
    toast("err", "Could not load the test image", String(err.message || err));
  }
}

/* ------------------------------------------------------------------------ */
/* Making the avatar                                                         */
/* ------------------------------------------------------------------------ */

let timer = null;

function scheduleRun() {
  if (!state.source) return;
  clearTimeout(timer);
  timer = setTimeout(run, 250);
}

async function run() {
  if (!state.source) return;
  if (state.busy) { state.again = true; return; }
  state.busy = true;
  state.again = false;
  render();

  const keep = state.selected != null ? state.result?.steps[state.selected]?.name : null;
  try {
    const fd = new FormData();
    fd.append("file", state.source.file, state.source.name);
    for (const [key, value] of Object.entries(state.options)) fd.append(key, String(value));
    const result = await api("POST", "/api/avatar/steps", { formData: fd });
    state.result = result;
    state.error = null;
    // Keep showing the step that was selected, if it still has an image.
    const index = keep ? result.steps.findIndex((s) => s.name === keep && s.image) : -1;
    state.selected = index >= 0 ? index : null;
  } catch (err) {
    if (!(err instanceof ApiError)) console.error(err);
    state.error = err instanceof ApiError ? err : new ApiError(0, null, "Unexpected error", String(err.message || err));
    state.result = null;
  } finally {
    state.busy = false;
    render();
    if (state.again) run();
  }
}

/* ------------------------------------------------------------------------ */
/* View                                                                      */
/* ------------------------------------------------------------------------ */

const STATUS_TAG = { pending: "TODO", blocked: "…", failed: "ERROR" };
const STATUS_TEXT = {
  pending: "Not implemented yet",
  blocked: "Waiting for an earlier step",
  failed: "Failed: read the message above",
};

const stepTitle = (step) => (step.number ? `Step ${step.number} · ${step.label}` : step.label);
const formatColors = (n) => (n === 1 ? "1 color" : n >= 10000 ? `${Math.round(n / 1000)}k colors` : `${n} colors`);

function lastImageIndex(result) {
  for (let i = result.steps.length - 1; i >= 0; i--) if (result.steps[i].image) return i;
  return -1;
}

const shownIndex = () => state.selected ?? lastImageIndex(state.result);

/** Steps that come after the palette and have more colors than it: something is wrong there. */
function colorProblems(result) {
  const bad = new Set();
  const first = result.steps.findIndex((s) => QUANTIZERS.has(s.name) && s.status === "done");
  if (first < 0) return bad;
  const allowed = result.palette.colors.length;
  result.steps.forEach((s, i) => { if (i >= first && s.image && s.colors > allowed) bad.add(i); });
  return bad;
}

function problemBox(err) {
  const warn = err.code === "PHOTO_TOO_SMALL";
  return el("div", { class: `problem${warn ? " warn" : ""}`, role: "alert" },
    el("strong", {}, err.title), el("p", {}, err.message));
}

function renderNotice(result) {
  const notice = $("#view-notice");
  const steps = result.steps.slice(1);
  const failed = steps.find((s) => s.status === "failed");
  const todo = steps.filter((s) => s.status === "pending");
  const bad = [...colorProblems(result)].map((i) => result.steps[i]);
  const palette = result.palette;
  let kind;
  let content;

  if (failed) {
    kind = "err";
    content = [el("strong", {}, `${stepTitle(failed)} failed. `), failed.message];
  } else if (bad.length) {
    kind = "err";
    content = [el("strong", {}, `${bad[0].class_name} returned ${bad[0].colors} colors, `),
      `but ${palette.label} has ${palette.colors.length}: after the palette, no step may add colors.`];
  } else if (todo.length) {
    const waiting = steps.filter((s) => s.status === "blocked" && s.number != null);
    const left = todo.length + waiting.length;
    const names = (list) => list.map((s, i) => [i ? ", " : "", el("code", {}, s.class_name), ` (${s.number})`]);
    kind = "warn";
    content = [el("strong", {}, `${left} step${left > 1 ? "s" : ""} to go.`),
      el("ul", {},
        el("li", {}, "Not implemented yet: ", names(todo)),
        waiting.length ? el("li", {}, "Waiting for them: ", names(waiting)) : null)];
  } else if (result.complete) {
    const final = result.steps[result.steps.length - 1];
    kind = "ok";
    content = [el("strong", {}, "Done! "),
      `${final.width}×${final.height}, ${final.colors} of the ${palette.colors.length} colors of ${palette.label}.`];
  }
  notice.hidden = !kind;
  if (kind) {
    notice.className = `notice notice-${kind}`;
    notice.replaceChildren(...content);
  }
}

function renderView() {
  const frame = $("#view-frame");
  frame.classList.toggle("loading", state.busy);
  $("#view-notice").hidden = true;
  $("#view-actions").hidden = true;
  $("#view-label").textContent = "Avatar";
  $("#view-meta").textContent = "";

  if (state.error) {
    frame.replaceChildren(problemBox(state.error));
    return;
  }
  const result = state.result;
  if (!result) {
    const text = state.source ? "Making your avatar…" : "Upload a photo to get started";
    frame.replaceChildren(el("div", { class: "empty" }, text));
    return;
  }

  const last = lastImageIndex(result);
  const index = shownIndex();
  const step = result.steps[index];
  const isAvatar = index === last && result.complete;
  frame.replaceChildren(el("img", { src: step.image, alt: stepTitle(step) }));
  $("#view-label").textContent = isAvatar ? "Avatar" : stepTitle(step);
  $("#view-meta").textContent = `${step.width}×${step.height} · ${formatColors(step.colors)}`;
  renderNotice(result);

  const download = $("#btn-download");
  download.hidden = !result.complete;
  download.href = result.steps[last].image;
  download.download = `avatar-${result.options.palette}-${result.options.pixels}px.png`;
  $("#btn-show-last").hidden = index === last;
  $("#view-actions").hidden = download.hidden && $("#btn-show-last").hidden;
}

function stepCard(step, index, active, tooManyColors) {
  const number = step.status === "input" ? "▸" : step.number ?? "·";
  const kind = step.status === "input" ? "input" : `${step.class_name}${step.number == null ? " · given" : ""}`;
  const detail = step.image
    ? `${step.width}×${step.height} · ${formatColors(step.colors)}`
    : STATUS_TEXT[step.status];
  return el("button", {
    type: "button",
    class: `step${active ? " active" : ""}${tooManyColors ? " too-many-colors" : ""}`,
    "data-status": step.status,
    disabled: !step.image,
    title: step.message || stepTitle(step),
    onclick: () => select(index),
  },
    el("span", { class: "step-head" },
      el("span", { class: "step-number" }, String(number)),
      el("span", { class: "step-label" }, step.label)),
    el("span", { class: "step-thumb" },
      step.image ? el("img", { src: step.image, alt: "" }) : el("span", { class: "todo" }, STATUS_TAG[step.status])),
    el("span", { class: "step-class" }, kind),
    el("span", { class: "step-detail" }, detail));
}

function renderSteps() {
  const list = $("#steps");
  const result = state.result;
  if (!result) {
    $("#pipeline-progress").textContent = "";
    list.replaceChildren(el("li", { class: "notice" }, "Each step of the pipeline will show up here, with its result."));
    return;
  }
  const own = result.steps.filter((s) => s.number != null);
  const done = own.filter((s) => s.status === "done").length;
  $("#pipeline-progress").textContent = `${done} of ${own.length} steps of yours done`;
  const shown = shownIndex();
  const bad = colorProblems(result);
  list.replaceChildren(...result.steps.map((step, i) => el("li", {}, stepCard(step, i, i === shown, bad.has(i)))));
}

function select(index) {
  state.selected = index === lastImageIndex(state.result) ? null : index;
  renderView();
  renderSteps();
}

function renderButtons() {
  const button = $("#btn-make");
  button.disabled = state.busy || !state.source;
  button.textContent = state.busy ? "Making…" : "Make avatar";
  $("#dropzone").classList.toggle("busy", state.busy);
}

function render() {
  renderView();
  renderSteps();
  renderButtons();
}

/* ------------------------------------------------------------------------ */
/* Options                                                                   */
/* ------------------------------------------------------------------------ */

function setOption(key, value) {
  state.options[key] = value;
  renderOptions();
  scheduleRun();
}

function renderOptions() {
  const o = state.options;
  for (const button of document.querySelectorAll("#pixels button")) {
    button.setAttribute("aria-pressed", String(Number(button.dataset.value) === o.pixels));
  }
  for (const input of document.querySelectorAll("#palettes input")) input.checked = input.value === o.palette;
  $("#dithering").checked = o.dithering;
  $("#frame").value = o.frame;
  $("#frame-value").textContent = o.frame === 0 ? "off" : `${o.frame} px`;
  renderCurl();
}

function renderCurl() {
  const o = state.options;
  const base = API_BASE || location.origin;
  $("#curl").textContent = [
    `curl -F "file=@photo.jpg" \\`,
    `     -F "palette=${o.palette}" -F "pixels=${o.pixels}" \\`,
    `     -F "dithering=${o.dithering}" -F "frame=${o.frame}" \\`,
    `     ${base}/api/avatar -o avatar.png`,
  ].join("\n");
}

/* ------------------------------------------------------------------------ */
/* Events                                                                    */
/* ------------------------------------------------------------------------ */

function bindEvents() {
  $("#file-input").addEventListener("change", (e) => {
    useFile(e.target.files[0]);
    e.target.value = "";
  });

  const zone = $("#dropzone");
  ["dragenter", "dragover"].forEach((t) => zone.addEventListener(t, (e) => { e.preventDefault(); zone.classList.add("dragging"); }));
  ["dragleave", "drop"].forEach((t) => zone.addEventListener(t, () => zone.classList.remove("dragging")));
  zone.addEventListener("drop", (e) => { e.preventDefault(); useFile(e.dataTransfer.files[0]); });

  $("#btn-camera").addEventListener("click", openCamera);
  $("#btn-capture").addEventListener("click", capture);
  $("#btn-camera-cancel").addEventListener("click", closeCamera);
  $("#btn-sample").addEventListener("click", loadSample);

  for (const button of document.querySelectorAll("#pixels button")) {
    button.addEventListener("click", () => setOption("pixels", Number(button.dataset.value)));
  }
  $("#dithering").addEventListener("change", (e) => setOption("dithering", e.target.checked));
  $("#frame").addEventListener("input", (e) => setOption("frame", Number(e.target.value)));

  $("#btn-reset").addEventListener("click", () => {
    state.options = { ...DEFAULT_OPTIONS };
    renderOptions();
    scheduleRun();
  });
  $("#options-form").addEventListener("submit", (e) => { e.preventDefault(); run(); });
  $("#btn-show-last").addEventListener("click", () => select(lastImageIndex(state.result)));
}

function init() {
  $("#link-docs").href = (API_BASE || "") + "/docs";
  renderOptions();
  render();
  bindEvents();
  checkServer();
  loadPalettes();
}

init();
