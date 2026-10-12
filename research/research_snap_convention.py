"""Pinned provider convention, separate from exact dataset-build provenance."""
import hashlib
import json
from pathlib import Path

from weekly_evidence_audit import stamp

CONTRACT_SHA256 = 'b2c0622633bef5f46e488b171b52d3ceeb13084905cbf0e2fc0009917d0cfadc'
CONTRACT_DIR = Path(__file__).resolve().parents[1] / 'config/source-contracts/nflverse-snaps-v1'


def load(cutoff, directory=CONTRACT_DIR):
    raw = (directory / 'contract.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != CONTRACT_SHA256:
        raise ValueError('SNAP_CONVENTION_CONTRACT_CHANGED')
    contract = json.loads(raw)
    if stamp(contract['observed_at']) > stamp(cutoff):
        raise ValueError('SNAP_CONVENTION_NOT_OBSERVED_AT_CUTOFF')
    for evidence in contract['evidence']:
        source = (directory / evidence['file']).read_bytes()
        if hashlib.sha256(source).hexdigest() != evidence['sha256']:
            raise ValueError('SNAP_CONVENTION_SOURCE_CHANGED')
    return {**contract, 'contract_sha256': CONTRACT_SHA256,
            'dataset_build_revision_verified': False}


def annotate(rows, contract):
    output = []
    for row in rows:
        values = {}
        for field in contract['fields']:
            value = row.get(field + '_provider_units')
            if value is not None and not 0 <= value <= 1:
                raise ValueError('SNAP_PROVIDER_CONVENTION_RANGE_MISMATCH')
            # No inference from snap counts, denominators or the observed range.
            values[field.replace('_pct', '_snap_share') + '_provider_convention'] = value
        output.append({**row, **values,
                       'provider_percentage_convention': contract['percentage_scale'],
                       'dataset_build_revision_verified': False})
    return output
