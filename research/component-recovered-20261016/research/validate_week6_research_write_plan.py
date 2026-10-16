"""Restrict scheduled writes to new research namespaces; never model locks."""
import argparse
from pathlib import PurePosixPath
import subprocess

PREFIXES=('data/research/prospective/waiver-expanded/history/','data/research/prospective/waiver-expanded/forecasts/','data/research/prospective/waiver-expanded/outcomes/','data/research/prospective/weekly-sources/','data/research/prospective/waiver-v2/history/',
          'data/research/prospective/waiver-v2/forecasts/','data/research/prospective/waiver-v2/outcomes/',
          'data/research/prospective/weekly-preparation/','data/research/prospective/report-preparation/',
          'data/research/prospective/football-context/','data/research/prospective/league-evidence/',
          'data/research/prospective/specialist-strategies/','data/research/prospective/auction-history/',
          'data/research/prospective/weekly-research-view/','data/research/prospective/m10/outcomes/')


def validate(ref,paths):
    if ref!='refs/heads/main':raise ValueError('WEEK6_RESEARCH_MAIN_ONLY')
    for raw in paths:
        path=PurePosixPath(raw)
        if path.is_absolute() or '..' in path.parts or '\\' in raw or not raw.startswith(PREFIXES):
            raise ValueError('WEEK6_RESEARCH_WRITE_OUTSIDE_OWNER: '+raw)
        if path.suffix not in {'.json','.gz','.md'}:
            raise ValueError('WEEK6_RESEARCH_UNSUPPORTED_ARTIFACT')


def main():
    p=argparse.ArgumentParser();p.add_argument('--ref',required=True);p.add_argument('--base');a=p.parse_args()
    command=['git','diff','--name-only',a.base+'...HEAD'] if a.base else ['git','diff','--cached','--name-only']
    validate(a.ref,subprocess.check_output(command,text=True).splitlines())
    print('PASS Week 6 main-only research write plan')


if __name__=='__main__':main()
