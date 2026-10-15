# QuantumSafe VPN Android Application — Master Academic Project Report

**Degree:** Bachelor of Technology in Computer Science and Engineering (Cyber Security)  
**Institution:** Amrita School of Computing, Amrita Vishwa Vidyapeetham, Chennai Campus  
**Department:** Department of Computer Science and Engineering  
**Academic Year:** 2025–2026  

---

## 1. Project Overview

This repository contains the complete LaTeX source, figures, TikZ vector diagrams, bibliography, and build scripts for the **141-page** academic project report titled:

> **"QuantumSafe VPN: Design, Implementation, and Evaluation of a Post-Quantum Cryptographic Virtual Private Network for Android"**

The project details the theoretical foundations, protocol engineering, Android native integration (`VpnService`), and experimental validation of a post-quantum secure tunneling mechanism leveraging **NIST FIPS 203 (ML-KEM-1024)**, **FIPS 204 (ML-DSA-87)**, **HKDF-SHA256**, and hardware-accelerated **AES-256-GCM** with a 64-bit sliding-window anti-replay mechanism.

---

## 2. Directory Structure

```text
QuantumSafeVPN_Report/
├── main.tex                             # Master LaTeX driver document
├── amritareport.cls                     # Institutional document class (Amrita Vishwa Vidyapeetham)
├── preamble.tex                         # Package imports, TikZ libraries, code styles, macros
├── references.bib                       # 45+ verified primary citations (IEEE, ACM, NIST FIPS, RFCs)
├── README.md                            # Documentation and compilation guide
├── frontmatter/
│   ├── abstract.tex                     # Formal abstract and keywords
│   └── abbreviations.tex                # Acronyms and notation list (longtable)
├── chapters/
│   ├── chapter01_introduction.tex       # Background, HNDL threat, Mosca's theorem, objectives
│   ├── chapter02_literature_review.tex  # PQC analysis, NIST standardization, Android VPN architecture
│   ├── chapter03_requirements.tex       # SRS, FRS/NFRS, TikZ use cases, user stories, RTM
│   ├── chapter04_system_design.tex      # Architecture, DFD L0/L1, sequence, UML, FSM, wireframes
│   ├── chapter05_security_analysis.tex  # Cryptographic proofs, IND-CCA2, STRIDE, quantum gate costs
│   ├── chapter06_android_ui.tex         # Minimal white design system, WCAG 2.1 AAA, Jetpack Compose
│   ├── chapter07_implementation.tex     # VpnService, JNI/PqcEngine, IP pool, multithreaded I/O
│   ├── chapter08_testing.tex            # Unit, integration, fuzzing, anti-replay, 20-test case matrix
│   ├── chapter09_results.tex            # APK footprint, latency, iperf3 throughput, PCAP analysis
│   ├── chapter10_deployment.tex         # Server systemd setup, iptables NAT, Android sideloading
│   └── chapter11_conclusion.tex         # Synthesis, objective achievements, lessons, future roadmap
├── appendices/
│   ├── appendixA_srs.tex                # Formal IEEE 830 Software Requirements Specification
│   ├── appendixB_test_matrix.tex        # Deep test execution catalogue and verification logs
│   ├── appendixC_deployment_guide.tex   # Hardened Linux deployment and APK release signing
│   ├── appendixD_wire_protocol.tex      # Binary wire packet framing offsets and JSON schemas
│   ├── appendixE_source_excerpts.tex    # Core Kotlin and Python source code listings
│   └── appendixF_pcap_dissection.tex    # Wireshark frame-by-frame hex dumps and dissection
└── figures/
    ├── Amrita_Logo.png                  # University crest (title page)
    ├── Amrita_Full_Logo.png             # Full university banner
    ├── vpn_cover_graphic.jpg            # Conceptual network tunnel illustration
    ├── pqc_tunnel_concept.jpg           # ML-KEM-1024 + HKDF + AES-GCM cryptographic pipeline
    ├── threat_model_concept.jpg         # STRIDE threat vectors vs PQC defense
    ├── ui_screens_overview.jpg          # 4-screen minimal white UI showcase
    ├── deployment_topology_concept.jpg  # End-to-end network deployment topology
    └── packet_capture_analysis.jpg      # Dissected Wireshark packet capture analysis
```

---

## 3. Compilation Instructions

The report requires a standard LaTeX distribution (MiKTeX 25.x or TeX Live 2024+) with `pdflatex` and `bibtex`.

### Windows PowerShell / Command Prompt:
```cmd
cd QuantumSafeVPN_Report
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

### Linux / macOS:
```bash
cd QuantumSafeVPN_Report
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

All 4 passes will compile cleanly with exit code `0`, generating `main.pdf` (141 pages, ~4.66 MB).

---

## 4. Metadata Placeholders for Submission

Before binding and formal departmental submission, update the institutional placeholders in `main.tex`:

| Placeholder | Location in `main.tex` | Description |
|---|---|---|
| `[Candidate Name]` | Line 31 (`\author{...}`) | Student author name(s) |
| `[Registration Number]` | Line 32 (`\rollnumber{...}`) | Institutional roll number(s) |
| `Dr. S. Udhayakumar` | Line 33 (`\guide{...}`) | Faculty Project Supervisor |
| `Assistant Professor` | Line 34 (`\guidedesignation{...}`) | Supervisor Designation |
| `Dr. S. Baghavathi Priya` | Line 35 (`\chairperson{...}`) | Chairperson / Head of Department |
| `Professor and Chairperson` | Line 36 (`\chairpersondesignation{...}`) | Chairperson Designation |
| `OCTOBER 2026` | Line 38 (`\submissiondate{...}`) | Month and year of defense |

---

## 5. Report Statistics and Compliance

- **Total Compiled Page Count:** 141 pages (Requirement: $\ge 101$ pages)
- **Bibliography:** 45 primary peer-reviewed papers, RFCs, and NIST standards (all resolved, 0 missing citations).
- **Cross-References:** All chapter, section, equation, figure, and table cross-references resolved (0 missing references).
- **Figures:** 8 high-resolution figures + 9 vector TikZ diagrams (Data Flow, Sequence, Class, Component, State Machine, Use Case, Threat Boundary).
- **Tables:** 16 formal academic tables formatted using `booktabs` and `longtable` (RTM, STRIDE, Test Matrix, Cryptographic Parameters, Protocol Framing).
