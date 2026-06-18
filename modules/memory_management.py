"""
Memory Management Module
Implements: First Fit, Best Fit, Worst Fit, Next Fit, Compaction, Paging
"""
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import colorsys
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
    def __init__(self, total=1024, os_size=128):
        self.total = total
        self.os_size = os_size
        self.blocks = []
        if os_size > 0:
            self.blocks.append(MemoryBlock(0, os_size, "OS"))
            if total > os_size:
                self.blocks.append(MemoryBlock(os_size, total - os_size))
        else:
            self.blocks.append(MemoryBlock(0, total))
        self.last_fit_pos = os_size
        self.color_map = {}
        self._color_idx = 0
        self.auto_compact = False

    def reset(self, total=None, os_size=None):
        if total is not None:
            self.total = total
        if os_size is not None:
            self.os_size = os_size
        self.blocks = []
        if self.os_size > 0:
            self.blocks.append(MemoryBlock(0, self.os_size, "OS"))
            if self.total > self.os_size:
                self.blocks.append(MemoryBlock(self.os_size, self.total - self.os_size))
        else:
            self.blocks.append(MemoryBlock(0, self.total))
        self.last_fit_pos = self.os_size
        self.color_map = {}
        self._color_idx = 0

    def _get_color(self, pid):
        if pid == "OS":
            return "#164e63"
        if pid not in self.color_map:
            self._color_idx += 1
            # Dynamic HSL generation from user's web version style
            h = (self._color_idx * 137 % 360) / 360.0
            r, g, b = colorsys.hls_to_rgb(h, 0.45, 0.65)
            self.color_map[pid] = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
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
        if self.auto_compact:
            self.compact()
            
        holes = [(i, b) for i, b in enumerate(self.blocks) if b.is_free and b.size >= size]
        if not holes:
            return False, "Not enough contiguous memory. Try compacting!"
            
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
        if self.auto_compact:
            self.compact()
        return True

    def clear(self):
        for b in self.blocks:
            if b.pid != "OS" and not b.is_free:
                b.pid = None
        self._merge_free()
        if self.auto_compact:
            self.compact()

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
            if not b.is_free and b.pid != "OS":
                num_pages = (b.size + page_size - 1) // page_size
                for i in range(num_pages):
                    pages.append({'pid': b.pid, 'page': i, 'frame': len(pages) % frames})
        return pages, frames

class MemoryManagementFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.mm = MemoryManager(1024, 128)
        self.history = []
        self.pid_counter = 1
        self.rect_map = []
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

        # Memory size & OS size setup
        sz_frame = ctk.CTkFrame(left, fg_color="transparent")
        sz_frame.grid(row=1, column=0, columnspan=2, padx=12, pady=4, sticky="ew")
        
        ctk.CTkLabel(sz_frame, text="Total(KB):", font=("Courier New", 11)).grid(row=0, column=0, sticky="w")
        self.mem_size_var = ctk.IntVar(value=1024)
        ctk.CTkSlider(sz_frame, from_=256, to=4096, variable=self.mem_size_var, width=100).grid(row=0, column=1, padx=4)
        self.mem_size_label = ctk.CTkLabel(sz_frame, text="1024", font=("Courier New", 11, "bold"), text_color="#4ECDC4")
        self.mem_size_label.grid(row=0, column=2, sticky="w")
        self.mem_size_var.trace_add("write", lambda *_: self.mem_size_label.configure(text=str(self.mem_size_var.get())))
        
        ctk.CTkLabel(sz_frame, text="OS(KB):", font=("Courier New", 11)).grid(row=1, column=0, sticky="w", pady=4)
        self.os_size_var = ctk.IntVar(value=128)
        ctk.CTkSlider(sz_frame, from_=0, to=1024, variable=self.os_size_var, width=100).grid(row=1, column=1, padx=4, pady=4)
        self.os_size_label = ctk.CTkLabel(sz_frame, text="128", font=("Courier New", 11, "bold"), text_color="#4ECDC4")
        self.os_size_label.grid(row=1, column=2, sticky="w", pady=4)
        self.os_size_var.trace_add("write", lambda *_: self.os_size_label.configure(text=str(self.os_size_var.get())))

        btn_frame = ctk.CTkFrame(sz_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=3, pady=4, sticky="w")
        ctk.CTkButton(btn_frame, text="Init/Reset", command=self._reset_memory, width=70,
                      fg_color="#FF6B6B", text_color="#fff", font=("Courier New", 11)).pack(side="left", padx=(0, 4))
        ctk.CTkButton(btn_frame, text="Clear", command=self._clear_memory, width=60,
                      fg_color="#F7DC6F", text_color="#000", font=("Courier New", 11)).pack(side="left", padx=4)

        # Algorithm and Auto Compact
        algo_frame = ctk.CTkFrame(left, fg_color="transparent")
        algo_frame.grid(row=2, column=0, columnspan=2, padx=12, pady=4, sticky="ew")
        ctk.CTkLabel(algo_frame, text="Algorithm:", font=("Courier New", 11)).pack(side="left")
        self.method_var = ctk.StringVar(value="First Fit")
        ctk.CTkOptionMenu(algo_frame, values=["First Fit", "Best Fit", "Worst Fit", "Next Fit"],
                          variable=self.method_var, font=("Courier New", 11),
                          fg_color="#2d2d44", button_color="#4ECDC4", width=100,
                          button_hover_color="#3ab8ae").pack(side="left", padx=8)
        self.auto_compact_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(algo_frame, text="Auto Compact", variable=self.auto_compact_var,
                        font=("Courier New", 11), fg_color="#4ECDC4", hover_color="#3ab8ae",
                        command=self._on_auto_compact_change).pack(side="left", padx=4)

        # Allocation inputs
        ctk.CTkLabel(left, text="── Allocate Process ──", font=("Courier New", 11), text_color="#4ECDC4").grid(
            row=3, column=0, columnspan=2, padx=12, pady=(12, 4))

        alloc_frame = ctk.CTkFrame(left, fg_color="transparent")
        alloc_frame.grid(row=4, column=0, columnspan=2, padx=12, pady=4, sticky="ew")
        ctk.CTkLabel(alloc_frame, text="Size(KB):", font=("Courier New", 11)).pack(side="left")
        self.alloc_size = ctk.CTkEntry(alloc_frame, width=140, placeholder_text="Enter size (e.g., 256)", font=("Courier New", 11))
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
        ctk.CTkLabel(dealloc_frame, text="💡 Click a process block in the\nMemory Map graph to kill it.", 
                     font=("Courier New", 11, "italic"), text_color="#aaa", justify="center").pack(side="left", fill="x", expand=True, padx=6)

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
        self.mem_canvas.mpl_connect('button_press_event', self._on_canvas_click)

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

    def _on_canvas_click(self, event):
        if event.inaxes != self.mem_ax:
            return
            
        click_y = event.ydata
        if click_y is None:
            return
            
        for y_start, y_end, pid in self.rect_map:
            if y_start <= click_y <= y_end:
                if messagebox.askyesno("Kill Process", f"Do you want to deallocate process {pid}?"):
                    self.mm.deallocate(pid)
                    self._draw_memory_map()
                    self._update_stats()
                break

    def _reset_memory(self):
        tot = self.mem_size_var.get()
        os_sz = self.os_size_var.get()
        if os_sz >= tot:
            messagebox.showerror("Error", "OS size must be less than Total Memory")
            return
        self.pid_counter = 1
        self.mm.reset(tot, os_sz)
        self._draw_memory_map()
        self._update_stats()

    def _clear_memory(self):
        self.pid_counter = 1
        self.mm.clear()
        self._draw_memory_map()
        self._update_stats()

    def _on_auto_compact_change(self):
        self.mm.auto_compact = self.auto_compact_var.get()
        if self.mm.auto_compact:
            self.mm.compact()
            self._draw_memory_map()
            self._update_stats()

    def _allocate(self):
        val = self.alloc_size.get().strip()
        if not val:
            messagebox.showerror("Error", "Please enter a size")
            return
            
        try:
            size = int(val)
            if size <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Size must be a positive integer")
            return
            
        pid = f"P{self.pid_counter}"
        ok, msg = self.mm.allocate(pid, size, self.method_var.get())
        if not ok:
            messagebox.showwarning("Allocation Failed", msg)
        else:
            self.pid_counter += 1
            
        self._draw_memory_map()
        self._update_stats()
        self.alloc_size.delete(0, "end")

    def _random_alloc(self):
        for i in range(random.randint(3, 6)):
            pid = f"P{self.pid_counter}"
            size = random.randint(64, 256)
            ok, _ = self.mm.allocate(pid, size, self.method_var.get())
            if ok:
                self.pid_counter += 1
        self._draw_memory_map()
        self._update_stats()

    def _compact(self):
        self.mm.compact()
        self._draw_memory_map(highlight_compact=True)
        self._update_stats()
        messagebox.showinfo("Compaction Done", f"Memory compacted!\nExternal fragmentation: {self.mm.get_external_fragmentation()} KB")

    def _draw_memory_map(self, highlight_compact=False):
        self.mem_ax.clear()
        self.mem_ax.set_facecolor("#12122a")
        total = self.mm.total
        y = 0
        self.rect_map = []
        for block in self.mm.blocks:
            frac = block.size / total
            if block.is_free:
                color = FREE_COLOR
                label = f"FREE\n{block.size}KB"
                tc = "#666"
            elif block.pid == "OS":
                color = self.mm._get_color(block.pid)
                label = f"OS\n{block.size}KB"
                tc = "#22d3ee"
            else:
                color = self.mm._get_color(block.pid)
                label = f"{block.pid}\n{block.size}KB"
                tc = "#fff"
                self.rect_map.append((y, y + frac, block.pid))
                
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
        self._draw_paging()

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
            color = self.mm._get_color(pg['pid'])
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
            f"OS Size        : {self.mm.os_size} KB\n"
            f"Allocated      : {allocated} KB ({util:.1f}%)\n"
            f"Free           : {free} KB\n"
            f"Holes          : {len(holes)}\n"
            f"Ext. Frag.     : {frag} KB\n"
            f"Method         : {self.method_var.get()}\n"
            f"Auto Compact   : {'Yes' if self.mm.auto_compact else 'No'}\n"
        )
        self.stats_box.configure(state="disabled")
