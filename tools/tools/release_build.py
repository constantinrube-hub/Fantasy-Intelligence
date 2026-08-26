#!/usr/bin/env python3
"""One-command deterministic FIE release build.

This is the supported local release entry point. It regenerates all browser
contracts/configuration, hashes the final source components, builds the isolated
Cloudflare Pages output, and runs the bounded source release gate.
"""
from __future__ import annotations
import argparse, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def run(*args: str) -> None:
    cmd = [sys.executable if args[0] == 'python' else args[0], *args[1:]]
    print('+', ' '.join(map(str, cmd)), flush=True)
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['personal', 'public'], default='personal')
    ns = ap.parse_args()
    run('python', 'research/generate_runtime_contracts.py')
    run('python', 'research/generate_model_config.py')
    run('python', 'research/generate_release_descriptor.py')
    run('python', 'research/build_app_manifest.py')
    run('python', 'tools/build_dist.py', '--mode', ns.mode)
    run('python', 'research/release_gate.py')
    print(f'RELEASE BUILD COMPLETE: mode={ns.mode} output=dist/')

if __name__ == '__main__':
    main()
