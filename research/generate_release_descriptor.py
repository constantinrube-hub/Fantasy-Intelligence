#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=json.load(open(ROOT/'config/release.json',encoding='utf-8'))
js='/* generated; do not edit */\nwindow.FIE_RELEASE='+json.dumps(src,separators=(',',':'))+';\n'
(ROOT/'app/generated/release.js').write_text(js,encoding='utf-8')
fun='/* generated; do not edit */\nexport const FIE_RELEASE='+json.dumps(src,separators=(',',':'))+';\n'
(ROOT/'functions/release.js').write_text(fun,encoding='utf-8')
print(src['release'])
