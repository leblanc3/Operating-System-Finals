"""
OS Algorithms Visualizer
Main application — CustomTkinter desktop app
Run: python main.py
"""
import customtkinter as ctk
import sys
import os

# Ensure modules can be found
sys.path.insert(0, os.path.dirname(__file__))

from modules.cpu_scheduling import CPUSchedulingFrame
from modules.memory_management import MemoryManagementFrame
from modules.virtual_memory import VirtualMemoryFrame
from modules.disk_management import DiskManagementFrame


# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

ACCENT       = "#4ECDC4"
ACCENT2      = "#FF6B6B"
SIDEBAR_BG   = "#0d0d1a"
MAIN_BG      = "#12122a"
CARD_BG      = "#1a1a2e"
NAV_HOVER    = "#2d2d44"
NAV_ACTIVE   = "#4ECDC4"
TEXT_PRIMARY = "#e8e8f0"
TEXT_DIM     = "#6b6b8a"


MODULES = [
    ("⚙ CPU Scheduling",   CPUSchedulingFrame),
    ("💾 Memory Mgmt",     MemoryManagementFrame),
    ("📄 Virtual Memory",  VirtualMemoryFrame),
    ("💿 Disk Mgmt",       DiskManagementFrame),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_select):
        super().__init__(parent, width=200, corner_radius=0, fg_color=SIDEBAR_BG)
        self.on_select = on_select
        self.buttons = []
        self._build()

    def _build(self):
        self.grid_rowconfigure(99, weight=1)

        # Logo / title area
        logo_frame = ctk.CTkFrame(self, fg_color="#090918", corner_radius=0, height=72)
        logo_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        logo_frame.grid_propagate(False)
        logo_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(logo_frame, text="OS VIZ",
                     font=("Courier New", 22, "bold"), text_color=ACCENT).grid(
            row=0, column=0, pady=(14, 0))
        ctk.CTkLabel(logo_frame, text="Algorithm Visualizer",
                     font=("Courier New", 9), text_color=TEXT_DIM).grid(row=1, column=0, pady=(0, 10))

        # Nav items
        ctk.CTkLabel(self, text="MODULES", font=("Courier New", 9, "bold"),
                     text_color=TEXT_DIM).grid(row=1, column=0, padx=16, pady=(20, 6), sticky="w")

        for i, (label, _) in enumerate(MODULES):
            btn = ctk.CTkButton(
                self, text=label, anchor="w",
                font=("Courier New", 12),
                fg_color="transparent",
                hover_color=NAV_HOVER,
                text_color=TEXT_PRIMARY,
                corner_radius=8,
                height=40,
                command=lambda idx=i: self.select(idx)
            )
            btn.grid(row=i+2, column=0, padx=10, pady=2, sticky="ew")
            self.buttons.append(btn)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color="#2d2d44").grid(
            row=99, column=0, sticky="sew", padx=16, pady=8)

        # Theme toggle
        ctk.CTkLabel(self, text="Appearance", font=("Courier New", 9, "bold"),
                     text_color=TEXT_DIM).grid(row=100, column=0, padx=16, pady=(4, 4), sticky="w")
        self.theme_switch = ctk.CTkSwitch(
            self, text="Dark Mode", font=("Courier New", 11),
            command=self._toggle_theme, text_color=TEXT_PRIMARY,
            progress_color=ACCENT, button_color=ACCENT2
        )
        self.theme_switch.grid(row=101, column=0, padx=16, pady=(0, 12), sticky="w")
        self.theme_switch.select()

    def select(self, idx):
        for i, btn in enumerate(self.buttons):
            if i == idx:
                btn.configure(fg_color=ACCENT, text_color="#000", font=("Courier New", 12, "bold"))
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_PRIMARY, font=("Courier New", 12))
        self.on_select(idx)

    def _toggle_theme(self):
        mode = "dark" if self.theme_switch.get() else "light"
        ctk.set_appearance_mode(mode)


class HeaderBar(ctk.CTkFrame):
    def __init__(self, parent, title=""):
        super().__init__(parent, height=56, corner_radius=0, fg_color=CARD_BG)
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(
            self, text=title, font=("Courier New", 16, "bold"), text_color=TEXT_PRIMARY)
        self.title_label.grid(row=0, column=0, padx=24, pady=12, sticky="w")

        self.subtitle = ctk.CTkLabel(
            self, text="", font=("Courier New", 10), text_color=TEXT_DIM)
        self.subtitle.grid(row=0, column=1, padx=8, pady=12, sticky="w")

        version_label = ctk.CTkLabel(
            self, text="v1.0 — PUP BSCS", font=("Courier New", 9), text_color=TEXT_DIM)
        version_label.grid(row=0, column=2, padx=24, pady=12, sticky="e")

    def set_title(self, title, subtitle=""):
        self.title_label.configure(text=title)
        self.subtitle.configure(text=subtitle)


SUBTITLES = [
    "FCFS · SJF · Priority · Round Robin · MLQ · MLFQ",
    "First Fit · Best Fit · Worst Fit · Next Fit · Compaction · Paging",
    "FIFO · LRU · Optimal · Clock · LFU · MFU · Belady's Anomaly",
    "FCFS · SSTF · SCAN · C-SCAN · LOOK · C-LOOK",
]


class OSVisualizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OS Algorithm Visualizer")
        self.geometry("1280x780")
        self.minsize(1100, 680)
        self.configure(fg_color=MAIN_BG)
        self._frames = {}
        self._build_layout()

    def _build_layout(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar = Sidebar(self, on_select=self._show_module)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")

        # Header
        self.header = HeaderBar(self, title=MODULES[0][0])
        self.header.grid(row=0, column=1, sticky="ew")

        # Content area
        self.content = ctk.CTkFrame(self, fg_color=MAIN_BG, corner_radius=0)
        self.content.grid(row=1, column=1, sticky="nsew", padx=0)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Instantiate all module frames
        for i, (label, FrameClass) in enumerate(MODULES):
            frame = FrameClass(self.content)
            frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
            self._frames[i] = frame
            frame.grid_remove()

        self.sidebar.select(0)

    def _show_module(self, idx):
        for i, frame in self._frames.items():
            frame.grid_remove()
        self._frames[idx].grid()
        label = MODULES[idx][0]
        subtitle = SUBTITLES[idx]
        self.header.set_title(label, subtitle)


def main():
    app = OSVisualizerApp()
    app.mainloop()


if __name__ == "__main__":
    main()