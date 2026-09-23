/*
 * Image Editor — TP 1 (frontend)
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
/* Operation catalog (must match the backend schemas)                        */
/* ------------------------------------------------------------------------ */

const OPERATIONS = [
  {
    id: "brightness",
    name: "Brightness",
    lib: "PIL.ImageEnhance.Brightness",
    description: "Lightens or darkens the image. 1.0 leaves the image unchanged, 0 turns it black.",
    params: [{ name: "factor", label: "Factor", type: "range", min: 0, max: 3, step: 0.05, def: 1 }],
  },
  {
    id: "contrast",
    name: "Contrast",
    lib: "PIL.ImageEnhance.Contrast",
    description: "Increases or reduces the difference between light and dark areas. 1.0 = unchanged.",
    params: [{ name: "factor", label: "Factor", type: "range", min: 0, max: 3, step: 0.05, def: 1 }],
  },
  {
    id: "saturation",
    name: "Saturation",
    lib: "PIL.ImageEnhance.Color",
    description: "Color intensity. 0 = black and white, 1.0 = unchanged, >1 = more vivid colors.",
    params: [{ name: "factor", label: "Factor", type: "range", min: 0, max: 3, step: 0.05, def: 1 }],
  },
  {
    id: "sharpness",
    name: "Sharpness",
    lib: "PIL.ImageEnhance.Sharpness",
    description: "Enhances fine details. <1 smooths, 1.0 = unchanged, >1 sharpens.",
    params: [{ name: "factor", label: "Factor", type: "range", min: 0, max: 5, step: 0.1, def: 1 }],
  },
  {
    id: "grayscale",
    name: "Grayscale",
    lib: "cv2.cvtColor / ImageOps.grayscale",
    description: "Converts the image to shades of gray. Takes no parameters.",
    params: [],
  },
  {
    id: "blur",
    name: "Blur",
    lib: "cv2.GaussianBlur / medianBlur / blur",
    description: "Smooths the image with a filter. The kernel size must be odd.",
    params: [
      {
        name: "method", label: "Method", type: "segmented", def: "gaussian",
        options: [["gaussian", "Gaussian"], ["median", "Median"], ["average", "Average"]],
      },
      { name: "kernel_size", label: "Kernel size", type: "range", min: 1, max: 51, step: 2, def: 5, suffix: " px" },
    ],
  },
  {
    id: "edges",
    name: "Edges",
    lib: "cv2.Canny",
    description: "Detects edges with the Canny algorithm. The lower threshold must be less than the upper one.",
    params: [
      { name: "lower_threshold", label: "Lower threshold", type: "range", min: 0, max: 255, step: 1, def: 100 },
      { name: "upper_threshold", label: "Upper threshold", type: "range", min: 0, max: 255, step: 1, def: 200 },
    ],
  },
  {
    id: "rotation",
    name: "Rotation",
    lib: "PIL.Image.rotate",
    description: "Rotates the image counterclockwise. With \"expand\" the canvas grows to avoid cropping.",
    params: [
      { name: "angle", label: "Angle", type: "range", min: -180, max: 180, step: 1, def: 90, suffix: "°" },
      { name: "expand", label: "Expand canvas", type: "check", def: true },
    ],
  },
  {
    id: "mirror",
    name: "Mirror",
    lib: "PIL.ImageOps.mirror / flip",
    description: "Flips the image horizontally or vertically.",
    params: [
      {
        name: "direction", label: "Direction", type: "segmented", def: "horizontal",
        options: [["horizontal", "Horizontal"], ["vertical", "Vertical"]],
      },
    ],
  },
  {
    id: "resize",
    name: "Resize",
    lib: "PIL.Image.resize / cv2.resize",
    description: "Changes the size in pixels. If the aspect ratio is kept, the height is computed from the width.",
    params: [
      { name: "width", label: "Width", type: "number", min: 1, max: 8000, def: 800, suffix: " px" },
      { name: "height", label: "Height", type: "number", min: 1, max: 8000, def: null, optional: true, suffix: " px",
        help: "Ignored if \"Keep aspect ratio\" is enabled." },
      { name: "keep_aspect_ratio", label: "Keep aspect ratio", type: "check", def: true },
    ],
  },
];

/* ------------------------------------------------------------------------ */
/* State                                                                     */
/* ------------------------------------------------------------------------ */

const state = {
  images: [],          // list returned by GET /api/images
  current: null,       // ImageOut (or {local: true, ...} if it could not be uploaded)
  result: null,        // ImageOut returned by the last operation
  galleryError: null,  // ApiError if the listing failed
  operation: OPERATIONS[0],
  values: {},          // chosen parameters, by operation id
  busy: false,
};

const $ = (sel) => document.querySelector(sel);
const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "dataset") Object.assign(node.dataset, v);
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (v === true) node.setAttribute(k, "");
    else if (v !== false && v != null) node.setAttribute(k, v);
  }
  for (const c of children.flat()) if (c != null) node.append(c);
  return node;
};

/* ------------------------------------------------------------------------ */
/* HTTP client                                                               */
/* ------------------------------------------------------------------------ */

class ApiError extends Error {
  constructor(status, title, message) {
    super(message);
    this.status = status;
    this.title = title;
  }
  get notImplemented() { return this.status === 501; }
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

function errorTitle(status) {
  if (status === 0) return "No connection to the server";
  if (status === 501) return "Not implemented yet";
  if (status === 404) return "Not found";
  if (status === 400 || status === 422) return "Invalid parameters";
  if (status === 413) return "File too large";
  if (status >= 500) return "Server error";
  return `Error ${status}`;
}

async function api(method, path, { json, formData } = {}) {
  const options = { method, headers: {} };
  if (json !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(json);
  } else if (formData) {
    options.body = formData;
  }

  let response;
  try {
    response = await fetch(API_BASE + path, options);
  } catch {
    const msg = `Could not connect to ${API_BASE || location.origin}. Is the backend running?`;
    throw new ApiError(0, errorTitle(0), msg);
  }

  const text = await response.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = text; }

  if (!response.ok) {
    const msg = errorMessage(response.status, body);
    throw new ApiError(response.status, errorTitle(response.status), msg);
  }
  return body;
}

const absoluteUrl = (url) => (/^(https?:|blob:|data:)/.test(url) ? url : API_BASE + url);

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

function toastError(err) {
  if (err instanceof ApiError) {
    toast(err.notImplemented ? "warn" : "err", err.title, err.message);
  } else {
    console.error(err);
    toast("err", "Unexpected error", String(err.message || err));
  }
}

/* ------------------------------------------------------------------------ */
/* Server                                                                    */
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

/* ------------------------------------------------------------------------ */
/* Gallery                                                                   */
/* ------------------------------------------------------------------------ */

async function loadGallery() {
  try {
    state.images = await api("GET", "/api/images");
    state.galleryError = null;
  } catch (err) {
    state.images = [];
    state.galleryError = err;
  }
  renderGallery();
}

function renderGallery() {
  const gallery = $("#gallery");
  const error = state.galleryError;
  if (error) {
    const cls = error.notImplemented ? "notice notice-warn" : "notice notice-err";
    gallery.replaceChildren(el("div", { class: cls }, el("strong", {}, error.title + ". "), error.message));
    return;
  }
  if (!state.images.length) {
    gallery.replaceChildren(el("div", { class: "notice" }, "No images saved yet."));
    return;
  }
  gallery.replaceChildren(...state.images.map((img) => {
    const active = state.current && !state.current.local && state.current.id === img.id;
    const badge = img.operation
      ? el("span", { class: "badge badge-op" }, operationName(img.operation))
      : el("span", { class: "badge" }, "Original");
    return el("div", {
      class: `item${active ? " active" : ""}`, role: "button", tabindex: "0",
      title: img.original_name,
      onclick: () => selectImage(img),
      onkeydown: (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectImage(img); } },
    },
      el("img", { src: absoluteUrl(img.url), alt: "", loading: "lazy" }),
      el("div", { class: "item-info" },
        el("div", { class: "item-name" }, `#${img.id} · ${img.original_name}`),
        el("div", { class: "item-detail" }, badge, ` ${img.width}×${img.height}`)),
      el("button", {
        class: "item-delete", title: "Delete", "aria-label": `Delete image ${img.id}`,
        onclick: (e) => { e.stopPropagation(); deleteImage(img); },
      }, "×"),
    );
  }));
}

function operationName(id) {
  return OPERATIONS.find((o) => o.id === id || o.id === String(id).replace(/_/g, "-"))?.name ?? id;
}

async function deleteImage(img) {
  try {
    await api("DELETE", `/api/images/${img.id}`);
    toast("ok", "Image deleted", `#${img.id} · ${img.original_name}`);
    if (state.current?.id === img.id) setCurrent(null);
    if (state.result?.id === img.id) setResult(null);
    await loadGallery();
  } catch (err) {
    toastError(err);
  }
}

async function selectImage(img) {
  // Requests the updated version from the server (exercises GET /api/images/{id}).
  try {
    setCurrent(await api("GET", `/api/images/${img.id}`));
  } catch (err) {
    toastError(err);
    setCurrent(img);
  }
  setResult(null);
}

/* ------------------------------------------------------------------------ */
/* Upload                                                                    */
/* ------------------------------------------------------------------------ */

const FORMATS = ["image/png", "image/jpeg", "image/webp", "image/bmp"];
const MAX_BYTES = 10 * 1024 * 1024;

async function uploadFile(file) {
  if (!file) return;
  if (!FORMATS.includes(file.type)) {
    toast("err", "Unsupported format", `${file.name} (${file.type || "unknown"}). Use PNG, JPG, WEBP or BMP.`);
    return;
  }
  if (file.size > MAX_BYTES) {
    toast("err", "File too large", "The maximum is 10 MB.");
    return;
  }

  const zone = $("#dropzone");
  zone.classList.add("busy");
  const fd = new FormData();
  fd.append("file", file);
  try {
    const image = await api("POST", "/api/images", { formData: fd });
    toast("ok", "Image uploaded", `#${image.id} · ${image.original_name}`);
    setCurrent(image);
    setResult(null);
    await loadGallery();
  } catch (err) {
    toastError(err);
    // A local preview is shown so the user can see what they tried to upload.
    const url = URL.createObjectURL(file);
    const dims = await measure(url);
    setCurrent({ local: true, id: null, url, original_name: file.name, width: dims.w, height: dims.h,
      format: file.type.split("/")[1].toUpperCase(), size_bytes: file.size });
    setResult(null);
  } finally {
    zone.classList.remove("busy");
    $("#file-input").value = "";
  }
}

function measure(url) {
  return new Promise((ok) => {
    const img = new Image();
    img.onload = () => ok({ w: img.naturalWidth, h: img.naturalHeight });
    img.onerror = () => ok({ w: 0, h: 0 });
    img.src = url;
  });
}

/* ------------------------------------------------------------------------ */
/* View                                                                      */
/* ------------------------------------------------------------------------ */

const formatBytes = (b) => (b >= 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`);

function metaText(img) {
  const parts = [];
  if (img.id != null) parts.push(`#${img.id}`);
  if (img.width) parts.push(`${img.width}×${img.height}`);
  if (img.format) parts.push(img.format);
  if (img.size_bytes) parts.push(formatBytes(img.size_bytes));
  return parts.join(" · ");
}

function paintFrame(frame, img, emptyText, stamp) {
  frame.classList.remove("loading");
  if (!img) {
    frame.replaceChildren(el("div", { class: "empty" }, emptyText));
    return;
  }
  const children = [el("img", { src: absoluteUrl(img.url), alt: img.original_name || "image" })];
  if (stamp) children.push(el("span", { class: `badge stamp ${stamp.cls}` }, stamp.text));
  frame.replaceChildren(...children);
}

function setCurrent(img) {
  if (state.current?.local && state.current.url !== img?.url) URL.revokeObjectURL(state.current.url);
  state.current = img;
  paintFrame($("#current-frame"), img, "Upload or pick an image to get started",
    img?.local ? { cls: "badge-warn", text: "Local preview · not on the server" }
      : img?.operation ? { cls: "badge-op", text: operationName(img.operation) } : null);
  $("#current-meta").textContent = img ? metaText(img) : "";

  // Suggest the current width for resize.
  if (img?.width) {
    state.values["resize"] = { ...valuesOf(OPERATIONS.find((o) => o.id === "resize")), width: img.width };
    if (state.operation.id === "resize") renderForm();
  }
  renderGallery();
  updateApplyButton();
}

function setResult(img) {
  state.result = img;
  paintFrame($("#result-frame"), img, "Apply an edit to see the result",
    img?.operation ? { cls: "badge-op", text: operationName(img.operation) } : null);
  $("#result-meta").textContent = img ? metaText(img) : "";
  $("#result-actions").hidden = !img;
  if (img) {
    const a = $("#btn-download");
    a.href = absoluteUrl(img.url);
    a.download = `${img.operation || "image"}-${img.id}.${(img.format || "png").toLowerCase()}`;
  }
}

/* ------------------------------------------------------------------------ */
/* Operations                                                                */
/* ------------------------------------------------------------------------ */

function valuesOf(op) {
  if (!state.values[op.id]) {
    state.values[op.id] = Object.fromEntries(op.params.map((p) => [p.name, p.def]));
  }
  return state.values[op.id];
}

function renderOperationList() {
  $("#operations").replaceChildren(...OPERATIONS.map((op, i) =>
    el("button", {
      type: "button", class: "op", role: "option",
      "aria-selected": String(op.id === state.operation.id),
      onclick: () => { state.operation = op; renderOperationList(); renderForm(); },
    }, el("span", { class: "num" }, String(i + 1)), op.name)));
}

function formatValue(p, v) {
  if (v == null || v === "") return "—";
  const n = Number(v);
  const text = p.step && p.step < 1 ? n.toFixed(2) : String(n);
  return text + (p.suffix || "");
}

function renderField(op, p) {
  const values = valuesOf(op);
  const id = `field-${op.id}-${p.name}`;

  if (p.type === "range") {
    const output = el("span", { class: "value" }, formatValue(p, values[p.name]));
    return el("div", { class: "field" },
      el("label", { for: id }, p.label, output),
      el("input", {
        id, type: "range", min: p.min, max: p.max, step: p.step, value: values[p.name],
        oninput: (e) => { values[p.name] = Number(e.target.value); output.textContent = formatValue(p, values[p.name]); },
      }));
  }

  if (p.type === "number") {
    return el("div", { class: "field" },
      el("label", { for: id }, p.label + (p.optional ? " (optional)" : "")),
      el("input", {
        id, type: "number", min: p.min, max: p.max, step: 1, value: values[p.name] ?? "",
        placeholder: p.optional ? "automatic" : "",
        oninput: (e) => { values[p.name] = e.target.value === "" ? null : Number(e.target.value); },
      }),
      p.help ? el("div", { class: "help" }, p.help) : null);
  }

  if (p.type === "check") {
    return el("div", { class: "field field-check" },
      el("label", { for: id },
        el("input", {
          id, type: "checkbox", checked: Boolean(values[p.name]),
          onchange: (e) => { values[p.name] = e.target.checked; },
        }),
        p.label));
  }

  if (p.type === "segmented") {
    const group = el("div", { class: "segmented", role: "group", "aria-label": p.label });
    const paint = () => group.replaceChildren(...p.options.map(([value, text]) =>
      el("button", {
        type: "button", "aria-pressed": String(values[p.name] === value),
        onclick: () => { values[p.name] = value; paint(); },
      }, text)));
    paint();
    return el("div", { class: "field" }, el("label", {}, p.label), group);
  }

  throw new Error(`Unknown parameter type: ${p.type}`);
}

function renderForm() {
  const op = state.operation;
  $("#op-name").textContent = op.name;
  $("#op-lib").textContent = op.lib;
  $("#op-description").textContent = op.description;
  $("#op-fields").replaceChildren(...(op.params.length
    ? op.params.map((p) => renderField(op, p))
    : [el("p", { class: "no-parameters" }, "This operation has no parameters.")]));
  updateApplyButton();
}

function updateApplyButton() {
  const button = $("#btn-apply");
  button.disabled = state.busy || !state.current;
  button.textContent = state.busy ? "Applying…" : `Apply ${state.operation.name.toLowerCase()}`;
}

function operationBody(op) {
  if (!op.params.length) return undefined;
  const values = valuesOf(op);
  const body = {};
  for (const p of op.params) {
    const v = values[p.name];
    if (v === null && p.optional) continue;
    body[p.name] = v;
  }
  return body;
}

async function applyOperation(event) {
  event.preventDefault();
  const op = state.operation;
  if (!state.current) return;

  if (state.current.local) {
    toast("warn", "The image is not on the server",
      "Upload the image to the server before applying edits.");
    return;
  }

  state.busy = true;
  updateApplyButton();
  $("#result-frame").classList.add("loading");
  try {
    const result = await api("POST", `/api/images/${state.current.id}/${op.id}`, { json: operationBody(op) });
    setResult(result);
    toast("ok", `${op.name} applied`, `New image #${result.id}`);
    await loadGallery();
  } catch (err) {
    $("#result-frame").classList.remove("loading");
    toastError(err);
  } finally {
    state.busy = false;
    updateApplyButton();
  }
}

/* ------------------------------------------------------------------------ */
/* Events                                                                    */
/* ------------------------------------------------------------------------ */

function bindEvents() {
  $("#file-input").addEventListener("change", (e) => uploadFile(e.target.files[0]));

  const zone = $("#dropzone");
  ["dragenter", "dragover"].forEach((t) => zone.addEventListener(t, (e) => { e.preventDefault(); zone.classList.add("dragging"); }));
  ["dragleave", "drop"].forEach((t) => zone.addEventListener(t, () => zone.classList.remove("dragging")));
  zone.addEventListener("drop", (e) => { e.preventDefault(); uploadFile(e.dataTransfer.files[0]); });

  $("#btn-refresh").addEventListener("click", loadGallery);
  $("#operation-form").addEventListener("submit", applyOperation);
  $("#btn-reset").addEventListener("click", () => {
    delete state.values[state.operation.id];
    if (state.operation.id === "resize" && state.current?.width) {
      state.values.resize = { ...valuesOf(state.operation), width: state.current.width };
    }
    renderForm();
  });
  $("#btn-use-result").addEventListener("click", () => {
    const r = state.result;
    setResult(null);
    setCurrent(r);
  });
}

function init() {
  $("#link-docs").href = (API_BASE || "") + "/docs";
  renderOperationList();
  renderForm();
  bindEvents();
  checkServer();
  loadGallery();
}

init();
