"""Interactive demo for the live presentation (Tkinter + matplotlib).

    python -m demo

Tab 1 "Deney" (experiment): choose the scenario (constant / Fig. 17 steps / custom steps /
load steps), irradiance, temperature, load, measurement noise and the controllers,
then run. Plots P_pv vs P_opt and D for every controller and lists the metrics.

Tab 2 "Bulanık çıkarım" (fuzzy inference): enter SInC and CSI by hand and see the
membership degrees, which of the 35 rules fire and how strongly, the clipped and
aggregated output set and the centroid dD. This is the Mamdani step that runs every 1 ms.
"""
from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np

from src import scenarios
from src.config import PANEL
from src.mppt import CONTROLLERS
from src.mppt.flc_sinc_csi import build_fis
from src.mppt.robust import make_variant
from src.pv_model import mpp
from src.simulate import run, summarize

ALGOS = [
    ("po", "P&O"),
    ("inc", "InC"),
    ("flc_sinc", "Alg. 3 (SInC)"),
    ("flc_sinc_csi", "Önerilen (SInC+CSI)"),
    ("alg3+FDC", "Alg. 3 + dayanıklı"),
    ("prop+FDC", "Önerilen + dayanıklı"),
]
COLORS = {"po": "tab:gray", "inc": "tab:brown", "flc_sinc": "tab:blue", "flc_sinc_csi": "tab:red",
          "alg3+FDC": "tab:cyan", "prop+FDC": "tab:green"}
SCENARIOS = ["Sabit ışınım", "Makale Şekil 17 (2 s)", "Özel basamaklar", "Yük basamağı 50→20→35 Ω"]


def make_controller(key: str):
    return CONTROLLERS[key]() if key in CONTROLLERS else make_variant(key)


def _dpi_aware() -> None:
    """Sharp rendering and correct sizes on high-DPI Windows displays (125-200 % scaling)."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


class DemoApp(tk.Tk):
    def __init__(self) -> None:
        _dpi_aware()
        super().__init__()
        self.title("Hibrit InC–Bulanık MPPT · Canlı Demo")
        self.geometry("1350x820")
        try:
            self.state("zoomed")      # maximised on Windows
        except tk.TclError:
            pass
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Run.TButton", font=("Segoe UI", 11, "bold"))
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        self.exp_tab = ttk.Frame(nb)
        self.fis_tab = ttk.Frame(nb)
        nb.add(self.exp_tab, text="  Deney  ")
        nb.add(self.fis_tab, text="  Bulanık çıkarım  ")
        self._build_experiment_tab()
        self._build_fis_tab()

    # ------------------------------------------------------------------ experiment tab
    def _build_experiment_tab(self) -> None:
        left = ttk.Frame(self.exp_tab, padding=10)
        left.pack(side="left", fill="y")
        right = ttk.Frame(self.exp_tab, padding=(0, 10, 10, 10))
        right.pack(side="left", fill="both", expand=True)

        self.v_scen = tk.StringVar(value=SCENARIOS[0])
        self.v_g = tk.DoubleVar(value=1000.0)
        self.v_t = tk.DoubleVar(value=25.0)
        self.v_r = tk.DoubleVar(value=50.0)
        self.v_noise = tk.DoubleVar(value=0.0)
        self.v_tend = tk.DoubleVar(value=0.6)
        self.v_steps = tk.StringVar(value="1000, 300, 700")
        self.v_stepdur = tk.DoubleVar(value=0.2)
        self.v_seed = tk.IntVar(value=0)
        self.v_algos = {k: tk.BooleanVar(value=k in ("po", "flc_sinc_csi")) for k, _ in ALGOS}

        def row(label, widget, r, hint=""):
            ttk.Label(left, text=label).grid(row=r, column=0, sticky="w", pady=3)
            widget.grid(row=r, column=1, sticky="we", pady=3)
            if hint:
                ttk.Label(left, text=hint, foreground="#666").grid(row=r, column=2, sticky="w", padx=4)

        ttk.Label(left, text="Senaryo", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
        cb = ttk.Combobox(left, textvariable=self.v_scen, values=SCENARIOS, state="readonly", width=26)
        row("Tür", cb, 1)
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_scenario())
        self.g_scale = self._scale(left, self.v_g, 100, 1100, 10)
        row("Işınım G (W/m²)", self.g_scale, 2)
        self.g_label = ttk.Label(left, width=7)
        self.g_label.grid(row=2, column=2, sticky="w")
        row("Sıcaklık T (°C)", self._scale(left, self.v_t, 0, 70, 1), 3)
        self.t_label = ttk.Label(left, width=7)
        self.t_label.grid(row=3, column=2, sticky="w")
        self.r_entry = ttk.Entry(left, textvariable=self.v_r, width=10)
        row("Yük R (Ω)", self.r_entry, 4, "20–200")
        self.steps_entry = ttk.Entry(left, textvariable=self.v_steps, width=26)
        row("Basamaklar (W/m²)", self.steps_entry, 5)
        self.stepdur_entry = ttk.Entry(left, textvariable=self.v_stepdur, width=10)
        row("Basamak süresi (s)", self.stepdur_entry, 6)
        self.tend_entry = ttk.Entry(left, textvariable=self.v_tend, width=10)
        row("Benzetim süresi (s)", self.tend_entry, 7, "≤ 3")

        ttk.Separator(left).grid(row=8, column=0, columnspan=3, sticky="we", pady=8)
        ttk.Label(left, text="Ölçüm gürültüsü", font=("Segoe UI", 10, "bold")).grid(row=9, column=0, columnspan=3, sticky="w")
        row("σ (% tam ölçek)", self._scale(left, self.v_noise, 0, 2, 0.05), 10)
        self.n_label = ttk.Label(left, width=7)
        self.n_label.grid(row=10, column=2, sticky="w")
        row("Tohum (seed)", ttk.Spinbox(left, from_=0, to=999, textvariable=self.v_seed, width=8), 11)

        ttk.Separator(left).grid(row=12, column=0, columnspan=3, sticky="we", pady=8)
        ttk.Label(left, text="Denetleyiciler", font=("Segoe UI", 10, "bold")).grid(row=13, column=0, columnspan=3, sticky="w")
        for i, (k, name) in enumerate(ALGOS):
            ttk.Checkbutton(left, text=name, variable=self.v_algos[k]).grid(row=14 + i, column=0, columnspan=3, sticky="w")

        self.run_btn = ttk.Button(left, text="▶  Deneyi çalıştır", style="Run.TButton", command=self._run)
        self.run_btn.grid(row=21, column=0, columnspan=3, sticky="we", pady=(12, 4))
        self.status = ttk.Label(left, text="Hazır.", foreground="#333", wraplength=330)
        self.status.grid(row=22, column=0, columnspan=3, sticky="w")
        self.mpp_label = ttk.Label(left, text="", foreground="#1d4ed8", wraplength=330)
        self.mpp_label.grid(row=23, column=0, columnspan=3, sticky="w", pady=(6, 0))

        cols = ("algo", "eff", "rmse", "conv", "fail")
        self.table = ttk.Treeview(right, columns=cols, show="headings", height=6)
        for c, t, w in zip(cols, ("Denetleyici", "Verim %", "RMSE (W)", "Ort. yakınsama (ms)", "Oturamayan aralık"),
                           (220, 100, 100, 150, 140)):
            self.table.heading(c, text=t)
            self.table.column(c, width=w, anchor="center")
        self.table.pack(side="bottom", fill="x", pady=(6, 0))

        self.fig = Figure(figsize=(9, 6), dpi=100)
        self.ax_p = self.fig.add_subplot(2, 1, 1)
        self.ax_d = self.fig.add_subplot(2, 1, 2, sharex=self.ax_p)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        NavigationToolbar2Tk(self.canvas, right).update()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        for v in (self.v_g, self.v_t, self.v_noise):
            v.trace_add("write", lambda *a: self._update_labels())
        self._on_scenario()
        self._update_labels()
        self._draw_empty()

    @staticmethod
    def _scale(parent, var, lo, hi, res):
        return tk.Scale(parent, variable=var, from_=lo, to=hi, resolution=res, orient="horizontal",
                        showvalue=False, length=190)

    def _update_labels(self) -> None:
        g, t, n = self.v_g.get(), self.v_t.get(), self.v_noise.get()
        self.g_label.config(text=f"{g:.0f}")
        self.t_label.config(text=f"{t:.0f}")
        self.n_label.config(text=f"{n:.2f} %")
        try:
            v, i, p = mpp(float(round(g)), float(round(t)))
            self.mpp_label.config(text=f"G={g:.0f} W/m², T={t:.0f} °C için gerçek MPP: "
                                       f"{p:.1f} W  (V={v:.1f} V, I={i:.2f} A)  ·  "
                                       f"σ_V={n / 100 * PANEL.voc:.3f} V, σ_I={n / 100 * PANEL.isc:.4f} A")
        except Exception:
            pass

    def _on_scenario(self) -> None:
        s = self.v_scen.get()
        custom = s == SCENARIOS[2]
        for w in (self.steps_entry, self.stepdur_entry):
            w.state(["!disabled"] if custom else ["disabled"])
        self.g_scale.config(state="disabled" if s in SCENARIOS[1:3] else "normal")
        self.r_entry.state(["disabled"] if s == SCENARIOS[3] else ["!disabled"])
        if s == SCENARIOS[1]:
            self.v_tend.set(2.0)
        elif s == SCENARIOS[3]:
            self.v_tend.set(0.6)

    def _draw_empty(self) -> None:
        for ax in (self.ax_p, self.ax_d):
            ax.clear()
            ax.grid(alpha=0.3)
        self.ax_p.set_ylabel("P (W)")
        self.ax_d.set_ylabel("Görev oranı D")
        self.ax_d.set_xlabel("Zaman (s)")
        self.ax_p.set_title("Parametreleri seçip 'Deneyi çalıştır'a basın")
        self.canvas.draw_idle()

    def _read_params(self) -> dict:
        s = self.v_scen.get()
        t_end = float(self.v_tend.get())
        if not 0.05 <= t_end <= 3.0:
            raise ValueError("Benzetim süresi 0,05–3 s arasında olmalı.")
        r = float(self.v_r.get())
        if not 5 <= r <= 500:
            raise ValueError("Yük 5–500 Ω arasında olmalı.")
        g = float(round(self.v_g.get()))
        if s == SCENARIOS[0]:
            g_fn, r_fn, changes = (lambda t: np.full_like(t, g)), (lambda t: np.full_like(t, r)), [0.0]
        elif s == SCENARIOS[1]:
            g_fn, r_fn, changes = scenarios.irradiance_steps, (lambda t: np.full_like(t, r)), list(np.arange(0, 2.0, 0.2))
        elif s == SCENARIOS[2]:
            levels = tuple(float(x) for x in self.v_steps.get().replace(";", ",").split(",") if x.strip())
            if not levels or min(levels) < 50 or max(levels) > 1200:
                raise ValueError("Basamaklar 50–1200 W/m² arasında, virgülle ayrılmış olmalı.")
            dur = float(self.v_stepdur.get())
            g_fn = lambda t, lv=levels, d=dur: scenarios.irradiance_steps(t, lv, d)
            r_fn = lambda t: np.full_like(t, r)
            changes = [k * dur for k in range(len(levels)) if k * dur < t_end]
        else:
            g_fn, r_fn, changes = (lambda t: np.full_like(t, g)), scenarios.load_steps, [0.0, 0.2, 0.4]
        algos = [k for k, _ in ALGOS if self.v_algos[k].get()]
        if not algos:
            raise ValueError("En az bir denetleyici seçin.")
        lv = float(self.v_noise.get()) / 100
        return {"g_fn": g_fn, "r_fn": r_fn, "changes": changes, "t_end": t_end, "algos": algos,
                "noise": (lv * PANEL.voc, lv * PANEL.isc), "seed": int(self.v_seed.get()),
                "t_cell": float(round(self.v_t.get()))}

    def _run(self) -> None:
        try:
            prm = self._read_params()
        except Exception as e:  # noqa: BLE001 - shown to the user
            messagebox.showerror("Geçersiz girdi", str(e))
            return
        self.run_btn.state(["disabled"])
        self.status.config(text="Çalışıyor…")
        threading.Thread(target=self._worker, args=(prm,), daemon=True).start()

    def _worker(self, prm: dict) -> None:
        results = []
        t0 = time.perf_counter()
        try:
            for k in prm["algos"]:
                self.after(0, self.status.config, {"text": f"Çalışıyor: {dict(ALGOS)[k]} …"})
                log = run(make_controller(k), g_fn=prm["g_fn"], r_fn=prm["r_fn"], t_end=prm["t_end"],
                          noise_std=prm["noise"], seed=prm["seed"], t_cell=prm["t_cell"])
                results.append((k, log, summarize(log, prm["changes"])))
            self.after(0, self._show, results, time.perf_counter() - t0)
        except Exception as e:  # noqa: BLE001
            self.after(0, messagebox.showerror, "Hata", str(e))
            self.after(0, self.run_btn.state, ["!disabled"])

    def _show(self, results, elapsed: float) -> None:
        self.ax_p.clear()
        self.ax_d.clear()
        for k, log, _ in results:
            self.ax_p.plot(log["t"], log["p_pv"], color=COLORS[k], lw=0.9, label=dict(ALGOS)[k])
            self.ax_d.plot(log["t"], log["d"], color=COLORS[k], lw=0.9)
        log = results[0][1]
        self.ax_p.plot(log["t"], log["p_opt"], "k:", lw=1.2, label="P_opt (gerçek MPP)")
        self.ax_p.set_ylabel("P (W)")
        self.ax_p.legend(loc="lower right", fontsize=8)
        self.ax_p.set_title(f"{self.v_scen.get()} · σ = {self.v_noise.get():.2f} % · T = {self.v_t.get():.0f} °C")
        self.ax_d.set_ylabel("Görev oranı D")
        self.ax_d.set_xlabel("Zaman (s)")
        for ax in (self.ax_p, self.ax_d):
            ax.grid(alpha=0.3)
        self.fig.tight_layout()
        self.canvas.draw_idle()
        self.table.delete(*self.table.get_children())
        for k, _, s in results:
            conv = "–" if np.isnan(s["conv_avg_ms"]) else f"{s['conv_avg_ms']:.1f}"
            self.table.insert("", "end", values=(dict(ALGOS)[k], f"{s['efficiency_pct']:.2f}", f"{s['rmse_w']:.2f}",
                                                 conv, int(s["conv_failed"])))
        self.status.config(text=f"Bitti ({elapsed:.1f} s). Verim = ΣP_pv / ΣP_opt; yakınsama = ±%2 banda girip kalma süresi.")
        self.run_btn.state(["!disabled"])

    # ------------------------------------------------------------------ fuzzy inference tab
    def _build_fis_tab(self) -> None:
        self.fis = build_fis()
        left = ttk.Frame(self.fis_tab, padding=10)
        left.pack(side="left", fill="y")
        right = ttk.Frame(self.fis_tab, padding=(0, 10, 10, 10))
        right.pack(side="left", fill="both", expand=True)
        self.v_sinc = tk.DoubleVar(value=-0.25)
        self.v_csi = tk.DoubleVar(value=0.0)
        ttk.Label(left, text="Girdiler", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(left, text="SInC (S)").grid(row=1, column=0, sticky="w")
        tk.Scale(left, variable=self.v_sinc, from_=-1.3, to=1.3, resolution=0.01, orient="horizontal",
                 length=260, command=lambda e: self._update_fis()).grid(row=1, column=1)
        ttk.Label(left, text="CSI (S)").grid(row=2, column=0, sticky="w")
        tk.Scale(left, variable=self.v_csi, from_=-0.12, to=0.12, resolution=0.002, orient="horizontal",
                 length=260, command=lambda e: self._update_fis()).grid(row=2, column=1)
        ttk.Label(left, text="SInC < 0: MPP'nin sağı → D artmalı\nSInC > 0: MPP'nin solu → D azalmalı\n"
                             "SInC = 0: MPP'deyiz → ΔD = 0", foreground="#555", justify="left").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=6)
        self.dd_label = ttk.Label(left, text="", font=("Segoe UI", 14, "bold"), foreground="#b91c1c")
        self.dd_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 8))
        ttk.Label(left, text="Ateşlenen kurallar (güçlüden zayıfa)", font=("Segoe UI", 10, "bold")).grid(
            row=5, column=0, columnspan=2, sticky="w")
        self.rules_list = tk.Listbox(left, width=48, height=14, font=("Consolas", 10))
        self.rules_list.grid(row=6, column=0, columnspan=2, sticky="we")
        ttk.Label(left, text="Kural: EĞER SInC=A VE CSI=B → ΔD=C\nGüç w = min(μ_A(SInC), μ_B(CSI))",
                  foreground="#555", justify="left").grid(row=7, column=0, columnspan=2, sticky="w", pady=6)

        self.ffig = Figure(figsize=(9, 7), dpi=100)
        self.f_ax = [self.ffig.add_subplot(3, 1, i) for i in (1, 2, 3)]
        self.fcanvas = FigureCanvasTkAgg(self.ffig, master=right)
        self.fcanvas.get_tk_widget().pack(fill="both", expand=True)
        self._update_fis()

    def _update_fis(self) -> None:
        s, c = float(self.v_sinc.get()), float(self.v_csi.get())
        ex = self.fis.explain(s, c)
        sinc_var, csi_var = self.fis.inputs
        for ax, var, x, rng, name in ((self.f_ax[0], sinc_var, s, (-1.3, 1.3), "SInC"),
                                      (self.f_ax[1], csi_var, c, (-0.12, 0.12), "CSI")):
            ax.clear()
            xs = np.linspace(*rng, 400)
            for lab in var.labels:
                y = var.mf_curve(lab, xs)
                ax.plot(xs, y, lw=1)
                m = var.membership(x)[lab]
                if m > 0:
                    ax.fill_between(xs, 0, np.minimum(y, m), alpha=0.25)
                    ax.text(x, m + 0.03, f"{lab}={m:.2f}", fontsize=8, ha="center")
            ax.axvline(x, color="k", lw=1.5)
            ax.set_title(f"{name} = {x:.3f}: üyelik dereceleri", fontsize=10)
            ax.set_ylim(0, 1.15)
            ax.grid(alpha=0.3)
        ax = self.f_ax[2]
        ax.clear()
        for lab in self.fis.output.labels:
            ax.plot(ex["u"], self.fis.out_mf[lab], color="#bbb", lw=0.8)
        ax.fill_between(ex["u"], 0, ex["aggregated"], color="tab:red", alpha=0.35, label="kırpılmış + birleştirilmiş çıkış")
        ax.axvline(ex["output"], color="tab:red", lw=2, label=f"centroid ΔD = {ex['output']:+.4f}")
        ax.set_title("Çıkış ΔD: max-min birleştirme ve ağırlık merkezi", fontsize=10)
        ax.set_ylim(0, 1.15)
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(alpha=0.3)
        self.ffig.tight_layout()
        self.fcanvas.draw_idle()
        d = ex["output"]
        direction = "D artır (gerilimi düşür)" if d > 1e-6 else "D azalt (gerilimi yükselt)" if d < -1e-6 else "D sabit (MPP)"
        self.dd_label.config(text=f"ΔD = {d:+.4f}   →  {direction}")
        self.rules_list.delete(0, "end")
        for (a, b), out, w in ex["fired"]:
            self.rules_list.insert("end", f"SInC={a:<2} VE CSI={b:<2} → ΔD={out:<2}  w={w:.2f}")


def main() -> None:
    DemoApp().mainloop()


if __name__ == "__main__":
    main()
