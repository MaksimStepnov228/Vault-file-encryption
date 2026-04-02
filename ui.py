import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
import os
import json
from datetime import datetime

from crypto import encrypt_file, decrypt_file, safe_output_path, LARGE_FILE_THRESHOLD
from compress import compress_file, decompress_file, available_algorithms, read_metadata
from compress import ALGORITHMS as COMP_ALGORITHMS
import sys

# ── Optional drag-and-drop ────────────────────────────────────────────────────
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False
    TkinterDnD = None

# ── PyInstaller path helper ───────────────────────────────────────────────────
def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel)

def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# ── Colours ───────────────────────────────────────────────────────────────────
BG        = "#10182a"
SURFACE2  = "#1a2744"
SURFACE3  = "#203050"
INSET     = "#0d1525"
BORDER_LO = "#080e1a"
BORDER_HI = "#3a5080"
BORDER    = "#1e2e4a"
ACCENT_A  = "#2060d0"
ACCENT_B  = "#4a9aff"
ACCENT_C  = "#6ab8ff"
ACCENT_DIM= "#152a5a"
TEXT      = "#c8d8f0"
MUTED     = "#4e6a90"
MUTED2    = "#2a3e5e"
SUCCESS   = "#30c080"
DANGER    = "#e04455"
WARN      = "#e0952a"
WHITE     = "#e8f0ff"
HDR_A     = "#1e3060"
HDR_B     = "#162448"
HDR_C     = "#10182a"
DROP_BORDER_IDLE  = "#253a60"
DROP_BORDER_HOVER = "#4a9aff"
DROP_BG_IDLE      = "#0d1828"
DROP_BG_HOVER     = "#10244a"

FONT       = ("Tahoma", 9)
FONT_SM    = ("Tahoma", 8)
FONT_BOLD  = ("Tahoma", 9, "bold")
FONT_TITLE = ("Tahoma", 13, "bold")

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    r1,g1,b1 = int(c1[1:3],16),int(c1[3:5],16),int(c1[5:7],16)
    r2,g2,b2 = int(c2[1:3],16),int(c2[3:5],16),int(c2[5:7],16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))

def lerp3(c1, c2, c3, t):
    return lerp_color(c1,c2,t*2) if t<=0.5 else lerp_color(c2,c3,(t-0.5)*2)

def draw_v3(cv, x0, y0, x1, y1, c1, c2, c3):
    h = y1-y0
    for i in range(h): cv.create_line(x0,y0+i,x1,y0+i,fill=lerp3(c1,c2,c3,i/h))

def draw_hg(cv, x0, y0, x1, y1, c1, c2):
    w = x1-x0
    for i in range(w): cv.create_line(x0+i,y0,x0+i,y1,fill=lerp_color(c1,c2,i/w))

def mkframe(parent, bg=BG, **kw):
    return tk.Frame(parent, bg=bg, **kw)

def mklabel(parent, text="", var=None, color=TEXT, font=FONT, anchor="w", bg=BG, **kw):
    cfg = dict(bg=bg, fg=color, font=font, anchor=anchor)
    return tk.Label(parent, textvariable=var, **cfg, **kw) if var else \
           tk.Label(parent, text=text, **cfg, **kw)

def thin_divider(parent, pady=3):
    tk.Frame(parent, bg=BORDER_LO, height=1).pack(fill="x", pady=(pady,0))
    tk.Frame(parent, bg=BORDER_HI, height=1).pack(fill="x", pady=(0,pady))

def _fmt_size(n):
    if n < 1024:    return f"{n} B"
    if n < 1048576: return f"{n/1024:.1f} KB"
    return f"{n/1048576:.2f} MB"

def _clean_drop_path(raw):
    p = raw.strip()
    return p[1:-1] if p.startswith("{") and p.endswith("}") else p

class NavyEntry(tk.Entry):
    def __init__(self, parent, var, show="", **kw):
        super().__init__(parent, textvariable=var, show=show,
                         bg=INSET, fg=TEXT, insertbackground=ACCENT_C,
                         selectbackground=ACCENT_DIM, selectforeground=ACCENT_C,
                         relief="flat", font=FONT, highlightthickness=1,
                         highlightbackground=BORDER, highlightcolor=ACCENT_B,
                         bd=0, **kw)
        self.bind("<FocusIn>",  lambda e: self.config(highlightbackground=ACCENT_B))
        self.bind("<FocusOut>", lambda e: self.config(highlightbackground=BORDER))


class GradientButton(tk.Frame):
    def __init__(self, parent, text, command, width=120, height=24,
                 c1=ACCENT_A, c2=ACCENT_B):
        tk.Frame.__init__(self, parent, width=width, height=height,
                          bd=0, highlightthickness=0, bg=BG)
        self.pack_propagate(False)
        self._text, self._command = text, command
        self._c1, self._c2 = c1, c2
        self._bw, self._bh = width, height
        self._hover = self._pressed = False
        self._cv = tk.Canvas(self, width=width, height=height, bd=0,
                             highlightthickness=0, cursor="hand2", bg=BG)
        self._cv.pack(fill="both", expand=True)
        self._cv.bind("<Enter>",           lambda e: self._state(hover=True))
        self._cv.bind("<Leave>",           lambda e: self._state(hover=False, pressed=False))
        self._cv.bind("<ButtonPress-1>",   lambda e: self._state(pressed=True))
        self._cv.bind("<ButtonRelease-1>", lambda e: (self._state(pressed=False), command()))
        self.after(20, self._draw)

    def _state(self, **kw):
        for k, v in kw.items(): setattr(self, f"_{k}", v)
        self._draw()

    def _draw(self):
        cv = self._cv; cv.delete("all")
        w, h = self._bw, self._bh
        c1 = lerp_color(self._c1, WHITE, 0.08 if self._hover else 0)
        c2 = lerp_color(self._c2, WHITE, 0.12 if self._hover else 0)
        if self._pressed:
            c1 = lerp_color(c1, "#000000", 0.18)
            c2 = lerp_color(c2, "#000000", 0.12)
        draw_hg(cv, 0, 0, w, h, c1, c2)
        off = 1 if self._pressed else 0
        cv.create_text(w//2+off, h//2+off, text=self._text,
                       fill=WHITE, font=FONT_BOLD, anchor="center")

class SmoothProgressBar(tk.Canvas):
    def __init__(self, parent, variable, height=10, **kw):
        tk.Canvas.__init__(self, parent, height=height, bg=INSET, bd=0,
                           highlightthickness=1, highlightbackground=BORDER_LO, **kw)
        self._var, self._target, self._current = variable, 0.0, 0.0
        self._var.trace_add("write", self._on_var)
        self.bind("<Configure>", lambda e: self._draw())
        self._tick()

    def _on_var(self, *_):
        self._target = min(max(self._var.get(), 0), 1)

    def _tick(self):
        if abs(self._current - self._target) > 0.001:
            self._current += (self._target - self._current) * 0.15
        else:
            self._current = self._target
        self._draw()
        self.after(16, self._tick)

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 2: return
        fw = int(w * self._current)
        if fw > 1: draw_hg(self, 0, 0, fw, h, ACCENT_A, ACCENT_C)
        pct = int(self._current * 100)
        if pct > 0:
            tx = fw-4 if fw > 30 else fw+18
            self.create_text(tx, h//2, text=f"{pct}%",
                             fill=WHITE if self._current > 0.55 else MUTED,
                             font=("Tahoma", 7), anchor="e")


class DropZone(tk.Frame):
    def __init__(self, parent, on_file_cb, mode="any", **kw):
        super().__init__(parent, bg=BG, **kw)
        self._cb, self._mode = on_file_cb, mode
        self._build()
        if _DND_AVAILABLE: self._register_dnd()

    def _build(self):
        self._zone = tk.Frame(self, bg=DROP_BG_IDLE,
                              highlightthickness=1,
                              highlightbackground=DROP_BORDER_IDLE)
        self._zone.pack(fill="x")
        inner = mkframe(self._zone, bg=DROP_BG_IDLE)
        inner.pack(fill="x", padx=6, pady=4)
        left = mkframe(inner, bg=DROP_BG_IDLE)
        left.pack(side="left", fill="x", expand=True)
        self._icon_lbl = tk.Label(left, text="v", bg=DROP_BG_IDLE,
                                  fg=MUTED2, font=("Tahoma", 13))
        self._icon_lbl.pack(side="left", padx=(2,6))
        col = mkframe(left, bg=DROP_BG_IDLE)
        col.pack(side="left", fill="x", expand=True)
        primary = "Drop file here" if _DND_AVAILABLE else "Select a file"
        self._main_lbl = tk.Label(col, text=primary, bg=DROP_BG_IDLE,
                                  fg=TEXT, font=FONT_BOLD, anchor="w")
        self._main_lbl.pack(anchor="w")
        sub = "or click Browse →" if _DND_AVAILABLE else "Use the Browse button →"
        self._sub_lbl = tk.Label(col, text=sub, bg=DROP_BG_IDLE,
                                 fg=MUTED, font=FONT_SM, anchor="w")
        self._sub_lbl.pack(anchor="w")
        tk.Button(inner, text="Browse…", bg=SURFACE3, fg=TEXT, font=FONT_SM,
                  relief="flat", bd=0, cursor="hand2", padx=8, pady=4,
                  highlightthickness=1, highlightbackground=BORDER_HI,
                  activebackground=ACCENT_A, activeforeground=WHITE,
                  command=self._browse).pack(side="right", padx=(6,2))

    def _browse(self):
        filters = {
            "vault": [("Vault files", "*.vault"), ("All files", "*.*")],
            "vz":    [("VZ archives", "*.vz"),    ("All files", "*.*")],
        }
        path = filedialog.askopenfilename(
            filetypes=filters.get(self._mode, [("All files", "*.*")]))
        if path: self._cb(path)

    def _register_dnd(self):
        targets = [self, self._zone]
        for child in self._zone.winfo_children():
            targets.append(child)
            for sub in child.winfo_children(): targets.append(sub)
        for widget in targets:
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<DropEnter>>", self._on_enter)
                widget.dnd_bind("<<DropLeave>>", self._on_leave)
                widget.dnd_bind("<<Drop>>",      self._on_drop)
            except Exception: pass

    def _on_enter(self, event=None):
        self._zone.config(highlightbackground=DROP_BORDER_HOVER, bg=DROP_BG_HOVER)
        for w in [self._icon_lbl, self._main_lbl, self._sub_lbl]:
            w.config(bg=DROP_BG_HOVER)
        self._icon_lbl.config(fg=ACCENT_B)
        return event.action if event else None

    def _on_leave(self, event=None):
        self._zone.config(highlightbackground=DROP_BORDER_IDLE, bg=DROP_BG_IDLE)
        for w in [self._icon_lbl, self._main_lbl, self._sub_lbl]:
            w.config(bg=DROP_BG_IDLE)
        self._icon_lbl.config(fg=MUTED2)

    def _on_drop(self, event):
        self._on_leave()
        path = _clean_drop_path(event.data)
        if os.path.isfile(path): self._cb(path)
        else: messagebox.showerror("Drop Error", f"Not a valid file:\n{path}")

    def set_file(self, name):
        display = name if len(name) <= 42 else name[:19] + "…" + name[-19:]
        self._main_lbl.config(text=display, fg=ACCENT_C)
        self._sub_lbl.config(text="")
        self._icon_lbl.config(fg=ACCENT_B)

class BasePanel(tk.Frame):
    def __init__(self, parent, drop_mode="any"):
        tk.Frame.__init__(self, parent, bg=BG, padx=16, pady=10)
        self.full_path    = None
        self.progress_var = tk.DoubleVar(value=0.0)
        self.status_var   = tk.StringVar(value="")
        self._dropzone = DropZone(self, on_file_cb=self._set_path, mode=drop_mode)
        self._dropzone.pack(fill="x")
        self._info_lbl = mklabel(self, text="", color=MUTED2, font=FONT_SM)
        self._info_lbl.pack(anchor="w", pady=(2,0))
        self._warn_lbl = mklabel(self, text="", color=WARN, font=FONT_SM)
        self._warn_lbl.pack(anchor="w")

    def _build_progress(self):
        row = mkframe(self)
        row.pack(fill="x", pady=(0,3))
        mklabel(row, text="Progress:", color=MUTED, font=FONT_SM).pack(side="left")
        self._status_lbl = mklabel(row, var=self.status_var, color=MUTED, font=FONT_SM)
        self._status_lbl.pack(side="right")
        SmoothProgressBar(self, self.progress_var).pack(fill="x")

    def _build_action_row(self, label, command):
        row = mkframe(self)
        row.pack(fill="x", pady=(6,0))
        GradientButton(row, label, command, width=112, height=23).pack(side="left")
        self._result_lbl = mklabel(row, text="", color=SUCCESS, font=FONT_SM)
        self._result_lbl.pack(side="left", padx=(10,0))

    def _set_path(self, path):
        self.full_path = path
        self._dropzone.set_file(os.path.basename(path))
        self._on_path_set(path)
        self._reset()

    def _on_path_set(self, path):
        pass

    def _reset(self):
        self.status_var.set("")
        self._status_lbl.config(fg=MUTED)
        self._result_lbl.config(text="")
        self.progress_var.set(0.0)

    def _set_status(self, msg, color=MUTED):
        self.status_var.set(msg)
        self._status_lbl.config(fg=color)

    def _progress_cb(self, val, msg=""):
        self.after(0, lambda: self.progress_var.set(val))
        self.after(0, lambda: self._set_status(msg))

    def _ui(self, fn, *args, **kwargs):
        self.after(0, lambda: fn(*args, **kwargs))

def _make_pw_row(parent, pw_var, label="Password:"):
    mklabel(parent, text=label, color=MUTED, font=FONT_SM).pack(anchor="w", pady=(0,2))
    row = mkframe(parent)
    row.pack(fill="x")
    entry = NavyEntry(row, pw_var, show="*", width=24)
    entry.pack(side="left", ipady=3)
    show_btn = tk.Button(row, text="Show", bg=BG, fg=MUTED2, font=FONT_SM,
                         relief="flat", bd=0, cursor="hand2", padx=6)
    show_btn.pack(side="left", padx=(6,0))
    _show = [False]
    def toggle():
        _show[0] = not _show[0]
        entry.config(show="" if _show[0] else "*")
        show_btn.config(text="Hide" if _show[0] else "Show")
    show_btn.config(command=toggle)
    return entry

ENC_ALGORITHMS = ["AES-256-GCM", "Blowfish-CBC"]

_ALGO_COLORS = {
    "AES-256-GCM":  (ACCENT_A, ACCENT_B),
    "Blowfish-CBC": ("#6a30b0", "#b060ff"),
}
_ALGO_HINTS = {
    "AES-256-GCM":  "128 bit blocks with 256 bit key (reccomended)",
    "Blowfish-CBC": "128-bit key, PKCS7 padding",
}

class AlgoSelector(tk.Frame):
    def __init__(self, parent, variable, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._var = variable
        self._btns = {}
        self._build()
        self._var.trace_add("write", lambda *_: self._redraw_all())

    def _build(self):
        mklabel(self, text="Algorithm:", color=MUTED, font=FONT_SM).pack(anchor="w", pady=(0,3))
        row = mkframe(self)
        row.pack(anchor="w")
        for algo in ENC_ALGORITHMS:
            cv = tk.Canvas(row, width=138, height=21, bd=0,
                           highlightthickness=0, cursor="hand2", bg=BG)
            cv.pack(side="left", padx=(0,6))
            cv.bind("<ButtonRelease-1>", lambda e, a=algo: self._var.set(a))
            cv.bind("<Enter>",  lambda e, a=algo: self._hover(a, True))
            cv.bind("<Leave>",  lambda e, a=algo: self._hover(a, False))
            cv._hovering = False
            self._btns[algo] = cv
        self._hint = mklabel(self, text="", color=MUTED, font=FONT_SM)
        self._hint.pack(anchor="w", pady=(2,0))
        self._redraw_all()

    def _hover(self, algo, state):
        self._btns[algo]._hovering = state
        self._redraw(algo)

    def _redraw_all(self):
        for a in ENC_ALGORITHMS: self._redraw(a)
        self._hint.config(text=_ALGO_HINTS.get(self._var.get(), ""))

    def _redraw(self, algo):
        cv = self._btns[algo]; cv.delete("all")
        sel = self._var.get() == algo
        hov = getattr(cv, "_hovering", False)
        w, h = 138, 21
        c1, c2 = _ALGO_COLORS[algo]
        if sel:
            draw_hg(cv,0,0,w,h,lerp_color(c1,"#000000",0.4),lerp_color(c2,"#000000",0.3))
            border = c2
        elif hov:
            draw_hg(cv,0,0,w,h,lerp_color(SURFACE2,"#000000",0.1),SURFACE3)
            border = lerp_color(BORDER_HI,c2,0.4)
        else:
            cv.configure(bg=SURFACE2)
            cv.create_rectangle(0,0,w-1,h-1,fill=SURFACE2,outline=BORDER)
            border = BORDER
        if sel or hov: cv.create_rectangle(0,0,w-1,h-1,fill="",outline=border)
        cv.create_oval(5,6,13,14,fill=c2 if sel else MUTED2,outline="")
        if sel: cv.create_oval(8,9,10,11,fill=WHITE,outline="")
        cv.create_text(18,h//2,text=algo,
                       fill=WHITE if sel else MUTED,
                       font=FONT_BOLD if sel else FONT_SM, anchor="w")


class VaultPanel(BasePanel):
    def __init__(self, parent, mode, app):
        super().__init__(parent, drop_mode="vault" if mode=="dec" else "any")
        self.mode = mode
        self.pw_var   = tk.StringVar()
        self.algo_var = tk.StringVar(value=ENC_ALGORITHMS[0])

        thin_divider(self, pady=4)
        AlgoSelector(self, self.algo_var).pack(fill="x")
        thin_divider(self, pady=4)
        _make_pw_row(self, self.pw_var)
        thin_divider(self, pady=4)
        self._build_progress()
        self._build_action_row(
            "Encrypt File" if mode=="enc" else "Decrypt File",
            self._on_action)

    def _on_path_set(self, path):
        if self.mode == "enc":
            self._info_lbl.config(text="  Output → [timestamp].vault next to source")
            try:
                sz = os.path.getsize(path)
                self._warn_lbl.config(
                    text=f"  ⚠ Large file ({_fmt_size(sz)}) loaded fully into RAM"
                    if sz > LARGE_FILE_THRESHOLD else "")
            except OSError:
                self._warn_lbl.config(text="")
        else:
            self._info_lbl.config(text="  Output → original filename (restored from vault)")
            self._warn_lbl.config(text="")

    def _on_action(self):
        if not self.full_path:
            messagebox.showwarning("No File", "Please select a file first."); return
        if not self.pw_var.get():
            messagebox.showwarning("No Password", "Please enter a password."); return
        self._reset()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            algo    = self.algo_var.get()
            out_dir = os.path.dirname(self.full_path) or "."
            if self.mode == "enc":
                orig_size = os.path.getsize(self.full_path)
                ts  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                out = safe_output_path(os.path.join(out_dir, f"{ts}.vault"))
                encrypt_file(self.full_path, out, self.pw_var.get(),
                             progress=self._progress_cb, algorithm=algo)
                name = os.path.basename(out)
                tag  = f"[{algo}] " if algo != ENC_ALGORITHMS[0] else ""
                self._ui(self._result_lbl.config, text=f"{tag}→ {name}", fg=SUCCESS)
                self._ui(self._set_status, "Done", SUCCESS)
                append_history({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "original_name": os.path.basename(self.full_path),
                                "original_size": orig_size, "vault_name": name,
                                "vault_path": out, "vault_size": os.path.getsize(out),
                                "algorithm": algo})
            else:
                out = decrypt_file(self.full_path, out_dir, self.pw_var.get(),
                                   progress=self._progress_cb, algorithm=algo)
                self._ui(self._result_lbl.config, text=f"→ {os.path.basename(out)}", fg=SUCCESS)
                self._ui(self._set_status, "Done", SUCCESS)
        except Exception as exc:
            self._ui(self._set_status, str(exc), DANGER)
            self._ui(self.progress_var.set, 0.0)

COMP_ALGO_COLORS = {
    "zlib": (ACCENT_A, ACCENT_B),
}
COMP_ALGO_HINTS = {
    "zlib": "Most effective compression",
}

class CompAlgoSelector(tk.Frame):
    def __init__(self, parent, variable, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._var = variable
        self._btns = {}
        self._avail = available_algorithms()
        self._build()
        self._var.trace_add("write", lambda *_: self._redraw_all())

    def _build(self):
        mklabel(self, text="Compression:", color=MUTED, font=FONT_SM).pack(anchor="w", pady=(0,3))
        row = mkframe(self); row.pack(anchor="w")
        for algo in COMP_ALGORITHMS:
            cv = tk.Canvas(row, width=80, height=21, bd=0,
                           highlightthickness=0, bg=BG,
                           cursor="hand2" if algo in self._avail else "arrow")
            cv.pack(side="left", padx=(0,4))
            if algo in self._avail:
                cv.bind("<ButtonRelease-1>", lambda e, a=algo: self._var.set(a))
                cv.bind("<Enter>",  lambda e, a=algo: self._hover(a, True))
                cv.bind("<Leave>",  lambda e, a=algo: self._hover(a, False))
            cv._hovering = False
            self._btns[algo] = cv
        self._hint = mklabel(self, text="", color=MUTED, font=FONT_SM)
        self._hint.pack(anchor="w", pady=(2,0))
        self._redraw_all()

    def _hover(self, algo, state):
        self._btns[algo]._hovering = state; self._redraw(algo)

    def _redraw_all(self):
        for a in COMP_ALGORITHMS: self._redraw(a)
        self._hint.config(text=COMP_ALGO_HINTS.get(self._var.get(), ""))

    def _redraw(self, algo):
        cv = self._btns[algo]; cv.delete("all")
        sel   = self._var.get() == algo
        hov   = getattr(cv, "_hovering", False)
        avail = algo in self._avail
        w, h  = 80, 21
        c1, c2 = COMP_ALGO_COLORS.get(algo, (ACCENT_A, ACCENT_B))
        if not avail:
            cv.create_rectangle(0,0,w-1,h-1,fill=INSET,outline=BORDER_LO)
            cv.create_text(w//2,h//2,text=algo,fill=MUTED2,font=FONT_SM,anchor="center")
            return
        if sel:
            draw_hg(cv,0,0,w,h,lerp_color(c1,"#000000",0.4),lerp_color(c2,"#000000",0.3))
            border = c2
        elif hov:
            draw_hg(cv,0,0,w,h,lerp_color(SURFACE2,"#000000",0.1),SURFACE3)
            border = lerp_color(BORDER_HI,c2,0.4)
        else:
            cv.configure(bg=SURFACE2)
            cv.create_rectangle(0,0,w-1,h-1,fill=SURFACE2,outline=BORDER)
            border = BORDER
        if sel or hov: cv.create_rectangle(0,0,w-1,h-1,fill="",outline=border)
        cv.create_text(w//2,h//2,text=algo,
                       fill=WHITE if sel else MUTED,
                       font=FONT_BOLD if sel else FONT_SM, anchor="center")


class CompressPanel(BasePanel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.pw_var   = tk.StringVar()
        self.algo_var = tk.StringVar(value=available_algorithms()[0])
        self.meta_var = tk.StringVar()

        thin_divider(self, pady=3)
        CompAlgoSelector(self, self.algo_var).pack(fill="x")
        thin_divider(self, pady=3)
        _make_pw_row(self, self.pw_var, "Password (optional):")
        thin_divider(self, pady=3)
        mklabel(self, text="Metadata note (optional):", color=MUTED, font=FONT_SM).pack(anchor="w", pady=(0,2))
        NavyEntry(self, self.meta_var, width=36).pack(anchor="w", ipady=3)
        thin_divider(self, pady=3)
        self._build_progress()
        self._build_action_row("Compress File", self._on_action)

    def _on_path_set(self, path):
        self._info_lbl.config(text="  Output → [filename].vz next to source")
        try:
            sz = os.path.getsize(path)
            self._warn_lbl.config(
                text=f"  ⚠ Large file ({_fmt_size(sz)}) loaded fully into RAM"
                if sz > LARGE_FILE_THRESHOLD else "")
        except OSError:
            self._warn_lbl.config(text="")

    def _on_action(self):
        if not self.full_path:
            messagebox.showwarning("No File", "Please select a file first."); return
        self._reset()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            out_dir = os.path.dirname(self.full_path) or "."
            stem    = os.path.splitext(os.path.basename(self.full_path))[0]
            out     = safe_output_path(os.path.join(out_dir, f"{stem}.vz"))
            note    = self.meta_var.get().strip()
            meta    = {"note": note} if note else None
            compress_file(self.full_path, out,
                          algorithm=self.algo_var.get(),
                          password=self.pw_var.get(),
                          metadata=meta,
                          progress=self._progress_cb)
            self._ui(self._result_lbl.config, text=f"→ {os.path.basename(out)}", fg=SUCCESS)
            self._ui(self._set_status, "Done", SUCCESS)
        except Exception as exc:
            self._ui(self._set_status, str(exc), DANGER)
            self._ui(self.progress_var.set, 0.0)


class DecompressPanel(BasePanel):
    def __init__(self, parent, app):
        super().__init__(parent, drop_mode="vz")
        self.pw_var = tk.StringVar()

        thin_divider(self, pady=3)
        self._meta_lbl = mklabel(self, text="", color=MUTED, font=FONT_SM)
        self._meta_lbl.pack(anchor="w")
        thin_divider(self, pady=3)
        _make_pw_row(self, self.pw_var, "Password (if encrypted):")
        thin_divider(self, pady=3)
        self._build_progress()
        self._build_action_row("Decompress File", self._on_action)

    def _on_path_set(self, path):
        self._info_lbl.config(text="  Output → original filename next to source")
        self._warn_lbl.config(text="")
        try:
            meta  = read_metadata(path)
            parts = []
            if "original_name" in meta: parts.append(meta["original_name"])
            if "original_size" in meta: parts.append(_fmt_size(meta["original_size"]))
            if "algorithm"     in meta: parts.append(meta["algorithm"])
            if meta.get("encrypted"):   parts.append("🔒 encrypted")
            if meta.get("note"):        parts.append(f'note: {meta["note"]}')
            self._meta_lbl.config(text="  " + "  ·  ".join(parts) if parts else "")
        except Exception:
            self._meta_lbl.config(text="")

    def _on_action(self):
        if not self.full_path:
            messagebox.showwarning("No File", "Please select a .vz file first."); return
        self._reset()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            out_dir = os.path.dirname(self.full_path) or "."
            out, _  = decompress_file(self.full_path, out_dir,
                                      password=self.pw_var.get(),
                                      progress=self._progress_cb)
            self._ui(self._result_lbl.config, text=f"→ {os.path.basename(out)}", fg=SUCCESS)
            self._ui(self._set_status, "Done", SUCCESS)
        except Exception as exc:
            self._ui(self._set_status, str(exc), DANGER)
            self._ui(self.progress_var.set, 0.0)

class WizardPanel(tk.Frame):
    def __init__(self, parent, app):
        tk.Frame.__init__(self, parent, bg=BG, padx=20, pady=16)
        self.steps = [
            ("Welcome to Vault",
             "This wizard covers how to use each tab.\nPress 'Next' to start."),
            ("Encrypt & Decrypt",
             "Encrypt turns any file into a .vault archive using AES-256-GCM\n"
             "or Blowfish-CBC. A password is required. Decrypt restores it.\n"
             "The original filename is preserved inside the vault header."),
            ("Compress & Decompress",
             "Compress shrinks a file into a .vz archive using zlib, zstd,\n"
             "or lz4. A password is optional leave it blank for no encryption.\n"
             "You can also attach a short metadata note (stored as plain text)."),
            ("A note on privacy",
             "The history log (vault_history.json) records filenames and paths.\n"
             "Rename files before encrypting if you want the name hidden\n"
             "it is stored inside the vault and .vz headers."),
            ("Ready!",
             "You're all set. Drop a file onto any tab and go.\n"
             "AES-256-GCM is recommended for encryption.\n"
             "zstd gives the best compression if installed."),
        ]
        self.cur = 0
        self._build()

    def _build(self):
        self._title = mklabel(self, text="", font=FONT_TITLE, color=ACCENT_C)
        self._title.pack(anchor="w", pady=(0,8))
        self._desc  = mklabel(self, text="", font=FONT, color=TEXT)
        self._desc.pack(anchor="w", pady=(0,16))
        row = mkframe(self); row.pack(fill="x")
        GradientButton(row, "Next", self._next, width=80).pack(side="left")
        self._step_lbl = mklabel(row, text="", color=MUTED2, font=FONT_SM)
        self._step_lbl.pack(side="left", padx=(10,0))
        self._refresh()

        thin_divider(self, pady=10)
        mklabel(self, text="Vault", font=FONT_BOLD, color=ACCENT_C).pack(anchor="w")
        mklabel(self,
                text="A local file encryption and compression tool.\n"
                     "Not even the FBI can read your files.",
                color=TEXT, font=FONT_SM).pack(anchor="w", pady=(2,6))
        info_rows = [
            ("Encryption",  "AES-256-GCM ; Blowfish-CBC"),
            ("Compression", "zlib (built-in) ; zstd (LATER) ; lz4 (LATER)"),
            ("Built: ",  "Python ; Tkinter ; cryptography ; pycryptodomex"),
            ("Version info: ", "v1.1.0 (01.04.2026) ; l.t.r."),
            ("Support: ", "https://www.donationalerts.com/r/ltrsociety"),
        ]
        for label, value in info_rows:
            row = mkframe(self); row.pack(anchor="w", fill="x", pady=1)
            mklabel(row, text=f"{label}:", color=MUTED,  font=FONT_SM, width=14).pack(side="left")
            mklabel(row, text=value,       color=TEXT,   font=FONT_SM).pack(side="left")

    def _next(self):
        self.cur = (self.cur + 1) % len(self.steps)
        self._refresh()
        if self.cur == 0:
            messagebox.showinfo("Vault Wizard", "Tutorial complete!")

    def _refresh(self):
        t, d = self.steps[self.cur]
        self._title.config(text=t)
        self._desc.config(text=d)
        self._step_lbl.config(text=f"{self.cur+1} / {len(self.steps)}")


# ── Application ───────────────────────────────────────────────────────────────
_AppBase = TkinterDnD.Tk if _DND_AVAILABLE else tk.Tk

TABS  = ["Encrypt", "Decrypt", "Compress", "Decompress", "Wizard"]
ICONS = ["ico1.png", "ico2.png", "ico5.png", "ico6.png", "ico3.png"]


class VaultApp(_AppBase):
    def __init__(self):
        super().__init__()
        self.title("Vault")
        self.geometry("520x420")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.ico_imgs = []
        for f in ICONS:
            img = Image.open(resource_path(f)).resize((20, 20), Image.LANCZOS)
            self.ico_imgs.append(ImageTk.PhotoImage(img))

        logo_raw = Image.open(resource_path("ico1.png")).resize((26, 26), Image.LANCZOS)
        self.logo_img = ImageTk.PhotoImage(logo_raw)

        self._active = 0
        self._build()

    def _build(self):
        self._hdr = tk.Canvas(self, height=52, bd=0, highlightthickness=0, bg=HDR_C)
        self._hdr.pack(fill="x")
        self._hdr.bind("<Configure>", self._draw_header)

        tk.Frame(self, bg=BORDER_LO, height=1).pack(fill="x")
        tk.Frame(self, bg=BORDER_HI, height=1).pack(fill="x")

        container = mkframe(self)
        container.pack(fill="both", expand=True)

        self._panels = [
            VaultPanel(container, "enc", self),
            VaultPanel(container, "dec", self),
            CompressPanel(container, self),
            DecompressPanel(container, self),
            WizardPanel(container, self),
        ]

        tk.Frame(self, bg=BORDER_LO, height=1).pack(fill="x")

        if not _DND_AVAILABLE:
            banner = tk.Frame(self, bg="#1a1010")
            banner.pack(fill="x")
            tk.Label(banner,
                     text="  pip install tkinterdnd2  for drag & drop",
                     bg="#1a1010", fg=WARN, font=FONT_SM).pack(pady=2)

        self._switch(0)

    def _draw_header(self, event=None):
        cv = self._hdr; cv.delete("all")
        w, h = cv.winfo_width(), cv.winfo_height()
        if w < 2: return
        draw_v3(cv, 0, 0, w, h, HDR_A, HDR_B, HDR_C)
        cv.create_image(20, h//2, image=self.logo_img)
        cv.create_text(40, h//2 - 6, text="Vault", fill=WHITE, font=FONT_TITLE, anchor="w")
        cv.create_text(40, h//2 + 7, text="Local file utility v1.1.0", fill=MUTED, font=FONT_SM, anchor="w")

        btn_w    = 62
        n        = len(TABS)
        bx_start = w - 8 - n * (btn_w + 3)

        for i, lbl in enumerate(TABS):
            active = (self._active == i)
            bx  = bx_start + i * (btn_w + 3)
            by0, by1 = 4, h - 4
            bg_c = lerp_color(HDR_B, ACCENT_A, 0.30) if active \
                   else lerp_color(HDR_B, HDR_C, 0.50)
            bo_c = lerp_color(BORDER_HI, ACCENT_B, 0.55) if active \
                   else lerp_color(BORDER_HI, HDR_B, 0.30)
            cv.create_rectangle(bx, by0, bx+btn_w, by1, fill=bg_c, outline=bo_c)
            cv.create_image(bx+btn_w//2, by0+11, image=self.ico_imgs[i])
            cv.create_text(bx+btn_w//2, by1-7, text=lbl,
                           fill=WHITE if active else MUTED,
                           font=FONT_SM, anchor="center")
            tag = f"_tab{i}"
            cv.create_rectangle(bx, by0, bx+btn_w, by1, fill="", outline="", tags=tag)
            cv.tag_bind(tag, "<ButtonRelease-1>", lambda e, ix=i: self._switch(ix))

    def _switch(self, idx):
        self._active = idx
        for i, p in enumerate(self._panels):
            if i == idx: p.pack(fill="both", expand=True)
            else:        p.pack_forget()
        self._draw_header()
