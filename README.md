TDA_Politico_COL — Political Sismograph (Colombia)

A reproducible data collection pipeline to capture and audit political
conversation on X/Twitter related to Colombia, using public mirrors
(Nitter / XCancel) and real temporal windows.

Focus: building a high-quality, auditable dataset with strict time
control, deduplication, and telemetry, suitable for downstream analysis
(topic modeling, networks, TDA, time series, etc.).


1) Motivation

Collecting tweets through search interfaces usually introduces several
well-known issues:

- Recency bias: results are returned ordered by most recent first.
- Geographic noise: terms such as Congress, Senate, Constitutional Court
  appear in multiple countries.
- Mirror instability: different mirrors fail or change HTML structure.
- Lack of auditability: low yield blocks are hard to diagnose.
- Duplication: the same tweet may appear across mirrors or pages.

This project addresses these issues by:

- Sampling through real sub-windows of time.
- Filtering tweets strictly by timestamp.
- Deduplicating by status_id.
- Logging every request and block for audit and diagnostics.


2) Main Features

- Real temporal sub-windows using since_time / until_time (epoch).
- Correct timezone handling: America/Bogota <-> UTC.
- Robust deduplication across mirrors and pages.
- Extraction of engagement metrics (K/M) with raw audit fields.
- Hashtag and mention extraction.
- Separate media channel (press outlets).
- Incremental CSV writing to avoid RAM overload.
- Per-window and per-request audit logs.
- Final run summary with throughput and failure statistics.


3) Repository Structure

TDA_Politico_COL
├── data
│   ├── raw
│   ├── processed
│   └── sample
├── logs
│   └── .gitkeep
├── src
│   ├── config
│   │   ├── settings.py
│   │   └── __init__.py
│   ├── queries
│   │   ├── mirrors.py
│   │   ├── query_core.py
│   │   └── __init__.py
│   ├── scraping
│   │   ├── browser.py
│   │   ├── extractor.py
│   │   ├── orchestrator.py
│   │   └── __init__.py
│   ├── utils
│   │   ├── dates.py
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   ├── text.py
│   │   └── __init__.py
│   ├── main.py
│   └── __init__.py
├── .gitignore
└── requirements.txt


Design principle:
each component can be modified independently (queries, windows,
priors, mirrors, logging) without editing a monolithic script.


4) Installation (Windows + PowerShell)

4.1 Create and activate virtual environment

python -m venv .venv
.\.venv\Scripts\Activate.ps1

4.2 Install dependencies

pip install -r requirements.txt


5) Running the pipeline

From the project root:

python -m src.main

Note:
The scraper relies on Selenium and undetected_chromedriver.
Google Chrome must be installed.


6) Outputs

Dataset (CSV)
- Written incrementally during execution.
- Typical fields include:
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

Logs and audit artifacts

window_log.csv
- One row per sub-window, channel, and mirror.
- Contains counts of seen items, valid dates, discarded items, and stop
  reasons.

request_log.csv
- One row per request attempt (mirror + sub-window).
- Includes latency, pages used, and short error messages if applicable.

run_summary.json
- Final execution summary:
  - total tweets collected
  - total requests
  - success and failure rates
  - throughput (tweets per minute)
  - performance by channel and mirror


7) Debugging and interpretation tips

High outside_window counts:
- Likely timezone conversion issues or HTML date parsing changes.

High dates_fail:
- Date selector or attribute may have changed in the mirror HTML.

Low obtained_n with high items_seen:
- Low real tweet density in that window,
- Overly broad queries,
- Insufficient pagination or mirror availability.


8) Customization points

The project is designed to be modified safely:

- Change sub-window size:
  SUBWINDOW_MINUTES in config/settings.py

- Change mirrors:
  MIRRORS in config/settings.py

- Change queries or channels:
  query_core.py in src/queries

- Change study date range:
  orchestrator logic in src/scraping

- Change daily sampling budgets:
  TOTAL_PER_DAY_PER_CHANNEL_* in settings


9) Planned extensions

- Colombia relevance score using:
  - local entity co-occurrence
  - language detection
  - profile location heuristics
- Semantic filtering using embeddings to reduce cross-country noise.
- Export to parquet with schema.
- Exploratory notebooks for downstream analysis.
- Unit tests for date parsing and metric normalization.


10) Disclaimer

This project is intended for research and portfolio purposes.
Users are responsible for complying with platform policies and
ethical considerations when collecting, storing, or publishing data.
