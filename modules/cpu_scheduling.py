"""
CPU Scheduling Module
Implements: FCFS, SJF (P/NP), Priority (P/NP), Round Robin, MLQ, MLFQ
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import json
import os
from tkinter import filedialog, messagebox


PROCESS_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
    "#F0B27A", "#82E0AA", "#F1948A", "#AED6F1", "#A9DFBF",
]


def fcfs(processes):
    procs = sorted(processes, key=lambda p: p['arrival'])
    timeline, time = [], 0
    for p in procs:
        if time < p['arrival']:
            time = p['arrival']
        start = time
        time += p['burst']
        timeline.append({'pid': p['pid'], 'start': start, 'end': time})
    return timeline, compute_metrics(processes, timeline)


def sjf_non_preemptive(processes):
    procs = [dict(p) for p in processes]
    timeline, time, done = [], 0, []
    while len(done) < len(procs):
        available = [p for p in procs if p['arrival'] <= time and p['pid'] not in done]
        if not available:
            time += 1
            continue
        p = min(available, key=lambda x: x['burst'])
        done.append(p['pid'])
        start = time
        time += p['burst']
        timeline.append({'pid': p['pid'], 'start': start, 'end': time})
    return timeline, compute_metrics(processes, timeline)


def sjf_preemptive(processes):
    procs = [dict(p) for p in processes]
    for p in procs:
        p['remaining'] = p['burst']
    timeline, time = [], 0
    total = sum(p['burst'] for p in procs)
    current = None
    seg_start = 0
    for _ in range(total + max(p['arrival'] for p in procs) + 1):
        available = [p for p in procs if p['arrival'] <= time and p['remaining'] > 0]
        if not available:
            time += 1
            continue
        chosen = min(available, key=lambda x: x['remaining'])
        if current != chosen['pid']:
            if current is not None:
                timeline.append({'pid': current, 'start': seg_start, 'end': time})
            current = chosen['pid']
            seg_start = time
        chosen['remaining'] -= 1
        time += 1
        if chosen['remaining'] == 0:
            timeline.append({'pid': current, 'start': seg_start, 'end': time})
            current = None
        if all(p['remaining'] == 0 for p in procs):
            break
    if current is not None:
        timeline.append({'pid': current, 'start': seg_start, 'end': time})
    timeline = merge_timeline(timeline)
    return timeline, compute_metrics(processes, timeline)


def priority_non_preemptive(processes):
    procs = [dict(p) for p in processes]
    timeline, time, done = [], 0, []
    while len(done) < len(procs):
        available = [p for p in procs if p['arrival'] <= time and p['pid'] not in done]
        if not available:
            time += 1
            continue
        p = min(available, key=lambda x: x.get('priority', 0))
        done.append(p['pid'])
        start = time
        time += p['burst']
        timeline.append({'pid': p['pid'], 'start': start, 'end': time})
    return timeline, compute_metrics(processes, timeline)


def priority_preemptive(processes):
    procs = [dict(p) for p in processes]
    for p in procs:
        p['remaining'] = p['burst']
    timeline, time = [], 0
    current = None
    seg_start = 0
    max_time = sum(p['burst'] for p in procs) + max(p['arrival'] for p in procs) + 5
    for _ in range(max_time):
        available = [p for p in procs if p['arrival'] <= time and p['remaining'] > 0]
        if not available:
            time += 1
            continue
        chosen = min(available, key=lambda x: x.get('priority', 0))
        if current != chosen['pid']:
            if current is not None:
                timeline.append({'pid': current, 'start': seg_start, 'end': time})
            current = chosen['pid']
            seg_start = time
        chosen['remaining'] -= 1
        time += 1
        if chosen['remaining'] == 0:
            timeline.append({'pid': current, 'start': seg_start, 'end': time})
            current = None
        if all(p['remaining'] == 0 for p in procs):
            break
    if current is not None:
        timeline.append({'pid': current, 'start': seg_start, 'end': time})
    timeline = merge_timeline(timeline)
    return timeline, compute_metrics(processes, timeline)


def round_robin(processes, quantum=2):
    procs = [dict(p) for p in processes]
    for p in procs:
        p['remaining'] = p['burst']
    queue, timeline, time = [], [], 0
    arrived = set()
    remaining_procs = sorted(procs, key=lambda x: x['arrival'])
    ready_queue = []
    i = 0
    while True:
        while i < len(remaining_procs) and remaining_procs[i]['arrival'] <= time:
            ready_queue.append(remaining_procs[i])
            i += 1
        if not ready_queue:
            if i < len(remaining_procs):
                time = remaining_procs[i]['arrival']
                continue
            else:
                break
        p = ready_queue.pop(0)
        run = min(quantum, p['remaining'])
        start = time
        time += run
        p['remaining'] -= run
        timeline.append({'pid': p['pid'], 'start': start, 'end': time})
        while i < len(remaining_procs) and remaining_procs[i]['arrival'] <= time:
            ready_queue.append(remaining_procs[i])
            i += 1
        if p['remaining'] > 0:
            ready_queue.append(p)
    return timeline, compute_metrics(processes, timeline)


def multilevel_queue(processes, quantum=2):
    fg = [p for p in processes if p.get('queue', 0) == 0]
    bg = [p for p in processes if p.get('queue', 0) != 0]
    t1, m1 = round_robin(fg, quantum) if fg else ([], {})
    offset = max((s['end'] for s in t1), default=0)
    bg_shifted = [dict(p, arrival=p['arrival'] + offset) for p in bg]
    t2, m2 = fcfs(bg_shifted) if bg_shifted else ([], {})
    return t1 + t2, compute_metrics(processes, t1 + t2)


def mlfq(processes, quanta=None):
    if quanta is None:
        quanta = [2, 4, 8]
    procs = [dict(p, remaining=p['burst'], queue_level=0) for p in processes]
    timeline, time = [], 0
    queues = [[] for _ in quanta]
    arrived = set()
    remaining = sorted(procs, key=lambda x: x['arrival'])
    idx = 0
    while True:
        while idx < len(remaining) and remaining[idx]['arrival'] <= time:
            queues[0].append(remaining[idx])
            idx += 1
        found = False
        for level, q in enumerate(queues):
            if not q:
                continue
            p = q.pop(0)
            found = True
            qt = quanta[level]
            run = min(qt, p['remaining'])
            start = time
            time += run
            p['remaining'] -= run
            timeline.append({'pid': p['pid'], 'start': start, 'end': time})
            while idx < len(remaining) and remaining[idx]['arrival'] <= time:
                queues[0].append(remaining[idx])
                idx += 1
            if p['remaining'] > 0:
                next_level = min(level + 1, len(quanta) - 1)
                queues[next_level].append(p)
            break
        if not found:
            if idx < len(remaining):
                time = remaining[idx]['arrival']
            else:
                break
    return timeline, compute_metrics(processes, timeline)


def merge_timeline(timeline):
    if not timeline:
        return timeline
    merged = [timeline[0].copy()]
    for seg in timeline[1:]:
        if seg['pid'] == merged[-1]['pid'] and seg['start'] == merged[-1]['end']:
            merged[-1]['end'] = seg['end']
        else:
            merged.append(seg.copy())
    return merged


def compute_metrics(processes, timeline):
    metrics = {}
    for p in processes:
        pid = p['pid']
        segs = [s for s in timeline if s['pid'] == pid]
        if not segs:
            continue
        finish = max(s['end'] for s in segs)
        tat = finish - p['arrival']
        wt = tat - p['burst']
        metrics[pid] = {'turnaround': tat, 'waiting': wt, 'finish': finish}
    if not metrics:
        return {'avg_waiting': 0, 'avg_turnaround': 0, 'utilization': 0, 'throughput': 0, 'per_process': {}}
    avg_wt = sum(v['waiting'] for v in metrics.values()) / len(metrics)
    avg_tat = sum(v['turnaround'] for v in metrics.values()) / len(metrics)
    total_time = max(s['end'] for s in timeline) if timeline else 1
    busy = sum(s['end'] - s['start'] for s in timeline)
    utilization = (busy / total_time * 100) if total_time > 0 else 0
    throughput = len(metrics) / total_time if total_time > 0 else 0
    return {
        'avg_waiting': avg_wt,
        'avg_turnaround': avg_tat,
        'utilization': utilization,
        'throughput': throughput,
        'per_process': metrics
    }


class CPUSchedulingFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.processes = []
        self.timeline = []
        self.color_map = {}
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="⚙ Process Configuration", font=("Courier New", 14, "bold")).grid(
            row=0, column=0, columnspan=4, padx=16, pady=(16, 8), sticky="w")

        fields = [("PID", "P1"), ("Arrival", "0"), ("Burst", "5"), ("Priority", "1")]
        self.entries = {}
        for i, (label, default) in enumerate(fields):
            ctk.CTkLabel(left, text=label, font=("Courier New", 11)).grid(row=1, column=i, padx=6, pady=4)
            e = ctk.CTkEntry(left, width=60, placeholder_text=default, font=("Courier New", 11))
            e.grid(row=2, column=i, padx=6, pady=4)
            self.entries[label] = e

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.grid(row=3, column=0, columnspan=4, padx=8, pady=4, sticky="ew")
        ctk.CTkButton(btn_row, text="+ Add", command=self._add_process, width=80,
                      fg_color="#4ECDC4", text_color="#000", font=("Courier New", 11, "bold")).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="⚡ Random", command=self._random_processes, width=90,
                      fg_color="#45B7D1", text_color="#000", font=("Courier New", 11, "bold")).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="🗑 Clear", command=self._clear_processes, width=80,
                      fg_color="#FF6B6B", text_color="#fff", font=("Courier New", 11, "bold")).pack(side="left", padx=4)

        self.process_list = ctk.CTkTextbox(left, height=160, font=("Courier New", 11),
                                           fg_color="#1a1a2e", text_color="#4ECDC4")
        self.process_list.grid(row=4, column=0, columnspan=4, padx=12, pady=8, sticky="ew")
        self.process_list.insert("end", "PID  ARR  BST  PRI\n" + "-"*20 + "\n")
        self.process_list.configure(state="disabled")

        ctk.CTkLabel(left, text="Algorithm", font=("Courier New", 12, "bold")).grid(
            row=5, column=0, columnspan=4, padx=16, pady=(8, 4), sticky="w")

        self.algo_var = ctk.StringVar(value="FCFS")
        algos = ["FCFS", "SJF (Non-Preemptive)", "SJF (Preemptive)",
                 "Priority (Non-Preemptive)", "Priority (Preemptive)",
                 "Round Robin", "Multilevel Queue", "MLFQ"]
        self.algo_menu = ctk.CTkOptionMenu(left, values=algos, variable=self.algo_var,
                                           font=("Courier New", 11), width=220,
                                           fg_color="#2d2d44", button_color="#4ECDC4",
                                           button_hover_color="#3ab8ae")
        self.algo_menu.grid(row=6, column=0, columnspan=4, padx=12, pady=4, sticky="ew")

        qt_frame = ctk.CTkFrame(left, fg_color="transparent")
        qt_frame.grid(row=7, column=0, columnspan=4, padx=12, pady=4, sticky="ew")
        ctk.CTkLabel(qt_frame, text="Time Quantum:", font=("Courier New", 11)).pack(side="left")
        self.quantum_var = ctk.IntVar(value=2)
        ctk.CTkSlider(qt_frame, from_=1, to=10, variable=self.quantum_var, width=120).pack(side="left", padx=8)
        self.quantum_label = ctk.CTkLabel(qt_frame, text="2", font=("Courier New", 11, "bold"), text_color="#4ECDC4")
        self.quantum_label.pack(side="left")
        self.quantum_var.trace_add("write", lambda *_: self.quantum_label.configure(text=str(self.quantum_var.get())))

        btn2 = ctk.CTkFrame(left, fg_color="transparent")
        btn2.grid(row=8, column=0, columnspan=4, padx=8, pady=(4, 8), sticky="ew")
        ctk.CTkButton(btn2, text="▶ Run Simulation", command=self._run_simulation,
                      fg_color="#96CEB4", text_color="#000", font=("Courier New", 13, "bold"), height=36).pack(
            side="left", padx=4, fill="x", expand=True)
        ctk.CTkButton(btn2, text="⊞ Compare All", command=self._compare_all,
                      fg_color="#FFEAA7", text_color="#000", font=("Courier New", 12, "bold"), height=36).pack(
            side="left", padx=4)

        io_frame = ctk.CTkFrame(left, fg_color="transparent")
        io_frame.grid(row=9, column=0, columnspan=4, padx=8, pady=(0, 8), sticky="ew")
        ctk.CTkButton(io_frame, text="💾 Save", command=self._save_processes, width=70,
                      fg_color="#2d2d44", font=("Courier New", 11)).pack(side="left", padx=4)
        ctk.CTkButton(io_frame, text="📂 Load", command=self._load_processes, width=70,
                      fg_color="#2d2d44", font=("Courier New", 11)).pack(side="left", padx=4)

        right = ctk.CTkFrame(self, corner_radius=12)
        right.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        self.metrics_frame = ctk.CTkFrame(right, height=80, corner_radius=8, fg_color="#1a1a2e")
        self.metrics_frame.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        self.metrics_frame.grid_propagate(False)
        self.metric_labels = {}
        for i, key in enumerate(["Avg Wait", "Avg TAT", "CPU Util%", "Throughput"]):
            f = ctk.CTkFrame(self.metrics_frame, fg_color="transparent")
            f.grid(row=0, column=i, padx=16, pady=8)
            ctk.CTkLabel(f, text=key, font=("Courier New", 10), text_color="#888").pack()
            lbl = ctk.CTkLabel(f, text="--", font=("Courier New", 16, "bold"), text_color="#4ECDC4")
            lbl.pack()
            self.metric_labels[key] = lbl
        self.metrics_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        chart_frame = ctk.CTkFrame(right, corner_radius=8)
        chart_frame.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.fig.patch.set_facecolor("#1a1a2e")
        self.ax.set_facecolor("#12122a")
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self._draw_empty_gantt()

    def _draw_empty_gantt(self):
        self.ax.clear()
        self.ax.set_facecolor("#12122a")
        self.ax.set_xlim(0, 20)
        self.ax.set_ylim(0, 1)
        self.ax.text(10, 0.5, "Run a simulation to see the Gantt chart",
                     ha='center', va='center', color='#555', fontsize=12, fontfamily='monospace')
        self.ax.axis('off')
        self.fig.tight_layout()
        self.canvas.draw()

    def _add_process(self):
        try:
            pid = self.entries["PID"].get().strip() or f"P{len(self.processes)+1}"
            arr = int(self.entries["Arrival"].get() or 0)
            burst = int(self.entries["Burst"].get() or 1)
            pri = int(self.entries["Priority"].get() or 1)
            if burst <= 0:
                raise ValueError("Burst must be > 0")
            if any(p['pid'] == pid for p in self.processes):
                messagebox.showerror("Error", f"PID '{pid}' already exists")
                return
            self.processes.append({'pid': pid, 'arrival': arr, 'burst': burst, 'priority': pri, 'queue': 0})
            self._refresh_list()
            for e in self.entries.values():
                e.delete(0, "end")
            # Auto-set next PID
            self.entries["PID"].insert(0, f"P{len(self.processes)+1}")
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def _random_processes(self):
        self.processes.clear()
        n = random.randint(4, 7)
        for i in range(n):
            self.processes.append({
                'pid': f"P{i+1}",
                'arrival': random.randint(0, 8),
                'burst': random.randint(1, 10),
                'priority': random.randint(1, 5),
                'queue': random.randint(0, 1)
            })
        self._refresh_list()

    def _clear_processes(self):
        self.processes.clear()
        self._refresh_list()
        self._draw_empty_gantt()

    def _refresh_list(self):
        self.process_list.configure(state="normal")
        self.process_list.delete("1.0", "end")
        self.process_list.insert("end", "PID    ARR  BST  PRI\n" + "-"*22 + "\n")
        for p in self.processes:
            self.process_list.insert("end", f"{p['pid']:<7}{p['arrival']:<5}{p['burst']:<5}{p['priority']}\n")
        self.process_list.configure(state="disabled")

    def _run_simulation(self):
        if not self.processes:
            messagebox.showwarning("No Processes", "Please add processes first.")
            return
        algo = self.algo_var.get()
        qt = self.quantum_var.get()
        try:
            if algo == "FCFS":
                timeline, metrics = fcfs(self.processes)
            elif algo == "SJF (Non-Preemptive)":
                timeline, metrics = sjf_non_preemptive(self.processes)
            elif algo == "SJF (Preemptive)":
                timeline, metrics = sjf_preemptive(self.processes)
            elif algo == "Priority (Non-Preemptive)":
                timeline, metrics = priority_non_preemptive(self.processes)
            elif algo == "Priority (Preemptive)":
                timeline, metrics = priority_preemptive(self.processes)
            elif algo == "Round Robin":
                timeline, metrics = round_robin(self.processes, qt)
            elif algo == "Multilevel Queue":
                timeline, metrics = multilevel_queue(self.processes, qt)
            else:
                timeline, metrics = mlfq(self.processes)
            self.timeline = timeline
            self._update_metrics(metrics)
            self._draw_gantt(timeline)
        except Exception as e:
            messagebox.showerror("Simulation Error", str(e))

    def _update_metrics(self, m):
        self.metric_labels["Avg Wait"].configure(text=f"{m['avg_waiting']:.2f}")
        self.metric_labels["Avg TAT"].configure(text=f"{m['avg_turnaround']:.2f}")
        self.metric_labels["CPU Util%"].configure(text=f"{m['utilization']:.1f}%")
        self.metric_labels["Throughput"].configure(text=f"{m['throughput']:.3f}")

    def _draw_gantt(self, timeline):
        self.ax.clear()
        self.ax.set_facecolor("#12122a")
        pids = sorted(set(s['pid'] for s in timeline))
        self.color_map = {pid: PROCESS_COLORS[i % len(PROCESS_COLORS)] for i, pid in enumerate(pids)}
        for seg in timeline:
            color = self.color_map[seg['pid']]
            self.ax.barh(0, seg['end'] - seg['start'], left=seg['start'], height=0.5,
                         color=color, edgecolor='#000', linewidth=0.5)
            mid = (seg['start'] + seg['end']) / 2
            if seg['end'] - seg['start'] > 0.5:
                self.ax.text(mid, 0, seg['pid'], ha='center', va='center',
                             color='black', fontsize=9, fontweight='bold', fontfamily='monospace')
        max_t = max(s['end'] for s in timeline)
        self.ax.set_xlim(0, max_t + 0.5)
        self.ax.set_ylim(-0.5, 0.8)
        self.ax.set_yticks([])
        self.ax.set_xlabel("Time", color='#aaa', fontfamily='monospace')
        self.ax.tick_params(colors='#aaa')
        self.ax.spines['bottom'].set_color('#333')
        for sp in ['top', 'left', 'right']:
            self.ax.spines[sp].set_visible(False)
        legend = [mpatches.Patch(color=self.color_map[pid], label=pid) for pid in pids]
        self.ax.legend(handles=legend, loc='upper right', fontsize=8,
                       facecolor='#1a1a2e', edgecolor='#333', labelcolor='white')
        self.ax.set_title(f"Gantt Chart — {self.algo_var.get()}", color='#ccc',
                          fontfamily='monospace', fontsize=11)
        self.fig.tight_layout()
        self.canvas.draw()

    def _compare_all(self):
        if not self.processes:
            messagebox.showwarning("No Processes", "Please add processes first.")
            return
        qt = self.quantum_var.get()
        algos = {
            "FCFS": fcfs(self.processes),
            "SJF-NP": sjf_non_preemptive(self.processes),
            "SJF-P": sjf_preemptive(self.processes),
            "Pri-NP": priority_non_preemptive(self.processes),
            "Pri-P": priority_preemptive(self.processes),
            f"RR(q={qt})": round_robin(self.processes, qt),
        }
        win = ctk.CTkToplevel(self)
        win.title("Algorithm Comparison")
        win.geometry("900x500")
        win.configure(fg_color="#12122a")
        names = list(algos.keys())
        avg_wt = [algos[a][1]['avg_waiting'] for a in names]
        avg_tat = [algos[a][1]['avg_turnaround'] for a in names]
        util = [algos[a][1]['utilization'] for a in names]
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        fig.patch.set_facecolor("#1a1a2e")
        for ax, data, title, color in zip(axes,
                [avg_wt, avg_tat, util],
                ["Avg Waiting Time", "Avg Turnaround Time", "CPU Utilization %"],
                ["#FF6B6B", "#4ECDC4", "#96CEB4"]):
            ax.set_facecolor("#12122a")
            bars = ax.bar(names, data, color=color, edgecolor='#333')
            ax.set_title(title, color='#ccc', fontfamily='monospace', fontsize=10)
            ax.tick_params(colors='#aaa', labelrotation=30)
            for sp in ['top', 'right']:
                ax.spines[sp].set_visible(False)
            for sp in ['bottom', 'left']:
                ax.spines[sp].set_color('#333')
            for bar, val in zip(bars, data):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        f'{val:.2f}', ha='center', color='#ccc', fontsize=8, fontfamily='monospace')
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)
        canvas.draw()

    def _save_processes(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            with open(path, 'w') as f:
                json.dump(self.processes, f, indent=2)

    def _load_processes(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            with open(path) as f:
                self.processes = json.load(f)
            self._refresh_list()