"""
Virtual Memory Module
Implements: FIFO, LRU, Optimal, Clock, LFU, MFU page replacement
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
from tkinter import messagebox
from collections import OrderedDict, Counter


def fifo_replace(ref_string, num_frames):
    frames, faults, history, queue = [], 0, [], []
    for page in ref_string:
        fault = page not in frames
        if fault:
            faults += 1
            if len(frames) < num_frames:
                frames.append(page)
                queue.append(page)
            else:
                evicted = queue.pop(0)
                idx = frames.index(evicted)
                frames[idx] = page
                queue.append(page)
        history.append((list(frames), fault, page))
    return history, faults


def lru_replace(ref_string, num_frames):
    frames, faults, history, order = [], 0, [], []
    for page in ref_string:
        fault = page not in frames
        if fault:
            faults += 1
            if len(frames) < num_frames:
                frames.append(page)
            else:
                lru = order[0]
                for p in order:
                    if p in frames:
                        lru = p
                        break
                order_in_frames = [p for p in order if p in frames]
                evict = order_in_frames[0]
                idx = frames.index(evict)
                frames[idx] = page
        if page in order:
            order.remove(page)
        order.append(page)
        history.append((list(frames), fault, page))
    return history, faults


def optimal_replace(ref_string, num_frames):
    frames, faults, history = [], 0, []
    for i, page in enumerate(ref_string):
        fault = page not in frames
        if fault:
            faults += 1
            if len(frames) < num_frames:
                frames.append(page)
            else:
                future = ref_string[i+1:]
                def next_use(p):
                    try:
                        return future.index(p)
                    except ValueError:
                        return float('inf')
                evict = max(frames, key=next_use)
                frames[frames.index(evict)] = page
        history.append((list(frames), fault, page))
    return history, faults


def clock_replace(ref_string, num_frames):
    frames = [None] * num_frames
    use_bits = [0] * num_frames
    hand = 0
    faults, history = 0, []
    for page in ref_string:
        if page in frames:
            use_bits[frames.index(page)] = 1
            history.append((list(f for f in frames if f is not None), False, page))
            continue
        faults += 1
        while True:
            if use_bits[hand] == 0:
                frames[hand] = page
                use_bits[hand] = 1
                hand = (hand + 1) % num_frames
                break
            else:
                use_bits[hand] = 0
                hand = (hand + 1) % num_frames
        history.append((list(f for f in frames if f is not None), True, page))
    return history, faults


def lfu_replace(ref_string, num_frames):
    frames, faults, history = [], 0, []
    freq = Counter()
    for page in ref_string:
        freq[page] += 1
        fault = page not in frames
        if fault:
            faults += 1
            if len(frames) < num_frames:
                frames.append(page)
            else:
                evict = min(frames, key=lambda p: freq[p])
                frames[frames.index(evict)] = page
        history.append((list(frames), fault, page))
    return history, faults


def mfu_replace(ref_string, num_frames):
    frames, faults, history = [], 0, []
    freq = Counter()
    for page in ref_string:
        freq[page] += 1
        fault = page not in frames
        if fault:
            faults += 1
            if len(frames) < num_frames:
                frames.append(page)
            else:
                evict = max(frames, key=lambda p: freq[p])
                frames[frames.index(evict)] = page
        history.append((list(frames), fault, page))
    return history, faults


ALGO_MAP = {
    "FIFO": fifo_replace,
    "LRU": lru_replace,
    "Optimal": optimal_replace,
    "Clock": clock_replace,
    "LFU": lfu_replace,
    "MFU": mfu_replace,
}


class VirtualMemoryFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.ref_string = []
        self.history = []
        self.step = 0
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Left
        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="📄 Virtual Memory Config", font=("Courier New", 14, "bold")).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w")

        # Frames
        fr_frame = ctk.CTkFrame(left, fg_color="transparent")
        fr_frame.grid(row=1, column=0, columnspan=2, padx=12, pady=4, sticky="ew")
        ctk.CTkLabel(fr_frame, text="Frames:", font=("Courier New", 11)).pack(side="left")
        self.frames_var = ctk.IntVar(value=3)
        ctk.CTkSlider(fr_frame, from_=1, to=8, variable=self.frames_var, width=100).pack(side="left", padx=8)
        self.frames_label = ctk.CTkLabel(fr_frame, text="3", font=("Courier New", 12, "bold"), text_color="#4ECDC4")
        self.frames_label.pack(side="left")
        self.frames_var.trace_add("write", lambda *_: self.frames_label.configure(text=str(self.frames_var.get())))

        # Reference string
        ctk.CTkLabel(left, text="Reference String:", font=("Courier New", 11)).grid(
            row=2, column=0, padx=16, pady=(8, 2), sticky="w")
        self.ref_entry = ctk.CTkEntry(left, placeholder_text="e.g. 7 0 1 2 0 3 0 4 2 3 0 3",
                                      font=("Courier New", 11))
        self.ref_entry.grid(row=3, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        ctk.CTkButton(left, text="⚡ Random String", command=self._random_ref,
                      fg_color="#45B7D1", text_color="#000", font=("Courier New", 11)).grid(
            row=4, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        # Algorithm
        ctk.CTkLabel(left, text="Algorithm:", font=("Courier New", 11)).grid(
            row=5, column=0, padx=16, pady=(8, 2), sticky="w")
        self.algo_var = ctk.StringVar(value="FIFO")
        ctk.CTkOptionMenu(left, values=list(ALGO_MAP.keys()), variable=self.algo_var,
                          font=("Courier New", 11), fg_color="#2d2d44",
                          button_color="#4ECDC4", button_hover_color="#3ab8ae").grid(
            row=6, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        # Controls
        ctrl = ctk.CTkFrame(left, fg_color="transparent")
        ctrl.grid(row=7, column=0, columnspan=2, padx=12, pady=(12, 4), sticky="ew")
        ctk.CTkButton(ctrl, text="▶ Run", command=self._run,
                      fg_color="#96CEB4", text_color="#000", font=("Courier New", 12, "bold")).pack(side="left", padx=4, fill="x", expand=True)
        ctk.CTkButton(ctrl, text="⏮", command=self._step_back, width=40,
                      fg_color="#2d2d44", font=("Courier New", 12)).pack(side="left", padx=2)
        ctk.CTkButton(ctrl, text="⏭", command=self._step_forward, width=40,
                      fg_color="#2d2d44", font=("Courier New", 12)).pack(side="left", padx=2)
        ctk.CTkButton(ctrl, text="↺", command=self._reset, width=40,
                      fg_color="#FF6B6B", text_color="#fff", font=("Courier New", 12)).pack(side="left", padx=2)

        # Stats
        self.fault_label = ctk.CTkLabel(left, text="Page Faults: --  |  Fault Rate: --%",
                                        font=("Courier New", 12, "bold"), text_color="#FF6B6B")
        self.fault_label.grid(row=8, column=0, columnspan=2, padx=12, pady=8)

        self.step_label = ctk.CTkLabel(left, text="Step: 0 / 0", font=("Courier New", 11), text_color="#888")
        self.step_label.grid(row=9, column=0, columnspan=2, padx=12, pady=4)

        # Belady compare
        ctk.CTkLabel(left, text="── Belady's Anomaly ──", font=("Courier New", 11), text_color="#FFEAA7").grid(
            row=10, column=0, columnspan=2, padx=12, pady=(12, 4))
        ctk.CTkButton(left, text="📊 Compare FIFO Frames", command=self._beladys_anomaly,
                      fg_color="#FFEAA7", text_color="#000", font=("Courier New", 11)).grid(
            row=11, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        # Right
        right = ctk.CTkFrame(self, corner_radius=12)
        right.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        self.fig, (self.ax_frames, self.ax_faults) = plt.subplots(2, 1, figsize=(8, 6),
                                                                    gridspec_kw={'height_ratios': [3, 1]})
        self.fig.patch.set_facecolor("#1a1a2e")
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)
        self._draw_empty()

    def _random_ref(self):
        pages = random.randint(4, 8)
        length = random.randint(12, 20)
        ref = [random.randint(0, pages-1) for _ in range(length)]
        self.ref_entry.delete(0, "end")
        self.ref_entry.insert(0, " ".join(map(str, ref)))

    def _parse_ref(self):
        try:
            return [int(x) for x in self.ref_entry.get().split()]
        except ValueError:
            messagebox.showerror("Error", "Invalid reference string")
            return []

    def _run(self):
        ref = self._parse_ref()
        if not ref:
            return
        self.ref_string = ref
        nf = self.frames_var.get()
        fn = ALGO_MAP[self.algo_var.get()]
        self.history, faults = fn(ref, nf)
        self.step = len(self.history)
        self._update_fault_label(faults, len(ref))
        self._draw_visualization(self.history, faults, len(ref))
        self.step_label.configure(text=f"Step: {self.step} / {len(self.history)}")

    def _step_forward(self):
        if not self.history:
            self._run()
            self.step = 0
        if self.step < len(self.history):
            self.step += 1
            sub = self.history[:self.step]
            faults = sum(1 for _, f, _ in sub if f)
            self._update_fault_label(faults, len(self.history))
            self._draw_visualization(sub, faults, len(self.history))
            self.step_label.configure(text=f"Step: {self.step} / {len(self.history)}")

    def _step_back(self):
        if self.step > 1:
            self.step -= 1
            sub = self.history[:self.step]
            faults = sum(1 for _, f, _ in sub if f)
            self._update_fault_label(faults, len(self.history))
            self._draw_visualization(sub, faults, len(self.history))
            self.step_label.configure(text=f"Step: {self.step} / {len(self.history)}")

    def _reset(self):
        self.history = []
        self.step = 0
        self.fault_label.configure(text="Page Faults: --  |  Fault Rate: --%")
        self.step_label.configure(text="Step: 0 / 0")
        self._draw_empty()

    def _update_fault_label(self, faults, total):
        rate = faults / total * 100 if total > 0 else 0
        self.fault_label.configure(text=f"Page Faults: {faults}  |  Fault Rate: {rate:.1f}%")

    def _draw_empty(self):
        for ax in [self.ax_frames, self.ax_faults]:
            ax.clear()
            ax.set_facecolor("#12122a")
        self.ax_frames.text(0.5, 0.5, "Run simulation to see visualization",
                            ha='center', va='center', color='#555', fontsize=11, fontfamily='monospace',
                            transform=self.ax_frames.transAxes)
        self.ax_frames.axis('off')
        self.ax_faults.axis('off')
        self.fig.tight_layout()
        self.canvas.draw()

    def _draw_visualization(self, history, faults, total):
        self.ax_frames.clear()
        self.ax_faults.clear()
        self.ax_frames.set_facecolor("#12122a")
        self.ax_faults.set_facecolor("#12122a")
        nf = self.frames_var.get()
        n = len(history)
        all_pages = sorted(set(p for _, _, p in history))
        page_colors = {p: ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
                           "#DDA0DD", "#F7DC6F"][i % 7] for i, p in enumerate(all_pages)}

        for t, (frames_state, fault, page) in enumerate(history):
            for row, f in enumerate(frames_state):
                color = page_colors.get(f, "#888")
                rect = plt.Rectangle((t, nf - row - 1), 0.9, 0.9, color=color,
                                     edgecolor='#FF6B6B' if fault and f == page else '#333',
                                     linewidth=2 if fault and f == page else 0.5)
                self.ax_frames.add_patch(rect)
                self.ax_frames.text(t + 0.45, nf - row - 0.55, str(f),
                                    ha='center', va='center', fontsize=9,
                                    fontfamily='monospace', color='#000', fontweight='bold')
            self.ax_frames.text(t + 0.45, nf + 0.3, str(page),
                                ha='center', va='center', fontsize=9,
                                fontfamily='monospace', color='#ccc')
            if fault:
                self.ax_frames.text(t + 0.45, -0.4, "F", ha='center', va='center',
                                    fontsize=9, color='#FF6B6B', fontweight='bold', fontfamily='monospace')

        self.ax_frames.set_xlim(-0.2, n + 0.2)
        self.ax_frames.set_ylim(-0.8, nf + 0.8)
        self.ax_frames.set_xticks([])
        self.ax_frames.set_yticks(range(nf))
        self.ax_frames.set_yticklabels([f"F{i}" for i in range(nf)], color='#888', fontfamily='monospace')
        self.ax_frames.set_title(f"{self.algo_var.get()} | {faults} faults / {total} refs",
                                 color='#ccc', fontfamily='monospace', fontsize=10)
        for sp in self.ax_frames.spines.values():
            sp.set_color('#333')

        # Fault timeline
        fault_times = [t for t, (_, f, _) in enumerate(history) if f]
        cumulative = list(range(1, len(fault_times) + 1))
        if fault_times:
            self.ax_faults.step([0] + fault_times + [n], [0] + cumulative + [cumulative[-1]],
                                color='#FF6B6B', linewidth=2)
            self.ax_faults.fill_between([0] + fault_times + [n], [0] + cumulative + [cumulative[-1]],
                                        alpha=0.2, color='#FF6B6B', step='pre')
        self.ax_faults.set_xlim(0, n)
        self.ax_faults.set_xlabel("Reference Step", color='#888', fontfamily='monospace')
        self.ax_faults.set_ylabel("Cumulative\nFaults", color='#888', fontfamily='monospace', fontsize=8)
        self.ax_faults.tick_params(colors='#888')
        for sp in self.ax_faults.spines.values():
            sp.set_color('#333')

        self.fig.tight_layout()
        self.canvas.draw()

    def _beladys_anomaly(self):
        ref = self._parse_ref()
        if not ref:
            return
        max_frames = 8
        fault_counts = []
        for nf in range(1, max_frames + 1):
            _, faults = fifo_replace(ref, nf)
            fault_counts.append(faults)

        win = ctk.CTkToplevel(self)
        win.title("Belady's Anomaly — FIFO Page Faults vs Frame Count")
        win.geometry("700x400")
        win.configure(fg_color="#12122a")

        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#12122a")
        ax.plot(range(1, max_frames + 1), fault_counts, 'o-', color='#FF6B6B', linewidth=2, markersize=8)
        ax.set_xlabel("Number of Frames", color='#aaa', fontfamily='monospace')
        ax.set_ylabel("Page Faults", color='#aaa', fontfamily='monospace')
        ax.set_title("Belady's Anomaly — FIFO (more frames ≠ fewer faults)", color='#ccc', fontfamily='monospace')
        ax.tick_params(colors='#aaa')
        for sp in ax.spines.values():
            sp.set_color('#333')
        anomalies = [i for i in range(1, len(fault_counts)) if fault_counts[i] > fault_counts[i-1]]
        for a in anomalies:
            ax.annotate("⚠ Anomaly", xy=(a+1, fault_counts[a]),
                        xytext=(a+1.3, fault_counts[a]+0.5),
                        color='#FFEAA7', fontsize=9, fontfamily='monospace',
                        arrowprops=dict(arrowstyle='->', color='#FFEAA7'))
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)
        canvas.draw()
