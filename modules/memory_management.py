"""
Memory Management Module
Implements: First Fit, Best Fit, Worst Fit, Next Fit, Compaction, Paging
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
from tkinter import messagebox


ALLOC_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
]
FREE_COLOR = "#2d2d44"
FRAG_COLOR = "#1a1a2e"


class MemoryBlock:
    def __init__(self, start, size, pid=None):
        self.start = start
        self.size = size
        self.pid = pid

    @property
    def end(self):
        return self.start + self.size

    @property
    def is_free(self):
        return self.pid is None


class MemoryManager:
    def __init__(self, total=1024):
        self.total = total
        self.blocks = [MemoryBlock(0, total)]
        self.last_fit_pos = 0
        self.color_map = {}
        self._color_idx = 0

    def reset(self, total=None):
        if total:
            self.total = total
        self.blocks = [MemoryBlock(0, self.total)]
        self.last_fit_pos = 0
        self.color_map = {}
        self._color_idx = 0

    def _get_color(self, pid):
        if pid not in self.color_map:
            self.color_map[pid] = ALLOC_COLORS[self._color_idx % len(ALLOC_COLORS)]
            self._color_idx += 1
        return self.color_map[pid]

    def get_free_holes(self):
        return [b for b in self.blocks if b.is_free]

    def get_external_fragmentation(self):
        holes = self.get_free_holes()
        if not holes:
            return 0
        total_free = sum(h.size for h in holes)
        largest = max(h.size for h in holes)
        return total_free - largest

    def allocate(self, pid, size, method="First Fit"):
        holes = [(i, b) for i, b in enumerate(self.blocks) if b.is_free and b.size >= size]
        if not holes:
            return False, "No suitable hole found"
        if method == "First Fit":
            idx, hole = holes[0]
        elif method == "Best Fit":
            idx, hole = min(holes, key=lambda x: x[1].size)
        elif method == "Worst Fit":
            idx, hole = max(holes, key=lambda x: x[1].size)
        elif method == "Next Fit":
            advanced = [(i, b) for i, b in holes if b.start >= self.last_fit_pos]
            idx, hole = advanced[0] if advanced else holes[0]
            self.last_fit_pos = hole.start
        else:
            idx, hole = holes[0]
        self._allocate_in_hole(idx, hole, pid, size)
        return True, f"Allocated {size}KB to {pid}"

    def _allocate_in_hole(self, idx, hole, pid, size):
        new_block = MemoryBlock(hole.start, size, pid)
        remainder = hole.size - size
        self.blocks.pop(idx)
        self.blocks.insert(idx, new_block)
        if remainder > 0:
            self.blocks.insert(idx + 1, MemoryBlock(hole.start + size, remainder))

    def deallocate(self, pid):
        for b in self.blocks:
            if b.pid == pid:
                b.pid = None
        self._merge_free()
        return True

    def _merge_free(self):
        merged = []
        for b in self.blocks:
            if merged and merged[-1].is_free and b.is_free:
                merged[-1] = MemoryBlock(merged[-1].start, merged[-1].size + b.size)
            else:
                merged.append(b)
        self.blocks = merged

    def compact(self):
        allocated = [b for b in self.blocks if not b.is_free]
        total_allocated = sum(b.size for b in allocated)
        new_blocks = []
        pos = 0
        for b in allocated:
            new_blocks.append(MemoryBlock(pos, b.size, b.pid))
            pos += b.size
        if pos < self.total:
            new_blocks.append(MemoryBlock(pos, self.total - pos))
        self.blocks = new_blocks
        return total_allocated

    def get_paging_info(self, page_size):
        pages = []
        frames = self.total // page_size
        for b in self.blocks:
            if not b.is_free:
                num_pages = (b.size + page_size - 1) // page_size
                for i in range(num_pages):
                    pages.append({'pid': b.pid, 'page': i, 'frame': len(pages) % frames})
        return pages, frames


class MemoryManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.mm = MemoryManager(1024)
        self.history = []
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Left panel
        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="💾 Memory Configuration", font=("Courier New", 14, "bold")).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w")

        # Memory size
        sz_frame = ctk.CTkFrame(left, fg_color="transparent")
        sz_frame.grid(row=1, column=0, columnspan=2, padx=12, pady=4, sticky="ew")
        ctk.CTkLabel(sz_frame, text="Total Memory (KB):", font=("Courier New", 11)).pack(side="left")
        self.mem_size_var = ctk.IntVar(value=1024)
        ctk.CTkSlider(sz_frame, from_=256, to=4096, variable=self.mem_size_var, width=120).pack(side="left", padx=8)
        self.mem_size_label = ctk.CTkLabel(sz_frame, text="1024", font=("Courier New", 11, "bold"), text_color="#4ECDC4")
        self.mem_size_label.pack(side="left")
        self.mem_size_var.trace_add("write", lambda *_: self.mem_size_label.configure(text=str(self.mem_size_var.get())))
        ctk.CTkButton(sz_frame, text="Reset", command=self._reset_memory, width=60,
                      fg_color="#FF6B6B", text_color="#fff", font=("Courier New", 11)).pack(side="left", padx=8)

        # Algorithm
        ctk.CTkLabel(left, text="Algorithm:", font=("Courier New", 11)).grid(row=2, column=0, padx=16, pady=4, sticky="w")
        self.method_var = ctk.StringVar(value="First Fit")
        ctk.CTkOptionMenu(left, values=["First Fit", "Best Fit", "Worst Fit", "Next Fit"],
                          variable=self.method_var, font=("Courier New", 11),
                          fg_color="#2d2d44", button_color="#4ECDC4",
                          button_hover_color="#3ab8ae").grid(row=2, column=1, padx=12, pady=4, sticky="ew")

        # Allocation inputs
        ctk.CTkLabel(left, text="── Allocate Process ──", font=("Courier New", 11), text_color="#4ECDC4").grid(
            row=3, column=0, columnspan=2, padx=12, pady=(12, 4))

        alloc_frame = ctk.CTkFrame(left, fg_color="transparent")
        alloc_frame.grid(row=4, column=0, columnspan=2, padx=12, pady=4, sticky="ew")
        ctk.CTkLabel(alloc_frame, text="PID:", font=("Courier New", 11)).pack(side="left")
        self.alloc_pid = ctk.CTkEntry(alloc_frame, width=60, placeholder_text="P1", font=("Courier New", 11))
        self.alloc_pid.pack(side="left", padx=6)
        ctk.CTkLabel(alloc_frame, text="Size(KB):", font=("Courier New", 11)).pack(side="left")
        self.alloc_size = ctk.CTkEntry(alloc_frame, width=70, placeholder_text="256", font=("Courier New", 11))
        self.alloc_size.pack(side="left", padx=6)

        ctk.CTkButton(left, text="✔ Allocate", command=self._allocate,
                      fg_color="#96CEB4", text_color="#000", font=("Courier New", 12, "bold")).grid(
            row=5, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        ctk.CTkButton(left, text="⚡ Random Alloc", command=self._random_alloc,
                      fg_color="#45B7D1", text_color="#000", font=("Courier New", 11)).grid(
            row=6, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        # Deallocation
        ctk.CTkLabel(left, text="── Deallocate Process ──", font=("Courier New", 11), text_color="#FF6B6B").grid(
            row=7, column=0, columnspan=2, padx=12, pady=(12, 4))

        dealloc_frame = ctk.CTkFrame(left, fg_color="transparent")
        dealloc_frame.grid(row=8, column=0, columnspan=2, padx=12, pady=4, sticky="ew")
        ctk.CTkLabel(dealloc_frame, text="PID:", font=("Courier New", 11)).pack(side="left")
        self.dealloc_pid = ctk.CTkEntry(dealloc_frame, width=80, placeholder_text="P1", font=("Courier New", 11))
        self.dealloc_pid.pack(side="left", padx=6)
        ctk.CTkButton(dealloc_frame, text="✘ Free", command=self._deallocate,
                      fg_color="#FF6B6B", text_color="#fff", font=("Courier New", 11)).pack(side="left", padx=6)

        # Compaction
        ctk.CTkLabel(left, text="── Compaction ──", font=("Courier New", 11), text_color="#FFEAA7").grid(
            row=9, column=0, columnspan=2, padx=12, pady=(12, 4))
        ctk.CTkButton(left, text="🔧 Compact Memory", command=self._compact,
                      fg_color="#FFEAA7", text_color="#000", font=("Courier New", 12, "bold")).grid(
            row=10, column=0, columnspan=2, padx=12, pady=4, sticky="ew")

        # Stats
        self.stats_box = ctk.CTkTextbox(left, height=120, font=("Courier New", 10),
                                        fg_color="#1a1a2e", text_color="#4ECDC4")
        self.stats_box.grid(row=11, column=0, columnspan=2, padx=12, pady=(8, 8), sticky="ew")

        # Right panel
        right = ctk.CTkFrame(self, corner_radius=12)
        right.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        tab = ctk.CTkTabview(right, fg_color="#1a1a2e", segmented_button_fg_color="#2d2d44",
                             segmented_button_selected_color="#4ECDC4",
                             segmented_button_selected_hover_color="#3ab8ae",
                             text_color="#ccc")
        tab.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        tab.add("Memory Map")
        tab.add("Paging")
        tab.set("Memory Map")

        # Memory map tab
        self.mem_fig, self.mem_ax = plt.subplots(figsize=(7, 5))
        self.mem_fig.patch.set_facecolor("#1a1a2e")
        self.mem_canvas = FigureCanvasTkAgg(self.mem_fig, master=tab.tab("Memory Map"))
        self.mem_canvas.get_tk_widget().pack(fill="both", expand=True)

        # Paging tab
        paging_ctrl = ctk.CTkFrame(tab.tab("Paging"), fg_color="transparent")
        paging_ctrl.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(paging_ctrl, text="Page Size (KB):", font=("Courier New", 11)).pack(side="left")
        self.page_size_var = ctk.IntVar(value=64)
        ctk.CTkSlider(paging_ctrl, from_=16, to=256, variable=self.page_size_var, width=120).pack(side="left", padx=8)
        self.page_size_label = ctk.CTkLabel(paging_ctrl, text="64", font=("Courier New", 11, "bold"), text_color="#4ECDC4")
        self.page_size_label.pack(side="left")
        self.page_size_var.trace_add("write", lambda *_: [
            self.page_size_label.configure(text=str(self.page_size_var.get())), self._draw_paging()])
        ctk.CTkButton(paging_ctrl, text="Refresh", command=self._draw_paging,
                      fg_color="#45B7D1", text_color="#000", font=("Courier New", 11)).pack(side="left", padx=8)

        self.page_fig, self.page_ax = plt.subplots(figsize=(7, 4))
        self.page_fig.patch.set_facecolor("#1a1a2e")
        self.page_canvas = FigureCanvasTkAgg(self.page_fig, master=tab.tab("Paging"))
        self.page_canvas.get_tk_widget().pack(fill="both", expand=True)

        self._draw_memory_map()

    def _reset_memory(self):
        self.mm.reset(self.mem_size_var.get())
        self._draw_memory_map()
        self._update_stats()

    def _allocate(self):
        pid = self.alloc_pid.get().strip()
        try:
            size = int(self.alloc_size.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid size")
            return
        if not pid:
            messagebox.showerror("Error", "Enter PID")
            return
        ok, msg = self.mm.allocate(pid, size, self.method_var.get())
        if not ok:
            messagebox.showwarning("Allocation Failed", msg)
        self._draw_memory_map()
        self._update_stats()
        self.alloc_pid.delete(0, "end")
        self.alloc_size.delete(0, "end")

    def _random_alloc(self):
        for i in range(random.randint(3, 6)):
            pid = f"P{i+1}"
            size = random.randint(64, 256)
            self.mm.allocate(pid, size, self.method_var.get())
        self._draw_memory_map()
        self._update_stats()

    def _deallocate(self):
        pid = self.dealloc_pid.get().strip()
        if not pid:
            messagebox.showerror("Error", "Enter PID")
            return
        self.mm.deallocate(pid)
        self._draw_memory_map()
        self._update_stats()
        self.dealloc_pid.delete(0, "end")

    def _compact(self):
        before_blocks = [MemoryBlock(b.start, b.size, b.pid) for b in self.mm.blocks]
        self.mm.compact()
        self._draw_memory_map(highlight_compact=True)
        self._update_stats()
        messagebox.showinfo("Compaction Done", f"Memory compacted!\nExternal fragmentation: {self.mm.get_external_fragmentation()} KB")

    def _draw_memory_map(self, highlight_compact=False):
        self.mem_ax.clear()
        self.mem_ax.set_facecolor("#12122a")
        total = self.mm.total
        y = 0
        height = 0.8
        for block in self.mm.blocks:
            frac = block.size / total
            if block.is_free:
                color = FREE_COLOR
                label = f"FREE\n{block.size}KB"
                tc = "#666"
            else:
                color = self.mm.color_map.get(block.pid, "#4ECDC4")
                label = f"{block.pid}\n{block.size}KB"
                tc = "#000"
            rect = plt.Rectangle((0, y), 1, frac, color=color, edgecolor="#333", linewidth=1)
            self.mem_ax.add_patch(rect)
            if frac > 0.03:
                self.mem_ax.text(0.5, y + frac/2, label, ha='center', va='center',
                                 color=tc, fontsize=9, fontfamily='monospace', fontweight='bold')
            self.mem_ax.text(1.02, y, f"{block.start}K", ha='left', va='center',
                             color='#888', fontsize=7, fontfamily='monospace')
            y += frac
        self.mem_ax.text(1.02, y, f"{total}K", ha='left', va='center',
                         color='#888', fontsize=7, fontfamily='monospace')
        self.mem_ax.set_xlim(0, 1.2)
        self.mem_ax.set_ylim(0, 1)
        self.mem_ax.set_xticks([])
        self.mem_ax.set_yticks([])
        self.mem_ax.set_title(f"Memory Map — {self.method_var.get()} | Total: {total}KB",
                              color='#ccc', fontfamily='monospace', fontsize=10)
        for sp in self.mem_ax.spines.values():
            sp.set_visible(False)
        self.mem_fig.tight_layout()
        self.mem_canvas.draw()

    def _draw_paging(self):
        page_size = self.page_size_var.get()
        pages, num_frames = self.mm.get_paging_info(page_size)
        self.page_ax.clear()
        self.page_ax.set_facecolor("#12122a")
        if not pages:
            self.page_ax.text(0.5, 0.5, "No allocated processes", ha='center', va='center',
                              color='#555', fontsize=12, fontfamily='monospace')
            self.page_ax.axis('off')
            self.page_fig.tight_layout()
            self.page_canvas.draw()
            return
        cols = 8
        rows = (len(pages) + cols - 1) // cols
        for i, pg in enumerate(pages):
            row, col = divmod(i, cols)
            color = self.mm.color_map.get(pg['pid'], "#4ECDC4")
            rect = plt.Rectangle((col, rows - row - 1), 0.9, 0.9, color=color, edgecolor='#000')
            self.page_ax.add_patch(rect)
            self.page_ax.text(col + 0.45, rows - row - 0.55,
                              f"{pg['pid']}\nP{pg['page']}→F{pg['frame']}",
                              ha='center', va='center', fontsize=6, fontfamily='monospace', color='#000')
        self.page_ax.set_xlim(-0.1, cols)
        self.page_ax.set_ylim(-0.1, rows + 0.1)
        self.page_ax.set_title(f"Page Table (Page={page_size}KB, Frames={num_frames})",
                               color='#ccc', fontfamily='monospace', fontsize=10)
        self.page_ax.axis('off')
        self.page_fig.tight_layout()
        self.page_canvas.draw()

    def _update_stats(self):
        allocated = sum(b.size for b in self.mm.blocks if not b.is_free)
        free = self.mm.total - allocated
        frag = self.mm.get_external_fragmentation()
        holes = self.mm.get_free_holes()
        util = (allocated / self.mm.total * 100) if self.mm.total > 0 else 0
        self.stats_box.configure(state="normal")
        self.stats_box.delete("1.0", "end")
        self.stats_box.insert("end",
            f"Total Memory   : {self.mm.total} KB\n"
            f"Allocated      : {allocated} KB ({util:.1f}%)\n"
            f"Free           : {free} KB\n"
            f"Holes          : {len(holes)}\n"
            f"Ext. Frag.     : {frag} KB\n"
            f"Method         : {self.method_var.get()}\n"
        )
        self.stats_box.configure(state="disabled")
