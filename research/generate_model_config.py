#!/usr/bin/env python3
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];src=ROOT/'config/model-config.json';out=ROOT/'app/generated/model-config.js'
obj=json.loads(src.read_text());raw=json.dumps(obj,sort_keys=True,separators=(',',':')).encode();obj['sha256']=hashlib.sha256(raw).hexdigest();out.write_text("/* GENERATED from config/model-config.json. */\n(function(){window.FIE_MODEL_CONFIG="+json.dumps(obj,separators=(',',':'))+";})();\n")
print(out.relative_to(ROOT))
