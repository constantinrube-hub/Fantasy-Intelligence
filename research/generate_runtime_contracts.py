#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'config/contracts/runtime-contracts.json'
JS=ROOT/'app/generated/runtime-contracts.js'
PY=ROOT/'research/generated_runtime_contracts.py'

def canonical(obj): return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True)
def main():
    obj=json.loads(SRC.read_text(encoding='utf-8'))
    digest=hashlib.sha256(canonical(obj).encode()).hexdigest()
    JS.parent.mkdir(parents=True,exist_ok=True)
    JS.write_text("/* GENERATED from config/contracts/runtime-contracts.json. Do not edit. */\n(function(){'use strict';window.FIERuntimeContracts="+json.dumps({**obj,'contract_sha256':digest},separators=(',',':'))+";})();\n",encoding='utf-8')
    PY.write_text("# GENERATED from config/contracts/runtime-contracts.json. Do not edit.\nCONTRACT_SHA256 = %r\nCONTRACTS = %s\n"%(digest,repr(obj)),encoding='utf-8')
    print(JS.relative_to(ROOT));print(PY.relative_to(ROOT));print(digest)
if __name__=='__main__': main()
