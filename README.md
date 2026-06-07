# OS Algorithm Visualizer

A full-featured interactive desktop application built with **Python + CustomTkinter** that simulates and visualizes fundamental Operating System algorithms.

---

## Features

### ⚙ CPU Scheduling
| Algorithm | Type |
|---|---|
| First Come First Serve (FCFS) | Non-preemptive |
| Shortest Job First (SJF) | Non-preemptive & Preemptive (SRTF) |
| Priority Scheduling | Non-preemptive & Preemptive |
| Round Robin | Configurable quantum |
| Multilevel Queue (MLQ) | Priority-based queues |
| Multilevel Feedback Queue (MLFQ) | Adaptive quantum levels |

- Manual process entry + random generation
- Save/load process lists (JSON)
- Gantt chart visualization with color-coded blocks
- Metrics: Avg Waiting Time, Avg TAT, CPU Utilization, Throughput
- Side-by-side algorithm comparison charts

### 💾 Memory Management
| Algorithm | Description |
|---|---|
| First Fit | First hole large enough |
| Best Fit | Smallest sufficient hole |
| Worst Fit | Largest available hole |
| Next Fit | Resumes from last allocated |

- Visual memory map (allocated + free holes)
- External fragmentation calculation
- **Compaction** with before/after visualization
- **Paging** view with configurable page/frame size
- Dynamic allocation and deallocation

### 📄 Virtual Memory (Page Replacement)
| Algorithm | Description |
|---|---|
| FIFO | First-in, first-out eviction |
| LRU | Least Recently Used |
| Optimal (OPT) | Minimum future use |
| Clock | Second-chance approximation |
| LFU | Least Frequently Used |
| MFU | Most Frequently Used |

- Configurable frames and reference string
- Step-by-step execution controls (⏮ ⏭)
- Page fault counter + rate display
- Cumulative fault timeline graph
- **Belady's Anomaly** demonstration (FIFO faults vs frames)

### 💿 Disk Management
| Algorithm | Description |
|---|---|
| FCFS | First Come First Serve |
| SSTF | Shortest Seek Time First |
| SCAN | Elevator algorithm |
| C-SCAN | Circular SCAN |
| LOOK | SCAN without edge travel |
| C-LOOK | Circular LOOK |

- Animated disk arm movement
- Total seek time calculation
- Seek sequence display
- Algorithm comparison bar charts

---

## Setup

### Requirements
- Python 3.9+
- pip

### Installation

```bash
# Clone or extract the project folder
cd os_visualizer

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

### Dependencies
```
customtkinter>=5.2.0
matplotlib>=3.7.0
Pillow>=10.0.0
numpy>=1.24.0
```

---

## UI Guide

| Control | Action |
|---|---|
| Sidebar | Switch between OS modules |
| Dark/Light toggle | Appearance switch |
| ▶ Run / Simulate | Execute selected algorithm |
| ⚡ Random | Generate random inputs |
| ⏮ ⏭ | Step-by-step through simulation |
| 📊 Compare | Side-by-side algorithm comparison |
| 💾 Save / 📂 Load | Persist process lists (CPU module) |
| 🔧 Compact | Trigger memory compaction |

---

## Project Structure

```
os_visualizer/
├── main.py                     # App entry point + layout
├── requirements.txt
├── README.md
└── modules/
    ├── __init__.py
    ├── cpu_scheduling.py       # CPU scheduling algorithms + Gantt
    ├── memory_management.py    # Contiguous + paging memory
    ├── virtual_memory.py       # Page replacement algorithms
    └── disk_management.py      # Disk scheduling + animation
```

---

## Notes

- All animations run in background threads — UI stays responsive.
- Gantt chart colors are auto-assigned per process ID.
- Memory compaction moves all allocated blocks to low addresses, collects free space at high end.
- Belady's anomaly viewer shows FIFO fault count for frames 1–8 on the current reference string.

---

*Built for ECEN/COSC coursework — PUP BSCS*
