"""
Disk Management Module
Implements: FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
from tkinter import messagebox
import threading
import time


def disk_fcfs(head, requests, disk_size):
    seq = [head] + requests
    moves = sum(abs(seq[i+1] - seq[i]) for i in range(len(seq)-1))
    return requests[:], moves


def disk_sstf(head, requests, disk_size):
    reqs = list(requests)
    seq, curr = [], head
    while reqs:
        nearest = min(reqs, key=lambda x: abs(x - curr))
        seq.append(nearest)
        curr = nearest
        reqs.remove(nearest)
    moves = sum(abs([head]+seq)[i+1] - ([head]+seq)[i] for i in range(len(seq)))
    moves = sum(abs(s - t) for s, t in zip([head]+seq, seq))
    return seq, moves


def disk_scan(head, requests, disk_size, direction=1):
    left = sorted([r for r in requests if r < head], reverse=True)
    right = sorted([r for r in requests if r >= head])
    if direction == 1:
        seq = right + [disk_size - 1] + left
    else:
        seq = left + [0] + right
    all_pts = [head] + seq
    moves = sum(abs(all_pts[i+1] - all_pts[i]) for i in range(len(all_pts)-1))
    return seq, moves


def disk_cscan(head, requests, disk_size):
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])
    seq = right + [disk_size - 1, 0] + left
    all_pts = [head] + seq
    moves = sum(abs(all_pts[i+1] - all_pts[i]) for i in range(len(all_pts)-1))
    return seq, moves


def disk_look(head, requests, disk_size, direction=1):
    left = sorted([r for r in requests if r < head], reverse=True)
    right = sorted([r for r in requests if r >= head])
    if direction == 1:
        seq = right + left
    else:
        seq = left + right
    all_pts = [head] + seq
    moves = sum(abs(all_pts[i+1] - all_pts[i]) for i in range(len(all_pts)-1))
    return seq, moves


def disk_clook(head, requests, disk_size):
    left = sorted([r for r in requests if r < head])
    right = sorted([r for r in requests if r >= head])
    seq = right + left
    all_pts = [head] + seq
    moves = sum(abs(all_pts[i+1] - all_pts[i]) for i in range(len(all_pts)-1))
    return seq, moves


DISK_ALGOS = {
    "FCFS": disk_fcfs,
    "SSTF": disk_sstf,
    "SCAN": disk_scan,
    "C-SCAN": disk_cscan,
    "LOOK": disk_look,
    "C-LOOK": disk_clook,
}


class DiskManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.requests = []
        self.seq = []
        self.anim_running = False
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Left
        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="💿 Disk Configuration", font=("Courier New", 14, "bold")).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w")

        # Disk size
        ds_frame = ctk.CTkFrame(left, fg_color="transparent")
        ds_frame.grid(row=1, column=0, columnspan=2, padx=12, pady=4, sticky="ew")
        ctk.CTkLabel(ds_frame, text="Disk Size:", font=("Courier New", 11)).pack(side="left")
        self.disk_size_var = ctk.IntVar(value=200)
        ctk.CTkSlider(ds_frame, from_=50, to=500, variable=self.disk_size_var, width=100).pack(side="left", padx=8)
        self.disk_size_label = ctk.CTkLabel(ds_frame, text="200", font=("Courier New", 11, "bold"), text_color="#4ECDC4")
        self.disk_size_label.pack(side="left")
        self.disk_size_var.trace_add("write", lambda *_: self.disk_size_label.configure(text=str(self.disk_size_var.get())))

        # Head position
        hp_frame = ctk.CTkFrame(left, fg_color="transparent")
        hp_frame.grid(row=2, column=0, columnspan=2, padx=12, pady=4, sticky="ew")
        ctk.CTkLabel(hp_frame, text="Head Position:", font=("Courier New", 11)).pack(side="left")
        self.head_var = ctk.IntVar(value=50)
        ctk.CTkSlider(hp_frame, from_=0, to=499, variable=self.head_var, width=100).pack(side="left", padx=8)
        self.head_label = ctk.CTkLabel(hp_frame, text="50", font=("Courier New", 11, "bold"), text_color="#FFEAA7")
        self.head_label.pack(side="left")
        self.head_var.trace_add("write", lambda *_: self.head_label.configure(text=str(self.head_var.get())))

        # Requests
        ctk.CTkLabel(left, text="Request Queue:", font=("Courier New", 11)).grid(
            row=3, column=0, padx=16, pady=(8, 2), sticky="w")
        self.req_entry = ctk.CTkEntry(left, placeholder_text="e.g. 98 183 37 122 14 124 65",
                                      font=("Courier New", 11))
        self.req_entry.grid(row=4, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        ctk.CTkButton(left, text="⚡ Random Queue", command=self._random_requests,
                      fg_color="#45B7D1", text_color="#000", font=("Courier New", 11)).grid(
            row=5, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        # Algorithm
        ctk.CTkLabel(left, text="Algorithm:", font=("Courier New", 11)).grid(
            row=6, column=0, padx=16, pady=(8, 2), sticky="w")
        self.algo_var = ctk.StringVar(value="FCFS")
        ctk.CTkOptionMenu(left, values=list(DISK_ALGOS.keys()), variable=self.algo_var,
                          font=("Courier New", 11), fg_color="#2d2d44",
                          button_color="#4ECDC4", button_hover_color="#3ab8ae").grid(
            row=7, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        # Speed
        sp_frame = ctk.CTkFrame(left, fg_color="transparent")
        sp_frame.grid(row=8, column=0, columnspan=2, padx=12, pady=4, sticky="ew")
        ctk.CTkLabel(sp_frame, text="Anim Speed:", font=("Courier New", 11)).pack(side="left")
        self.speed_var = ctk.DoubleVar(value=0.3)
        ctk.CTkSlider(sp_frame, from_=0.05, to=1.0, variable=self.speed_var, width=100).pack(side="left", padx=8)

        # Controls
        ctrl = ctk.CTkFrame(left, fg_color="transparent")
        ctrl.grid(row=9, column=0, columnspan=2, padx=12, pady=(12, 4), sticky="ew")
        ctk.CTkButton(ctrl, text="▶ Simulate", command=self._run_simulation,
                      fg_color="#96CEB4", text_color="#000", font=("Courier New", 12, "bold")).pack(
            side="left", padx=4, fill="x", expand=True)
        ctk.CTkButton(ctrl, text="📊 Compare", command=self._compare_all,
                      fg_color="#FFEAA7", text_color="#000", font=("Courier New", 11)).pack(side="left", padx=4)
        ctk.CTkButton(ctrl, text="↺", command=self._reset, width=40,
                      fg_color="#FF6B6B", text_color="#fff", font=("Courier New", 12)).pack(side="left", padx=2)

        # Results
        self.result_box = ctk.CTkTextbox(left, height=140, font=("Courier New", 10),
                                         fg_color="#1a1a2e", text_color="#4ECDC4")
        self.result_box.grid(row=10, column=0, columnspan=2, padx=12, pady=(8, 8), sticky="ew")

        # Right
        right = ctk.CTkFrame(self, corner_radius=12)
        right.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.fig.patch.set_facecolor("#1a1a2e")
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)
        self._draw_empty()

    def _random_requests(self):
        disk_size = self.disk_size_var.get()
        n = random.randint(6, 12)
        reqs = [random.randint(0, disk_size - 1) for _ in range(n)]
        self.req_entry.delete(0, "end")
        self.req_entry.insert(0, " ".join(map(str, reqs)))

    def _parse_requests(self):
        try:
            return [int(x) for x in self.req_entry.get().split()]
        except ValueError:
            messagebox.showerror("Error", "Invalid request queue")
            return []

    def _run_simulation(self):
        reqs = self._parse_requests()
        if not reqs:
            return
        self.requests = reqs
        head = self.head_var.get()
        disk_size = self.disk_size_var.get()
        algo_fn = DISK_ALGOS[self.algo_var.get()]
        self.seq, moves = algo_fn(head, reqs, disk_size)
        self._update_results(moves)
        self._animate_disk(head, self.seq, disk_size)

    def _update_results(self, moves):
        reqs = self.requests
        head = self.head_var.get()
        algo = self.algo_var.get()
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("end",
            f"Algorithm      : {algo}\n"
            f"Initial Head   : {head}\n"
            f"Disk Size      : {self.disk_size_var.get()}\n"
            f"Requests       : {reqs}\n"
            f"Seek Sequence  : {self.seq}\n"
            f"Total Seek Time: {moves} cylinders\n"
        )
        self.result_box.configure(state="disabled")

    def _animate_disk(self, head, seq, disk_size):
        all_pts = [head] + seq
        self.ax.clear()
        self.ax.set_facecolor("#12122a")

        def draw_step(n):
            self.ax.clear()
            self.ax.set_facecolor("#12122a")
            pts = all_pts[:n+1]
            times = list(range(len(pts)))
            self.ax.plot(times, pts, 'o-', color='#4ECDC4', linewidth=2, markersize=8, zorder=3)
            self.ax.plot(times[0], pts[0], 's', color='#FFEAA7', markersize=12, zorder=4)
            if n > 0:
                self.ax.plot(times[-1], pts[-1], 'D', color='#FF6B6B', markersize=10, zorder=4)
            for t, p in zip(times, pts):
                self.ax.annotate(str(p), (t, p), textcoords="offset points", xytext=(5, 5),
                                 color='#ccc', fontsize=8, fontfamily='monospace')
            self.ax.set_xlim(-0.5, len(all_pts))
            self.ax.set_ylim(-10, disk_size + 10)
            self.ax.set_xlabel("Request Order", color='#888', fontfamily='monospace')
            self.ax.set_ylabel("Cylinder/Track", color='#888', fontfamily='monospace')
            self.ax.set_title(f"Disk Scheduling — {self.algo_var.get()} | Seek: {sum(abs(all_pts[i+1]-all_pts[i]) for i in range(n))} cylinders",
                              color='#ccc', fontfamily='monospace', fontsize=10)
            self.ax.tick_params(colors='#888')
            for sp in self.ax.spines.values():
                sp.set_color('#333')
            legend_elems = [
                mpatches.Patch(color='#FFEAA7', label=f'Start: {head}'),
                mpatches.Patch(color='#4ECDC4', label='Seek path'),
                mpatches.Patch(color='#FF6B6B', label='Current'),
            ]
            self.ax.legend(handles=legend_elems, facecolor='#1a1a2e', edgecolor='#333',
                           labelcolor='white', fontsize=8)
            self.fig.tight_layout()
            self.canvas.draw()

        def animate():
            for i in range(len(all_pts)):
                draw_step(i)
                time.sleep(self.speed_var.get())

        t = threading.Thread(target=animate, daemon=True)
        t.start()

    def _reset(self):
        self.requests = []
        self.seq = []
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.configure(state="disabled")
        self._draw_empty()

    def _draw_empty(self):
        self.ax.clear()
        self.ax.set_facecolor("#12122a")
        self.ax.text(0.5, 0.5, "Configure and run a disk simulation",
                     ha='center', va='center', color='#555', fontsize=11,
                     fontfamily='monospace', transform=self.ax.transAxes)
        self.ax.axis('off')
        self.fig.tight_layout()
        self.canvas.draw()

    def _compare_all(self):
        reqs = self._parse_requests()
        if not reqs:
            return
        head = self.head_var.get()
        disk_size = self.disk_size_var.get()
        results = {}
        for name, fn in DISK_ALGOS.items():
            _, moves = fn(head, reqs, disk_size)
            results[name] = moves

        win = ctk.CTkToplevel(self)
        win.title("Disk Algorithm Comparison — Total Seek Time")
        win.geometry("700x420")
        win.configure(fg_color="#12122a")

        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#12122a")
        names = list(results.keys())
        values = list(results.values())
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]
        bars = ax.bar(names, values, color=colors, edgecolor='#333')
        ax.set_title(f"Total Seek Time Comparison (Head={head})", color='#ccc', fontfamily='monospace')
        ax.set_ylabel("Total Cylinders Moved", color='#aaa', fontfamily='monospace')
        ax.tick_params(colors='#aaa')
        for sp in ['top', 'right']:
            ax.spines[sp].set_visible(False)
        for sp in ['bottom', 'left']:
            ax.spines[sp].set_color('#333')
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    str(val), ha='center', color='#ccc', fontsize=10, fontfamily='monospace')
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)
        canvas.draw()
