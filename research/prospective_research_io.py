"""Exact first-write research artifacts; no production authority."""
from __future__ import annotations
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path


def clock(value):
    parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('RESEARCH_TIMEZONE_REQUIRED')
    return parsed.astimezone(timezone.utc)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def write(path, value):
    path = Path(path)
    data = encoded(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('RESEARCH_DIVERGENT_FIRST_WRITE')
        return
    with path.open('xb') as stream:
        stream.write(data)


def binding(root, path, observed_at):
    path = Path(path).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('RESEARCH_PATH_OUTSIDE_ROOT')
    return {'path': path.relative_to(Path(root).resolve()).as_posix(),
            'sha256': sha(path), 'observed_at': clock(observed_at).isoformat()}


def verified(root, item, cutoff):
    relative = Path(item['path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('RESEARCH_UNSAFE_PATH')
    path = (Path(root)/relative).resolve()
    if not path.is_relative_to(Path(root).resolve()) or not path.is_file():
        raise ValueError('RESEARCH_BINDING_MISSING')
    if sha(path) != item['sha256'] or clock(item['observed_at']) > clock(cutoff):
        raise ValueError('RESEARCH_HASH_OR_CUTOFF_DRIFT')
    return path


def response(root, folder, name, url, raw, observed_at, kind):
    """Retain exact response bytes compressed, not parsed/reserialized bytes."""
    import re
    if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
        raise ValueError('RESEARCH_RESPONSE_NAME_INVALID')
    path = Path(folder)/(name + '.' + kind + '.gz')
    path.parent.mkdir(parents=True, exist_ok=True)
    compressed = gzip.compress(raw, mtime=0)
    if path.exists():
        if gzip.decompress(path.read_bytes()) != raw:
            raise ValueError('RESEARCH_RESPONSE_COLLISION')
    else:
        with path.open('xb') as f:
            f.write(compressed)
    return {**binding(root, path, observed_at), 'endpoint': url, 'kind': kind,
            'raw_sha256': hashlib.sha256(raw).hexdigest(), 'raw_size': len(raw)}


def replay_response(root, item, cutoff):
    raw = gzip.decompress(verified(root, item, cutoff).read_bytes())
    if hashlib.sha256(raw).hexdigest() != item['raw_sha256'] or len(raw) != item['raw_size']:
        raise ValueError('RESEARCH_RAW_RESPONSE_DRIFT')
    return raw


def gates(blockers):
    return {**{name: False for name in ('activation_eligible', 'forecast_eligible',
            'ranking_eligible', 'recommendation_eligible', 'transaction_eligible')},
            'research_only': True, 'blockers': sorted(set(blockers))}
