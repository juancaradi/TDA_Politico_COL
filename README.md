# 🇨🇴 TDA Political Seismograph (Colombia)

A high-precision, fault-tolerant data acquisition pipeline for capturing and auditing political discourse on **X (formerly Twitter)** using public mirrors (Nitter / XCancel), designed for **scientific reproducibility** and downstream analysis in **Topological Data Analysis (TDA)**, NLP, and Network Theory.

> **Status:** Active Development  
> **Python:** 3.10+  
> **Primary Focus:** Temporal fidelity, auditability, and robustness under mirror instability.

---

## 📖 Overview

**TDA_Politico_COL** is not a conventional web scraper.  
It is a **temporal sampling instrument** designed to reconstruct political conversation streams with **strict control over time, provenance, and failure modes**.

Typical scraping approaches suffer from:
- Recency bias
- Temporal gaps
- Mirror-specific duplication
- Silent failures
- Poor auditability

This project addresses those issues by treating data collection as a **controlled experiment**, not a crawl.

The system behaves as a **Political Seismograph**:  
it scans the political discourse through real temporal sub-windows, records what was observed, what failed, and why.

---

## 🎯 Design Goals

- **Temporal accuracy** over volume
- **Auditability** over opacity
- **Reproducibility** over convenience
- **Separation of concerns** over monolithic scripts

---

## 🚀 Key Features

### 1. Real Temporal Sampling
- Epoch-based queries using `since_time` / `until_time`
- Fixed **10-minute sub-windows**
- Strict filtering by tweet timestamp (UTC ↔ America/Bogota)

### 2. Stratified Traffic Allocation
- Daily quotas split by hour using a diurnal traffic profile
- Sub-hour weighting to mitigate “most recent first” bias
- Weekend vs weekday differentiation

### 3. Mirror Resilience
- Automatic rotation across public mirrors
- Graceful fallback on empty or failing mirrors
- Robust deduplication across mirrors and pages via `status_id`

### 4. Full Telemetry & Audit Logs
Every execution leaves a forensic trail:
- What was requested
- What was observed
- What failed
- How long it took

### 5. Incremental & Safe Storage
- Incremental CSV writes (flush strategy)
- No in-memory accumulation of large datasets
- Safe termination handling (Ctrl + C)

---

## 🧠 Semantic Channels

Queries are organized into four semantic dimensions (`src/queries/query_core.py`):

| Channel | Description | Research Use |
|------|------------|-------------|
| **TIPO_A_ACTORES** | Political actors and parties | Node tracking |
| **TIPO_B_FRAMES** | Institutions, issues, economy, security | Context modeling |
| **TIPO_B2_MEDIOS** | Press and media outlets | Agenda-setting |
| **TIPO_C_MIXTA** | Actors ∩ Issues | Narrative intersections |
| **TIPO_D_INTENSIDAD** | Polarizing vocabulary | Discourse intensity |

---

## 🗂 Repository Structure

```text
TDA_Politico_COL
├── data
│   ├── raw                 # (Output) Incremental CSVs land here
│   └── sample              # Small datasets for testing/validation
├── logs                    # (Output) Session statistics, telemetry & error traces
├── src
│   ├── config
│   │   └── settings.py     # Quotas, paths, limits & global constants
│   ├── queries
│   │   ├── mirrors.py      # Nitter instance list & rotation logic
│   │   └── query_core.py   # Semantic definitions (Actors, Frames, Intensity)
│   ├── scraping
│   │   ├── browser.py      # Undetected Chrome infrastructure
│   │   ├── extractor.py    # Sub-window sampling & retry logic (The Soldier)
│   │   └── orchestrator.py # Time & budget management (The General)
│   ├── utils
│   │   ├── dates.py        # Timezone handling & epoch conversion
│   │   ├── logging.py      # Telemetry system & CSV flushing
│   │   ├── metrics.py      # Parsing engagement numbers (K/M -> int)
│   │   └── text.py         # NLP normalization & Mojibake fixes
│   └── main.py             # Application entry point
├── .gitignore
├── CHANGELOG.md            # History of changes & versions
├── README.md
└── requirements.txt
```


### 6. Design principle:
Each module can evolve independently (queries, mirrors, windows, logging) without modifying a monolithic script.

### Installation (Windows / PowerShell)

### Environment Setup

```powershell
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Requirements

- Google Chrome (stable version)

- Python ≥ 3.10


## ▶️ 7.  Running the Pipeline

From the project root:

```powershell
python -m src.main
```


### During execution, the console will display:

- Active channel and sub-window

- Mirror currently in use

- Items seen vs accepted

- Heartbeat signals confirming liveness

## 📤 8. Outputs

### a. Raw Dataset

- Location: data/raw/

- Incrementally written CSV

- No preprocessing beyond extraction

- Suitable for downstream ETL, NLP, or TDA pipelines

- Typical fields:

- timestamp_local

- timestamp_utc

- query_type

- texto_raw

- texto_norm

- hashtags

- menciones

- replies, retweets, quotes, likes

- status_id

- mirror_used

- query_hash


## b. Audit & Telemetry Logs (logs/)

### window_log.csv

- One row per sub-window × channel × mirror

- Counts of valid, discarded, and failed items

- Stop reasons and diagnostics

### request_log.csv

- One row per request attempt

- Latency, pages traversed, error summaries

### run_summary.json

- Final execution summary

- Throughput (tweets/min)

- Success & failure rates

- Performance by channel and mirror


## 🧪 9. Debugging & Interpretation

### High outside_window
→ Timezone mismatch or HTML date parsing change

### High dates_fail
→ Mirror HTML structure changed

### Low obtained_n with high items_seen
→ Low tweet density, overly broad query, or mirror degradation

## 🛑 10. Safe Termination

- The pipeline handles Ctrl + C gracefully:

- Flushes buffers

- Writes logs

- Generates final summaries

- Exits without data corruption

## 🧩 11. Customization Points

Sub-window size: SUBWINDOW_MINUTES

Daily quotas: TOTAL_PER_DAY_PER_CHANNEL_*

Mirrors: src/queries/mirrors.py

Queries & semantics: src/queries/query_core.py

Study date range: src/main.py


## 🔭 12. Planned Extensions

Colombia relevance scoring

Language detection and filtering

Semantic embeddings for noise reduction

Parquet export with schema

Exploratory notebooks

Unit tests for date & metric parsing


##### ⚠️ Ethics & Disclaimer

This project is intended for academic research and portfolio purposes.

Uses only publicly available mirror data

No private data is accessed

Users are responsible for complying with platform policies and local regulations

```python
# Author: Juan Camilo Ramírez Díaz
# Context: Mathematics, Data Analysis & Topological Data Analysis Research
```