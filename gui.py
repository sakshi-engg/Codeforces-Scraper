from tkinter import *
from tkinter import messagebox
import requests
import threading

# ─── Palette ────────────────────────────────────────────────────
BG     = "#0D1117"
CARD   = "#161B22"
BORDER = "#30363D"
ACCENT = "#00D4FF"
TEXT   = "#E6EDF3"
MUTED  = "#8B949E"
CELL   = "#21262D"
RED    = "#F85149"

def rank_color(rating):
    if   rating < 1200: return "#888888"
    elif rating < 1400: return "#77FF77"
    elif rating < 1600: return "#77DDBB"
    elif rating < 1900: return "#AAAAFF"
    elif rating < 2100: return "#FF88FF"
    elif rating < 2400: return "#FFBB55"
    elif rating < 2600: return "#FF7777"
    elif rating < 3000: return "#FF3333"
    else:               return "#AA0000"


class App:
    def __init__(self, root):
        self.root = root
        root.title("CF Stats Viewer")
        root.geometry("480x650")
        root.configure(bg=BG)
        root.resizable(False, False)
        self._spinning = False
        self._spin_angle = 0
        self._build()

    # ── Build UI ──────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = Frame(self.root, bg=BG)
        hdr.pack(fill=X, pady=(30, 0))
        Label(hdr, text="⚡ CODEFORCES", font=("Consolas", 22, "bold"),
              bg=BG, fg=ACCENT).pack()
        Label(hdr, text="STATS  VIEWER", font=("Consolas", 10),
              bg=BG, fg=MUTED).pack()

        Canvas(self.root, height=1, bg=BORDER, highlightthickness=0)\
            .pack(fill=X, padx=40, pady=18)

        # Entry
        inp = Frame(self.root, bg=BG)
        inp.pack(padx=40, fill=X)
        Label(inp, text="HANDLE", font=("Consolas", 8, "bold"),
              bg=BG, fg=MUTED).pack(anchor=W)

        self._ef = Frame(inp, bg=BORDER, padx=2, pady=2)
        self._ef.pack(fill=X)
        self.entry = Entry(self._ef, font=("Consolas", 14), bg=CARD,
                           fg=TEXT, insertbackground=ACCENT,
                           relief=FLAT, width=28)
        self.entry.pack(ipady=10, padx=1)
        self.entry.bind("<Return>",   lambda _: self.fetch())
        self.entry.bind("<FocusIn>",  lambda _: self._ef.config(bg=ACCENT))
        self.entry.bind("<FocusOut>", lambda _: self._ef.config(bg=BORDER))

        # Button
        self.btn = Button(self.root, text="SHOW STATS  ▶",
                          font=("Consolas", 12, "bold"),
                          bg=ACCENT, fg=BG,
                          activebackground="#33EEFF", activeforeground=BG,
                          relief=FLAT, cursor="hand2",
                          padx=30, pady=12, command=self.fetch)
        self.btn.pack(pady=20)
        self.btn.bind("<Enter>", lambda _: self.btn.config(bg="#33EEFF"))
        self.btn.bind("<Leave>", lambda _: self.btn.config(bg=ACCENT))

        # Spinner canvas
        self.spinner = Canvas(self.root, width=48, height=48,
                              bg=BG, highlightthickness=0)

        # Result card
        self.card = Frame(self.root, bg=CARD,
                          highlightbackground=BORDER, highlightthickness=1)

    # ── Spinner ───────────────────────────────────────────────────
    def _spin_show(self):
        self.card.pack_forget()
        self.spinner.pack(pady=16)
        self._spinning = True
        self._tick_spin()

    def _spin_hide(self):
        self._spinning = False
        self.spinner.pack_forget()

    def _tick_spin(self):
        if not self._spinning:
            return
        c = self.spinner
        c.delete("all")
        a = self._spin_angle
        c.create_arc(4, 4, 44, 44, start=a,     extent=270,
                     outline=ACCENT, width=3, style=ARC)
        c.create_arc(4, 4, 44, 44, start=a+270, extent=90,
                     outline=BORDER, width=3, style=ARC)
        self._spin_angle = (a + 12) % 360
        self.root.after(30, self._tick_spin)

    # ── Fetch (threaded) ──────────────────────────────────────────
    def fetch(self):
        h = self.entry.get().strip()
        if not h:
            self._ef.config(bg=RED)
            self.root.after(500, lambda: self._ef.config(bg=BORDER))
            return
        self.btn.config(state=DISABLED, text="FETCHING …")
        self._spin_show()
        threading.Thread(target=self._do_fetch, args=(h,), daemon=True).start()

    def _do_fetch(self, h):
        try:
            url  = f"https://codeforces.com/api/user.info?handles={h}"
            data = requests.get(url, timeout=10).json()
            self.root.after(0, lambda: self._show(data, h))
        except Exception as ex:
            self.root.after(0, lambda: self._net_err(str(ex)))

    # ── Result card ───────────────────────────────────────────────
    def _show(self, data, handle):
        self._spin_hide()
        self.btn.config(state=NORMAL, text="SHOW STATS  ▶")
        for w in self.card.winfo_children():
            w.destroy()

        if data.get("status") != "OK":
            Label(self.card, text="✗  USER NOT FOUND",
                  font=("Consolas", 13, "bold"),
                  bg=CARD, fg=RED).pack(pady=24)
            self.card.pack(fill=X, padx=40, pady=4)
            return

        x   = data["result"][0]
        r   = x.get("rating",    0)
        mr  = x.get("maxRating", 0)
        rk  = x.get("rank",      "unranked").title()
        mrk = x.get("maxRank",   "unranked").title()
        rc  = rank_color(r)
        mrc = rank_color(mr)

        # Handle row
        top = Frame(self.card, bg=CARD)
        top.pack(fill=X, padx=20, pady=(18, 4))
        Label(top, text="●", font=("Consolas", 14),
              bg=CARD, fg=rc).pack(side=LEFT)
        Label(top, text=f"  {handle}",
              font=("Consolas", 18, "bold"), bg=CARD, fg=TEXT).pack(side=LEFT)

        Canvas(self.card, height=1, bg=BORDER, highlightthickness=0)\
            .pack(fill=X, padx=20, pady=6)

        # 2×2 stat grid
        grid = Frame(self.card, bg=CARD)
        grid.pack(fill=X, padx=20, pady=6)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        cells = [
            ("CURRENT RATING", str(r),  rc),
            ("CURRENT RANK",   rk,      rc),
            ("MAX RATING",     str(mr), mrc),
            ("MAX RANK",       mrk,     mrc),
        ]
        for i, (lbl, val, col) in enumerate(cells):
            cell = Frame(grid, bg=CELL, padx=14, pady=10)
            cell.grid(row=i//2, column=i%2, padx=4, pady=4, sticky=NSEW)
            Label(cell, text=lbl, font=("Consolas", 8),
                  bg=CELL, fg=MUTED).pack(anchor=W)
            Label(cell, text=val, font=("Consolas", 14, "bold"),
                  bg=CELL, fg=col).pack(anchor=W)

        # Rating bar
        bframe = Frame(self.card, bg=CARD)
        bframe.pack(fill=X, padx=20, pady=(8, 20))
        Label(bframe, text="RATING PROGRESS  (max 3000)",
              font=("Consolas", 8), bg=CARD, fg=MUTED).pack(anchor=W)
        bar = Canvas(bframe, height=8, bg=BORDER,
                     highlightthickness=0, relief=FLAT)
        bar.pack(fill=X, pady=4)
        self.root.after(50, lambda: self._anim_bar(bar, r, rc))

        self.card.pack(fill=X, padx=40, pady=4)
        self._flash_card()

    # ── Animated rating bar ───────────────────────────────────────
    def _anim_bar(self, canvas, rating, color, step=0):
        canvas.update_idletasks()
        w = canvas.winfo_width()
        if w < 10:
            self.root.after(50, lambda: self._anim_bar(canvas, rating, color, step))
            return
        target = min(rating / 3000, 1.0)
        pct    = min(step / 60, target)
        canvas.delete("all")
        if pct > 0:
            canvas.create_rectangle(0, 0, int(w * pct), 8, fill=color, outline="")
        if pct < target:
            self.root.after(12, lambda: self._anim_bar(canvas, rating, color, step + 1))

    # ── Card flash on reveal ──────────────────────────────────────
    def _flash_card(self):
        seq = [ACCENT, BORDER, ACCENT, BORDER]
        def step(i=0):
            if i < len(seq):
                self.card.config(highlightbackground=seq[i])
                self.root.after(120, lambda: step(i + 1))
        step()

    def _net_err(self, msg):
        self._spin_hide()
        self.btn.config(state=NORMAL, text="SHOW STATS  ▶")
        messagebox.showerror("Network Error", msg)


root = Tk()
App(root)
root.mainloop()
