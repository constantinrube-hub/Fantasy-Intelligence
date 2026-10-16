"""Portable first-write IO and source verification for the component recovery."""
from pathlib import Path
import gzip,hashlib,json,os,io,zipfile
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
BASE=Path('data/research/components/recovery-20261016')
OLD=Path('data/research/components/2026-10-14/c2-c4-v1/captures/20261014T174651230972Z/issuance')
JOINT=Path('data/research/components/2026-10-15/joint-v5')
TRAINING=Path('data/research/components/2026-10-14/c2-c4-v1/priors')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def now():return datetime.now(timezone.utc).isoformat()
def clock(t):
    d=datetime.fromisoformat(str(t).replace('Z','+00:00'))
    if d.tzinfo is None:raise ValueError('TIMEZONE_REQUIRED')
    return d.astimezone(timezone.utc)
def write(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    if p.exists():
        if p.read_bytes()!=raw:raise ValueError('IMMUTABLE_REVISION_EXISTS:'+str(p))
    else:atomic_bytes(p,raw)
def rows(p):
    with gzip.open(p,'rt',encoding='utf-8') as f:
        for x in f:
            if x.strip():yield json.loads(x)
def lines(p,rs):
    writer=AtomicJsonLines(p)
    for r in rs:writer.append(r)
    writer.close()
def verified(root,ref,cutoff=None):
    rel=Path(ref['path']);p=(Path(root)/rel).resolve()
    if rel.is_absolute() or '..' in rel.parts or not p.is_relative_to(Path(root).resolve()):raise ValueError('UNSAFE_SOURCE_PATH')
    if not p.is_file() or sha(p)!=ref['sha256']:raise ValueError('SOURCE_HASH_MISMATCH:'+str(rel))
    if cutoff and clock(ref['observed_at'])>clock(cutoff):raise ValueError('SOURCE_AFTER_CUTOFF')
    return p
def closure(folder,root=ROOT):return {p.relative_to(root).as_posix():sha(p) for p in sorted(Path(folder).rglob('*')) if p.is_file()}
def atomic_bytes(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.partial')
    with tmp.open('xb') as f:
        if f.write(raw)!=len(raw):raise ValueError('SHORT_FILE_WRITE')
        f.flush();os.fsync(f.fileno())
    if tmp.read_bytes()!=raw:raise ValueError('TEMPORARY_WRITE_DID_NOT_PRESERVE_BYTES')
    os.replace(tmp,path)
    if path.read_bytes()!=raw:raise ValueError('FINAL_WRITE_DID_NOT_PRESERVE_BYTES')
class AtomicJsonLines:
    def __init__(self,path):
        self.path=Path(path);self.rows=0
        if self.path.exists():raise ValueError('IMMUTABLE_ROWS_EXIST:'+str(path))
        self.buffer=io.BytesIO();self.gz=gzip.GzipFile(filename='',fileobj=self.buffer,mode='wb',mtime=0)
    def append(self,value):
        self.gz.write((json.dumps(value,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n').encode());self.rows+=1
    def close(self):
        self.gz.close();raw=self.buffer.getvalue();gzip.decompress(raw);atomic_bytes(self.path,raw)
def atomic_npz(path,**arrays):
    import numpy as np
    stream=io.BytesIO();np.savez_compressed(stream,**arrays);raw=stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:raise ValueError('INVALID_IN_MEMORY_SCENARIO_ARCHIVE')
    atomic_bytes(path,raw)
