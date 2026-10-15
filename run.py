#!/usr/bin/env python3
"""
QuantumSafeVPN — Web Application Launcher
==========================================

Usage:
    python run.py              Start the web application (default port 8000)
    python run.py --port 9000  Start on a custom port
    python run.py --test       Run all security tests
    python run.py --benchmark  Run PQC benchmarks
"""
import os
import sys
import subprocess
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def check_dependencies():
    """Check and install required dependencies."""
    required = ["fastapi", "uvicorn"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"[*] Installing missing dependencies: {', '.join(missing)}")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "fastapi", "uvicorn[standard]",
            "--quiet"
        ])
        print("[+] Dependencies installed successfully")


def main():
    parser = argparse.ArgumentParser(
        description="QuantumSafeVPN — Post-Quantum Secure VPN Web Application"
    )
    parser.add_argument("--port", type=int, default=8000, help="Web server port (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Web server host (default: 0.0.0.0)")
    parser.add_argument("--test", action="store_true", help="Run security tests")
    parser.add_argument("--benchmark", action="store_true", help="Run PQC benchmarks")
    args = parser.parse_args()

    if args.test:
        print("=" * 60)
        print("  QuantumSafeVPN — Security Test Suite")
        print("=" * 60)
        tests = [
            "tests.test_mlkem",
            "tests.test_mldsa", 
            "tests.test_classical",
            "tests.test_vpn_tampering",
            "tests.test_ip_pool",
            "tests.test_integration"
        ]
        all_passed = True
        for t in tests:
            print(f"\n--- {t} ---")
            result = subprocess.run(
                [sys.executable, "-m", t], 
                cwd=PROJECT_ROOT
            )
            if result.returncode != 0:
                all_passed = False
        print("\n" + "=" * 60)
        print("  ALL TESTS PASSED [PASS]" if all_passed else "  SOME TESTS FAILED [FAIL]")
        print("=" * 60)
        sys.exit(0 if all_passed else 1)

    if args.benchmark:
        try:
            sys.path.insert(0, PROJECT_ROOT)
            from benchmark.benchmark import run_benchmarks
            run_benchmarks()
        except Exception as e:
            print(f"  Benchmark error: {e}")
        sys.exit(0)

    # Default: Launch Web Application
    check_dependencies()
    
    # Auto-detect if port is occupied (e.g. by Splunk or IIS)
    target_port = args.port
    import socket
    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        test_sock.bind((args.host, target_port))
        test_sock.close()
    except OSError:
        for fallback_p in [8001, 8002, 8888, 9000, 9090]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind((args.host, fallback_p))
                s.close()
                print(f"\n[!] Port {target_port} is in use by another service. Switching automatically to port {fallback_p}.\n")
                target_port = fallback_p
                break
            except OSError:
                continue

    print()
    print("=" * 60)
    print("  QuantumSafeVPN — Post-Quantum Web Application")
    print("  Quantum-Safe Network Security Platform")
    print("=" * 60)
    print()
    print(f"  🌐 Open in browser:  http://127.0.0.1:{target_port}")
    print(f"  📡 Listening on:     {args.host}:{target_port}")
    print()
    print("  Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    import uvicorn
    sys.path.insert(0, PROJECT_ROOT)
    uvicorn.run(
        "webapp.backend:app",
        host=args.host,
        port=target_port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
