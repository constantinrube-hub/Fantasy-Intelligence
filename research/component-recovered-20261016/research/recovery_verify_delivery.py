"""Dependency-free verification of extracted source/runtime package contents."""
from pathlib import Path
import hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
def run(root=ROOT):
    errors=[];count=0
    for name in ['SOURCE-FILES.json','RUNTIME-FILES.json']:
        path=root/name
        if not path.is_file():errors.append('MISSING_MANIFEST:'+name);continue
        manifest=json.loads(path.read_text())
        for rel,h in manifest.items():
            p=(root/rel).resolve()
            if not p.is_relative_to(root.resolve()) or not p.is_file():errors.append('MISSING_OR_UNSAFE:'+rel);continue
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:errors.append('HASH:'+rel)
            count+=1
            if p.suffix=='.npz':
                try:
                    with zipfile.ZipFile(p) as z:
                        if z.testzip() is not None:errors.append('ARCHIVE_CRC:'+rel)
                except zipfile.BadZipFile:errors.append('ARCHIVE_TRUNCATED:'+rel)
    result={'status':'PASS' if not errors else 'FAIL','verified_files':count,'errors':errors[:30],'error_count':len(errors)}
    print(json.dumps(result));return 1 if errors else 0
if __name__=='__main__':raise SystemExit(run())
