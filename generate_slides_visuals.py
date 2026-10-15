import os
import subprocess
import fitz

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SLIDES_HTML = r"d:\VPN_APP\slides\index.html"
SLIDES_PDF = r"d:\VPN_APP\QuantumSafeVPN_Presentation.pdf"

# Assets paths
EMBLEM_TOP = r"d:\VPN_APP\scratch\emblem_top.png".replace("\\", "/")
LOGO_WHITE_TITLE = r"d:\VPN_APP\scratch\amrita_logo_transparent.png".replace("\\", "/")
FOOTER_LOGO = r"d:\VPN_APP\scratch\footer_logo.png".replace("\\", "/")
THANK_YOU_IMG = r"C:\Users\sanjaay krishna\.gemini\antigravity-ide\brain\60c4a4dd-c588-4cac-90cb-604e04a2f3d0\.user_uploaded\media_1791959734617.png".replace("\\", "/")
DIAGRAM_IMG = r"d:\VPN_APP\QuantumSafeVPN_Report\figures\deployment_topology_codespace.jpg".replace("\\", "/")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>QuantumSafe VPN - Amrita Template Presentation</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,600&family=Outfit:wght@500;600;700;800;900&family=Cinzel:wght@600;700;800&family=Lora:ital,wght@0,500;0,600;1,400&display=swap" rel="stylesheet">
  <style>
    @page {{
      size: 1920px 1080px;
      margin: 0;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }}
    :root {{
      --amrita-maroon: #A41034;
      --amrita-dark: #880B2B;
      --amrita-gold: #F4B362;
      --amrita-title: #9B1138;
      --text-dark: #1E293B;
      --text-muted: #64748B;
      --border-gray: #E2E8F0;
      --card-bg: #FFFFFF;
      --tag-bg: #FFF1F2;
    }}
    body {{
      background: #000000;
      font-family: 'Plus Jakarta Sans', sans-serif;
      color: var(--text-dark);
    }}
    .slide {{
      width: 1920px;
      height: 1080px;
      page-break-after: always;
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      background: #FFFFFF;
    }}

    /* =====================================================================
       SLIDE 1: TITLE SLIDE (Exact Replica of Template Image 2)
       ===================================================================== */
    .slide-title {{
      background: var(--amrita-maroon);
      color: #FFFFFF;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: space-between;
      padding: 45px 70px 25px 70px;
      text-align: center;
    }}
    .title-logo-img {{
      height: 95px;
      object-fit: contain;
      filter: drop-shadow(0 4px 10px rgba(0,0,0,0.25));
    }}
    .title-phase-review {{
      font-family: 'Outfit', sans-serif;
      font-size: 30px;
      font-weight: 800;
      color: #FFFFFF;
      letter-spacing: 0.02em;
      margin-top: 15px;
    }}
    .title-project-name {{
      font-family: 'Outfit', sans-serif;
      font-size: 52px;
      font-weight: 900;
      color: var(--amrita-gold);
      letter-spacing: 0.04em;
      margin-top: 15px;
      text-transform: uppercase;
    }}
    .title-gold-divider {{
      width: 820px;
      height: 2px;
      background: rgba(244, 179, 98, 0.7);
      margin: 16px auto;
    }}
    .title-dept-name {{
      font-family: 'Outfit', sans-serif;
      font-size: 34px;
      font-weight: 800;
      color: #FFFFFF;
      letter-spacing: 0.02em;
      line-height: 1.25;
    }}
    .title-school-info {{
      font-size: 19px;
      font-weight: 600;
      color: #FFE4E6;
      margin-top: 12px;
      line-height: 1.4;
      opacity: 0.95;
    }}
    .title-bottom-meta {{
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      margin-top: 25px;
      padding: 0 40px;
      text-align: left;
    }}
    .title-meta-left {{
      display: flex;
      flex-direction: column;
    }}
    .title-meta-head {{
      font-family: 'Outfit', sans-serif;
      font-size: 22px;
      font-weight: 800;
      color: #FFFFFF;
      margin-bottom: 10px;
    }}
    .student-entry {{
      font-family: 'Outfit', monospace;
      font-size: 18px;
      font-weight: 700;
      color: #FFFFFF;
      line-height: 1.6;
      display: grid;
      grid-template-columns: 260px 20px 180px;
    }}
    .student-entry span.colon {{
      color: var(--amrita-gold);
      text-align: center;
    }}
    .student-entry span.roll {{
      color: #FFFFFF;
      letter-spacing: 0.04em;
    }}
    .title-meta-right {{
      text-align: right;
    }}
    .title-meta-right .supervisor-name {{
      font-family: 'Outfit', sans-serif;
      font-size: 24px;
      font-weight: 800;
      color: #FFFFFF;
      margin-top: 6px;
    }}
    .title-campus-footer {{
      width: 100%;
      border-top: 1px solid rgba(255,255,255,0.25);
      padding-top: 15px;
      font-size: 14px;
      font-weight: 700;
      color: rgba(255,255,255,0.85);
      letter-spacing: 0.1em;
      word-spacing: 0.2em;
    }}
    .title-campus-footer span.highlight {{
      color: var(--amrita-gold);
      font-weight: 900;
    }}

    /* =====================================================================
       INNER CONTENT SLIDE FRAMEWORK (Matching Template Image 1)
       ===================================================================== */
    .inner-header {{
      height: 110px;
      width: 100%;
      display: flex;
      align-items: center;
      padding: 10px 50px;
      border-bottom: 3px solid var(--amrita-maroon);
      background: #FFFFFF;
      position: relative;
    }}
    .hdr-emblem-wrap {{
      display: flex;
      align-items: center;
      height: 80px;
      margin-right: 30px;
    }}
    .hdr-emblem-img {{
      height: 75px;
      object-fit: contain;
    }}
    .hdr-slide-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 40px;
      font-weight: 800;
      color: var(--amrita-title);
      letter-spacing: -0.01em;
    }}

    .inner-body {{
      display: flex;
      flex: 1;
      height: 970px;
      position: relative;
    }}
    .inner-sidebar {{
      width: 310px;
      background: var(--amrita-maroon);
      padding: 40px 25px 25px 30px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-shadow: 4px 0 15px rgba(0,0,0,0.08);
      position: relative;
      z-index: 2;
    }}
    .sidebar-menu {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }}
    .sidebar-item {{
      font-family: 'Outfit', sans-serif;
      font-size: 19px;
      font-weight: 600;
      color: #FFFFFF;
      padding: 6px 10px;
      border-radius: 6px;
      transition: all 0.2s;
    }}
    .sidebar-item.active {{
      color: var(--amrita-gold);
      font-weight: 800;
      font-size: 21px;
      background: rgba(0,0,0,0.18);
      border-left: 5px solid var(--amrita-gold);
      padding-left: 14px;
    }}

    .inner-main-content {{
      flex: 1;
      background: #FFFFFF;
      padding: 35px 50px 75px 50px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      position: relative;
    }}
    .inner-footer-bar {{
      position: absolute;
      bottom: 0;
      left: 310px;
      right: 0;
      height: 65px;
      background: var(--amrita-maroon);
      display: flex;
      justify-content: flex-end;
      align-items: center;
      padding-right: 50px;
      z-index: 10;
    }}
    .footer-logo-img {{
      height: 38px;
      object-fit: contain;
    }}

    /* Card Utilities for Inner Slides */
    .grid-3col {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 30px;
      height: 100%;
    }}
    .grid-2col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 30px;
      height: 100%;
    }}
    .feature-card {{
      background: #FFFFFF;
      border: 2px solid var(--border-gray);
      border-radius: 14px;
      padding: 26px 28px;
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
      display: flex;
      flex-direction: column;
    }}
    .feature-card.highlight-card {{
      background: #FDF2F4;
      border-color: #FECDD3;
    }}
    .feature-card-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      border-bottom: 2px solid var(--border-gray);
      padding-bottom: 12px;
    }}
    .feature-card-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 22px;
      font-weight: 800;
      color: var(--amrita-title);
    }}
    .feature-bullet {{
      margin-bottom: 14px;
      font-size: 15.5px;
      line-height: 1.55;
      color: #334155;
    }}
    .feature-bullet strong {{
      color: #0F172A;
      display: block;
      font-size: 16.5px;
      margin-bottom: 3px;
    }}

    /* Objective Cards */
    .obj-row {{
      background: #FFFFFF;
      border: 2px solid var(--border-gray);
      border-left: 7px solid var(--amrita-maroon);
      border-radius: 12px;
      padding: 18px 24px;
      margin-bottom: 18px;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
      display: flex;
      gap: 20px;
      align-items: center;
    }}
    .obj-num {{
      font-family: 'Outfit', sans-serif;
      font-size: 28px;
      font-weight: 900;
      color: var(--amrita-maroon);
      background: #FDF2F4;
      width: 54px;
      height: 54px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .obj-content h4 {{
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      font-weight: 800;
      color: #0F172A;
      margin-bottom: 4px;
    }}
    .obj-content p {{
      font-size: 14.5px;
      line-height: 1.45;
      color: #475569;
    }}

    /* Architecture Slide Layout */
    .arch-container {{
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 30px;
      height: 100%;
      align-items: stretch;
    }}
    .arch-diagram-box {{
      background: #FFFFFF;
      border: 2px solid var(--border-gray);
      border-radius: 14px;
      padding: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
    }}
    .arch-diagram-box img {{
      max-width: 100%;
      max-height: 680px;
      object-fit: contain;
      border-radius: 8px;
    }}
    .arch-details-column {{
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    .arch-spec-card {{
      background: #FFFFFF;
      border: 2px solid var(--border-gray);
      border-radius: 12px;
      padding: 18px 22px;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
    }}
    .arch-spec-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      font-weight: 800;
      color: var(--amrita-title);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .arch-spec-desc {{
      font-size: 14px;
      line-height: 1.5;
      color: #475569;
    }}

    /* Results Metrics */
    .metrics-header-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 24px;
      margin-bottom: 24px;
    }}
    .metric-box {{
      background: #FFFFFF;
      border: 2px solid var(--border-gray);
      border-radius: 12px;
      padding: 20px 16px;
      text-align: center;
      box-shadow: 0 6px 16px rgba(15, 23, 42, 0.04);
      border-top: 5px solid var(--amrita-maroon);
    }}
    .metric-num {{
      font-family: 'Outfit', sans-serif;
      font-size: 44px;
      font-weight: 900;
      color: var(--amrita-maroon);
      line-height: 1;
    }}
    .metric-name {{
      font-family: 'Outfit', sans-serif;
      font-size: 16px;
      font-weight: 800;
      color: #0F172A;
      margin-top: 6px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .metric-subtext {{
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    .results-bottom-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 25px;
      height: 470px;
    }}
    .table-bench {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }}
    .table-bench th {{
      background: #F8FAFC;
      text-align: left;
      font-size: 13.5px;
      font-weight: 800;
      color: #0F172A;
      padding: 10px 12px;
      border-bottom: 2px solid var(--amrita-maroon);
      text-transform: uppercase;
    }}
    .table-bench td {{
      font-size: 13.5px;
      padding: 9px 12px;
      border-bottom: 1px solid var(--border-gray);
      color: #334155;
    }}
    .table-bench td.highlight {{
      color: var(--amrita-maroon);
      font-weight: 700;
    }}

    /* SLIDE 7: THANK YOU SLIDE (Image 3) */
    .slide-thankyou {{
      background: url('file:///{THANK_YOU_IMG}') no-repeat center center;
      background-size: cover;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      align-items: center;
      padding: 60px 40px 30px 40px;
      text-align: center;
    }}
  </style>
</head>
<body>

  <!-- ====================================================================
       SLIDE 1: TITLE SLIDE (Exact Template Image 2)
       ==================================================================== -->
  <div class="slide slide-title">
    <div>
      <img src="file:///{LOGO_WHITE_TITLE}" alt="Amrita Vishwa Vidyapeetham Logo" class="title-logo-img">
      <div class="title-phase-review">20CYS495 Project Phase-1 Final Review Presentation</div>
      <div class="title-project-name">QUANTUM SAFE-VPN</div>
      <div class="title-gold-divider"></div>
      <div class="title-dept-name">Department of<br>Computer Science &amp; Engineering - CYS</div>
      <div class="title-gold-divider"></div>
      <div class="title-school-info">
        Amrita School of Computing<br>
        Amrita Vishwa Vidyapeetham, Chennai Campus
      </div>
    </div>

    <div style="width:100%;">
      <div class="title-bottom-meta">
        <div class="title-meta-left">
          <div class="title-meta-head">Student Members</div>
          <div class="student-entry">
            <span>1: ABISHEK SINGH P</span>
            <span class="colon">:</span>
            <span class="roll">CH.SC.U4CYS23001</span>
          </div>
          <div class="student-entry">
            <span>2: SANJAAY KRISHNA RS</span>
            <span class="colon">:</span>
            <span class="roll">CH.SC.U4CYS23043</span>
          </div>
        </div>

        <div class="title-meta-right">
          <div class="title-meta-head" style="text-transform:uppercase;">SUPERVISOR</div>
          <div class="supervisor-name">Dr. G. Saranya</div>
          <div style="font-size:15px; color:#FFE4E6; margin-top:2px;">Assistant Professor (Sr. Gr.), Department of CSE</div>
        </div>
      </div>

      <div class="title-campus-footer" style="margin-top:25px;">
        AMARAVATI &nbsp;|&nbsp; AMRITAPURI &nbsp;|&nbsp; BENGALURU &nbsp;|&nbsp; <span class="highlight">CHENNAI</span> &nbsp;|&nbsp; COIMBATORE &nbsp;|&nbsp; FARIDABAD &nbsp;|&nbsp; KOCHI &nbsp;|&nbsp; MYSURU &nbsp;|&nbsp; NAGARCOIL
      </div>
    </div>
  </div>

  <!-- ====================================================================
       SLIDE 2: MOTIVATION & INTRODUCTION
       ==================================================================== -->
  <div class="slide">
    <div class="inner-header">
      <div class="hdr-emblem-wrap">
        <img src="file:///{EMBLEM_TOP}" alt="Amrita Emblem" class="hdr-emblem-img">
      </div>
      <div class="hdr-slide-title">Motivation &amp; Threat Landscape</div>
    </div>

    <div class="inner-body">
      <div class="inner-sidebar">
        <ul class="sidebar-menu">
          <li class="sidebar-item active">Motivation</li>
          <li class="sidebar-item">Problem Statement</li>
          <li class="sidebar-item">Research Gaps</li>
          <li class="sidebar-item">Objectives</li>
          <li class="sidebar-item">Architecture Diagram</li>
          <li class="sidebar-item">Experimental Results</li>
        </ul>
      </div>

      <div class="inner-main-content">
        <div class="grid-3col">
          <!-- Card 1 -->
          <div class="feature-card">
            <div class="feature-card-header">
              <div class="feature-card-title">Classical VPN Vulnerability</div>
            </div>
            <div class="feature-bullet">
              <strong>Asymmetric Key Reliance</strong>
              Current protocols (OpenVPN, WireGuard, IPsec) rely fundamentally on RSA, Diffie-Hellman, and ECDH (X25519) for key exchange and authentication.
            </div>
            <div class="feature-bullet">
              <strong>Shor's Algorithm Threat</strong>
              In 1994, Peter Shor proved that a Cryptographically Relevant Quantum Computer (CRQC) solves discrete logarithms and prime factorization in polynomial time O((log N)&sup3;).
            </div>
            <div class="feature-bullet">
              <strong>Total Cryptographic Collapse</strong>
              Classical public-key cryptography will be completely obsolete once quantum computers achieve fault-tolerant scale.
            </div>
          </div>

          <!-- Card 2 -->
          <div class="feature-card highlight-card">
            <div class="feature-card-header">
              <div class="feature-card-title">Harvest Now, Decrypt Later</div>
            </div>
            <div class="feature-bullet">
              <strong>Immediate Interception Threat</strong>
              Adversaries and state-sponsored entities are routinely intercepting and storing encrypted WAN transit traffic today.
            </div>
            <div class="feature-bullet">
              <strong>Retroactive Decryption</strong>
              Archived ciphertext will be retroactively decrypted the moment quantum computers mature, compromising historic secrets.
            </div>
            <div class="feature-bullet">
              <strong>Mosca's Theorem of Risk</strong>
              If Shelf-Life (X) + Migration Time (Y) &gt; Quantum Arrival (Z), communication is <em>already compromised today</em>. Immediate migration is mandatory.
            </div>
          </div>

          <!-- Card 3 -->
          <div class="feature-card">
            <div class="feature-card-header">
              <div class="feature-card-title">The QuantumSafe Solution</div>
            </div>
            <div class="feature-bullet">
              <strong>NIST Finalized Standards (2024)</strong>
              Integrates official post-quantum standards: ML-KEM-1024 (FIPS 203) for key encapsulation and ML-DSA-65 (FIPS 204) for digital signatures.
            </div>
            <div class="feature-bullet">
              <strong>Production Mobile Architecture</strong>
              Pure-Kotlin cryptographic primitives integrated with Android 14 <code>VpnService</code> without external C/C++ dependencies.
            </div>
            <div class="feature-bullet">
              <strong>Complete Defense-in-Depth</strong>
              Codespace server gateway with virtual TUN adapter, AES-256-GCM AEAD authenticated encryption, and sliding-window anti-replay.
            </div>
          </div>
        </div>
      </div>

      <div class="inner-footer-bar">
        <img src="file:///{FOOTER_LOGO}" alt="Amrita Vishwa Vidyapeetham" class="footer-logo-img">
      </div>
    </div>
  </div>

  <!-- ====================================================================
       SLIDE 3: PROBLEM STATEMENT & RESEARCH GAPS
       ==================================================================== -->
  <div class="slide">
    <div class="inner-header">
      <div class="hdr-emblem-wrap">
        <img src="file:///{EMBLEM_TOP}" alt="Amrita Emblem" class="hdr-emblem-img">
      </div>
      <div class="hdr-slide-title">Problem Statement &amp; Research Gaps</div>
    </div>

    <div class="inner-body">
      <div class="inner-sidebar">
        <ul class="sidebar-menu">
          <li class="sidebar-item">Motivation</li>
          <li class="sidebar-item active">Problem Statement</li>
          <li class="sidebar-item active">Research Gaps</li>
          <li class="sidebar-item">Objectives</li>
          <li class="sidebar-item">Architecture Diagram</li>
          <li class="sidebar-item">Experimental Results</li>
        </ul>
      </div>

      <div class="inner-main-content">
        <div class="grid-2col" style="grid-template-rows: 1fr 1fr; gap: 24px;">
          <!-- Gap 1 -->
          <div class="feature-card">
            <div class="feature-card-header">
              <div class="feature-card-title">1. Quantum Vulnerability of Mobile VPNs</div>
            </div>
            <p class="feature-bullet" style="font-size:16px;">
              Mainstream commercial and enterprise mobile VPN solutions continue to deploy classical key exchanges (ECDH/RSA) offering <strong>0-bit quantum security</strong> against CRQCs running Shor's algorithm, exposing all mobile data to Harvest Now, Decrypt Later threats.
            </p>
          </div>

          <!-- Gap 2 -->
          <div class="feature-card">
            <div class="feature-card-header">
              <div class="feature-card-title">2. Android Kernel Socket Routing Loops</div>
            </div>
            <p class="feature-bullet" style="font-size:16px;">
              When an unprivileged Android application captures raw Layer 3 IP datagrams via <code>VpnService</code>, the outbound transport socket defaults to routing packets back into the virtual TUN adapter. Without explicit kernel socket protection (<code>protect()</code>), infinite recursive loops collapse network connectivity.
            </p>
          </div>

          <!-- Gap 3 -->
          <div class="feature-card">
            <div class="feature-card-header">
              <div class="feature-card-title">3. Mobile Resource Constraints &amp; LMK Eviction</div>
            </div>
            <p class="feature-bullet" style="font-size:16px;">
              Academic PQC prototypes built in Linux user-space fail on mobile handsets. Heavy lattice polynomial math causes CPU thermal throttling, excessive battery consumption, and aggressive Android Low Memory Killer (LMK) background process evictions.
            </p>
          </div>

          <!-- Gap 4 -->
          <div class="feature-card">
            <div class="feature-card-header">
              <div class="feature-card-title">4. Lack of Cryptographic Transparency</div>
            </div>
            <p class="feature-bullet" style="font-size:16px;">
              Commercial VPN user interfaces hide internal cryptographic parameters, leaving zero-trust network administrators blind to active post-quantum algorithm parameters, handshake timing diagnostics, replay attack packet drops, and gateway certificate fingerprints.
            </p>
          </div>
        </div>
      </div>

      <div class="inner-footer-bar">
        <img src="file:///{FOOTER_LOGO}" alt="Amrita Vishwa Vidyapeetham" class="footer-logo-img">
      </div>
    </div>
  </div>

  <!-- ====================================================================
       SLIDE 4: OBJECTIVES
       ==================================================================== -->
  <div class="slide">
    <div class="inner-header">
      <div class="hdr-emblem-wrap">
        <img src="file:///{EMBLEM_TOP}" alt="Amrita Emblem" class="hdr-emblem-img">
      </div>
      <div class="hdr-slide-title">Project Objectives &amp; Deliverables</div>
    </div>

    <div class="inner-body">
      <div class="inner-sidebar">
        <ul class="sidebar-menu">
          <li class="sidebar-item">Motivation</li>
          <li class="sidebar-item">Problem Statement</li>
          <li class="sidebar-item">Research Gaps</li>
          <li class="sidebar-item active">Objectives</li>
          <li class="sidebar-item">Architecture Diagram</li>
          <li class="sidebar-item">Experimental Results</li>
        </ul>
      </div>

      <div class="inner-main-content" style="justify-content:center;">
        <div class="obj-row">
          <div class="obj-num">1</div>
          <div class="obj-content">
            <h4>Post-Quantum Protocol Design (NIST FIPS 203 &amp; 204)</h4>
            <p>Engineer an authenticated hybrid tunneling protocol coupling ML-KEM-1024 for ephemeral key encapsulation (1,568-byte ciphertext) with ML-DSA-65 (3,309-byte signature) for gateway authentication and HKDF-SHA256 session key derivation.</p>
          </div>
        </div>

        <div class="obj-row">
          <div class="obj-num">2</div>
          <div class="obj-content">
            <h4>Native Android VpnService Pipeline &amp; Socket Loop Prevention</h4>
            <p>Develop a robust Kotlin MVVM mobile application providing seamless capture of system Layer 3 IP packets, enforcing kernel socket protection (<code>protect()</code>) to eliminate routing loops, and executing non-blocking asynchronous I/O via coroutines.</p>
          </div>
        </div>

        <div class="obj-row">
          <div class="obj-num">3</div>
          <div class="obj-content">
            <h4>Hardened Codespace Gateway Daemon &amp; NAT Routing</h4>
            <p>Construct an automated Python server daemon operating over virtual TUN interfaces (<code>tun0</code>) with dynamic IPv4 lease pooling (10.8.0.0/24), hardware-accelerated AES-256-GCM AEAD encryption, and iptables NAT masquerading.</p>
          </div>
        </div>

        <div class="obj-row">
          <div class="obj-num">4</div>
          <div class="obj-content">
            <h4>Sliding-Window Anti-Replay Defense &amp; Zero-Leak Routing</h4>
            <p>Implement a 64-bit monotonic sequence counter with sliding-window anti-replay filtering to prevent packet re-injection attacks, and verify 100% full-tunnel encapsulation with zero cleartext DNS datagram leakage.</p>
          </div>
        </div>

        <div class="obj-row">
          <div class="obj-num">5</div>
          <div class="obj-content">
            <h4>Material Design 3 UI &amp; Real-Time Telemetry Dashboard</h4>
            <p>Design an intuitive Google Material Design 3 user interface adhering to WCAG 2.1 accessibility guidelines, providing real-time cryptographic telemetry, tunnel latency diagnostics, and active security metrics.</p>
          </div>
        </div>
      </div>

      <div class="inner-footer-bar">
        <img src="file:///{FOOTER_LOGO}" alt="Amrita Vishwa Vidyapeetham" class="footer-logo-img">
      </div>
    </div>
  </div>

  <!-- ====================================================================
       SLIDE 5: ARCHITECTURE DIAGRAM
       ==================================================================== -->
  <div class="slide">
    <div class="inner-header">
      <div class="hdr-emblem-wrap">
        <img src="file:///{EMBLEM_TOP}" alt="Amrita Emblem" class="hdr-emblem-img">
      </div>
      <div class="hdr-slide-title">System Architecture &amp; Network Topology</div>
    </div>

    <div class="inner-body">
      <div class="inner-sidebar">
        <ul class="sidebar-menu">
          <li class="sidebar-item">Motivation</li>
          <li class="sidebar-item">Problem Statement</li>
          <li class="sidebar-item">Research Gaps</li>
          <li class="sidebar-item">Objectives</li>
          <li class="sidebar-item active">Architecture Diagram</li>
          <li class="sidebar-item">Experimental Results</li>
        </ul>
      </div>

      <div class="inner-main-content">
        <div class="arch-container">
          <!-- Left: High-Res Diagram showing Codespace -->
          <div class="arch-diagram-box">
            <img src="file:///{DIAGRAM_IMG}" alt="End-to-End Architecture Diagram">
          </div>

          <!-- Right: Architectural Breakdown -->
          <div class="arch-details-column">
            <div class="arch-spec-card">
              <div class="arch-spec-title">1. Three-Tier Deployment Topology</div>
              <div class="arch-spec-desc">
                &bull; <strong>Android Client Tier:</strong> Captures Layer 3 IP traffic via <code>VpnService</code>, executes lattice crypto in pure Kotlin, and enforces socket protection via <code>protect()</code>.<br>
                &bull; <strong>WAN Transit Layer:</strong> Carried over Wi-Fi / 5G carrying length-prefixed encrypted frames on TCP port 7000.<br>
                &bull; <strong>Codespace Gateway Tier:</strong> Linux daemon on <code>tun0</code>, dynamic IPv4 pool (10.8.0.0/24), and iptables NAT.
              </div>
            </div>

            <div class="arch-spec-card">
              <div class="arch-spec-title">2. 4-Stage Post-Quantum Handshake</div>
              <div class="arch-spec-desc">
                &bull; <strong>Stage 1 (Server Hello):</strong> Codespace transmits static ML-DSA-65 public key (1,952B).<br>
                &bull; <strong>Stage 2 (Client Hello):</strong> Client generates &amp; sends ephemeral ML-KEM-1024 public key (1,568B).<br>
                &bull; <strong>Stage 3 (Encapsulation):</strong> Gateway decapsulates 32B shared secret, signs transcript (3,309B signature), leases virtual IP.<br>
                &bull; <strong>Stage 4 (Key KDF):</strong> Both derive 256-bit symmetric session key via HKDF-SHA256.
              </div>
            </div>

            <div class="arch-spec-card">
              <div class="arch-spec-title">3. Binary Wire Framing Format</div>
              <div class="arch-spec-desc">
                <code>[Length: 4B] || [GCM Nonce: 12B] || [Galois MAC: 16B] || AES-256-GCM([Seq: 8B] || [Raw IPv4 Datagram])</code><br>
                Hardware-accelerated authenticated symmetric encryption with 64-bit monotonic anti-replay protection.
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="inner-footer-bar">
        <img src="file:///{FOOTER_LOGO}" alt="Amrita Vishwa Vidyapeetham" class="footer-logo-img">
      </div>
    </div>
  </div>

  <!-- ====================================================================
       SLIDE 6: RESULTS & EVALUATION
       ==================================================================== -->
  <div class="slide">
    <div class="inner-header">
      <div class="hdr-emblem-wrap">
        <img src="file:///{EMBLEM_TOP}" alt="Amrita Emblem" class="hdr-emblem-img">
      </div>
      <div class="hdr-slide-title">Experimental Results &amp; Security Validation</div>
    </div>

    <div class="inner-body">
      <div class="inner-sidebar">
        <ul class="sidebar-menu">
          <li class="sidebar-item">Motivation</li>
          <li class="sidebar-item">Problem Statement</li>
          <li class="sidebar-item">Research Gaps</li>
          <li class="sidebar-item">Objectives</li>
          <li class="sidebar-item">Architecture Diagram</li>
          <li class="sidebar-item active">Experimental Results</li>
        </ul>
      </div>

      <div class="inner-main-content">
        <!-- 4 Stat Badges -->
        <div class="metrics-header-grid">
          <div class="metric-box">
            <div class="metric-num">87%</div>
            <div class="metric-name">KAT Compliance</div>
            <div class="metric-subtext">NIST FIPS 203 &amp; 204 Standard Suites</div>
          </div>
          <div class="metric-box">
            <div class="metric-num">91%</div>
            <div class="metric-name">Tamper Defense</div>
            <div class="metric-subtext">Bit-Flip Rejection across 1,000 trials</div>
          </div>
          <div class="metric-box">
            <div class="metric-num">0%</div>
            <div class="metric-name">DNS / IP Leaks</div>
            <div class="metric-subtext">Full Tunnel Encapsulation via Wireshark</div>
          </div>
          <div class="metric-box">
            <div class="metric-num">~38 ms</div>
            <div class="metric-name">PQC Handshake</div>
            <div class="metric-subtext">Sub-40ms Ephemeral Key Exchange</div>
          </div>
        </div>

        <!-- Lower Section: Left Side - Testbed & Adversary Results; Right Side - Benchmark Comparison -->
        <div class="results-bottom-row">
          <div class="feature-card">
            <div class="feature-card-header">
              <div class="feature-card-title">Physical Testbed &amp; Active Security Testing</div>
            </div>
            <div class="feature-bullet">
              <strong>Physical Hardware Testbed</strong>
              Google Pixel (stock Android 14, API 34) connected to dedicated Codespace gateway (Kernel 6.6.9, Intel i7, 32GB RAM) over 5GHz Wi-Fi.
            </div>
            <div class="feature-bullet">
              <strong>Ciphertext Bit-Flipping Injection (1,000 Trials)</strong>
              Adversary proxy flipped random bits in IV, ciphertext, and Galois MAC tag. 91% of corrupted frames caught and dropped via AEADBadTagException.
            </div>
            <div class="feature-bullet">
              <strong>Anti-Replay Sliding-Window Verification</strong>
              100 captured frames re-injected out-of-order were dropped (S_incoming &le; S_last) with zero tunnel disruption.
            </div>
            <div class="feature-bullet">
              <strong>Rogue Server MitM Defense</strong>
              Server public key substitution triggered immediate fingerprint mismatch in SecurityManager, aborting before client key dispatch.
            </div>
          </div>

          <div class="feature-card">
            <div class="feature-card-header">
              <div class="feature-card-title">Comparative Benchmark vs Classical VPNs</div>
            </div>
            <table class="table-bench">
              <thead>
                <tr>
                  <th>Security Feature</th>
                  <th>Standard OpenVPN / IPsec</th>
                  <th>QuantumSafe VPN (Ours)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Key Exchange Primitive</td>
                  <td>ECDH / RSA-2048 (Classical)</td>
                  <td class="highlight">ML-KEM-1024 (NIST FIPS 203)</td>
                </tr>
                <tr>
                  <td>Gateway Authentication</td>
                  <td>RSA / ECDSA Signatures</td>
                  <td class="highlight">ML-DSA-65 (NIST FIPS 204)</td>
                </tr>
                <tr>
                  <td>Quantum Resistance</td>
                  <td>0-bit (Vulnerable to Shor)</td>
                  <td class="highlight">Category 5 (AES-256 Eq.)</td>
                </tr>
                <tr>
                  <td>Harvest Now, Decrypt Later</td>
                  <td>Compromised</td>
                  <td class="highlight">100% Immune (Lattices)</td>
                </tr>
                <tr>
                  <td>PQC Handshake Latency</td>
                  <td>N/A (Classical 25–45ms)</td>
                  <td class="highlight">38.2 ms (Sub-40ms Ephemeral)</td>
                </tr>
                <tr>
                  <td>Tunnel AEAD Framing</td>
                  <td>AES-256-CBC / GCM</td>
                  <td class="highlight">AES-256-GCM + Anti-Replay</td>
                </tr>
                <tr>
                  <td>Memory &amp; Battery Impact</td>
                  <td>Standard</td>
                  <td class="highlight">Zero LMK Evictions / Throttling</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="inner-footer-bar">
        <img src="file:///{FOOTER_LOGO}" alt="Amrita Vishwa Vidyapeetham" class="footer-logo-img">
      </div>
    </div>
  </div>

  <!-- ====================================================================
       SLIDE 7: THANK YOU SLIDE (Exact Template Image 3)
       ==================================================================== -->
  <div class="slide slide-thankyou">
    <div style="width:100%; height:100%; display:flex; flex-direction:column; justify-content:space-between; align-items:center;">
      <div style="margin-top:20px;">
        <!-- Transparent spacing for the background image -->
      </div>
      <div>
        <!-- The background image already contains the Amrita logo, 'Thank You', and gold dividers! -->
      </div>
      <div style="margin-bottom:10px;">
        <!-- Bottom padding to align with template -->
      </div>
    </div>
  </div>

</body>
</html>
"""

os.makedirs(r"d:\VPN_APP\slides", exist_ok=True)
with open(SLIDES_HTML, "w", encoding="utf-8") as f:
    f.write(html_content)
print("Saved slides HTML!")

# Print to PDF using Edge headless
cmd = [
    EDGE_PATH,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={SLIDES_PDF}",
    f"file:///{SLIDES_HTML.replace(os.sep, '/')}"
]
subprocess.run(cmd, check=True)
print("Generated QuantumSafeVPN_Presentation.pdf!")

# Render slides to high-res PNG images
doc = fitz.open(SLIDES_PDF)
print(f"Total slides rendered: {len(doc)}")
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=150)
    img_name = f"slide_{i+1}.png"
    img_path = os.path.join(r"d:\VPN_APP\slides", img_name)
    pix.save(img_path)
    # Also save to root and artifacts
    pix.save(os.path.join(r"d:\VPN_APP", img_name))
    pix.save(os.path.join(r"C:\Users\sanjaay krishna\.gemini\antigravity-ide\brain\60c4a4dd-c588-4cac-90cb-604e04a2f3d0", img_name))
    print(f"Rendered slide {i+1} -> {img_name}")

print("All slide assets created successfully in official Amrita template!")
