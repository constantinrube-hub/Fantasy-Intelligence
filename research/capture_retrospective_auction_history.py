"""Newly observed exposed auctions; never original bids or adoption evidence."""
from collections import Counter
import json
from datetime import datetime,timezone
from prospective_research_io import binding,clock,encoded,gates,now,replay_response,response,write
from capture_week6_research_sources import fetch
from strict_sleeper_baseline import finite


def endpoint(league,round):
    if not str(league).isdigit() or isinstance(round,bool) or not 1<=round<=18:raise ValueError('AUCTION_TARGET_INVALID')
    return f'https://api.sleeper.app/v1/league/{league}/transactions/{round}'


def validate_receipt(root,item,season,league,round,cutoff):
    if (item.get('season'),item.get('league_id'),item.get('round'))!=(season,str(league),round) or item.get('endpoint')!=endpoint(league,round):
        raise ValueError('AUCTION_RECEIPT_TARGET_DRIFT')
    payload=json.loads(replay_response(root,item,cutoff))
    if not isinstance(payload,list):raise ValueError('AUCTION_RESPONSE_NOT_LIST')
    return payload


def summarize(observations,cutoff):
    counts=Counter();unique={};conflicts=[]
    for item,rows in observations:
        for row in rows:
            if not isinstance(row,dict) or not row.get('transaction_id'):
                counts['INVALID_TRANSACTION_ID']+=1;continue
            key=(item['league_id'],str(row['transaction_id']))
            if key in unique:
                if encoded(unique[key]['raw_transaction'])!=encoded(row):conflicts.append({'league_id':key[0],'transaction_id':key[1],'status':'CONFLICTING_RETROSPECTIVE_PAYLOAD'})
                continue
            price=finite((row.get('settings') or {}).get('waiver_bid'))
            timestamp=finite(row.get('status_updated'))
            invalid=False
            try:
                event_clock=datetime.fromtimestamp(timestamp/1000,timezone.utc).isoformat() if timestamp is not None else None
                invalid=event_clock is not None and clock(event_clock)>clock(cutoff)
            except (ValueError,OverflowError,OSError):event_clock=None;invalid=True
            if invalid:kind='INVALID_FUTURE_OR_MALFORMED_EVENT_TIME'
            elif row.get('type')!='waiver':kind='NONAUCTION'
            elif row.get('status')=='complete' and price is not None and price>=0:kind='COMPLETED_PRICED_WAIVER'
            else:kind='EXPOSED_UNPRICED_OR_NONCOMPLETED_WAIVER'
            counts[kind]+=1
            unique[key]={'league_id':key[0],'transaction_id':key[1],'round':item['round'],
                         'observed_at':item['observed_at'],'source_event_time':event_clock,
                         'classification':kind,'exposed_bid':price if price is not None and price>=0 else None,
                         'raw_transaction':row,'adoption':'UNKNOWN','rival_maximum':None,
                         'acquisition_probability':None,'optimal_bid':None,
                         'original_auction_receipt':False,'complete_failed_bids':False}
    return {'observations':[unique[key] for key in sorted(unique)],'counts':dict(sorted(counts.items())),
            'conflicts':conflicts,'unique_league_transaction_count':len(unique)}


def capture(root,season,target_week,league_ids,fetcher=fetch):
    if season<2026 or not 2<=target_week<=18:raise ValueError('AUCTION_TARGET_INVALID')
    start=now();stamp=clock(start).strftime('%Y%m%dT%H%M%S%fZ')
    base=root/f'data/research/prospective/auction-history/{season}/target_week_{target_week:02d}'
    folder=base/stamp
    # Reserve a fresh namespace even when the platform clock repeats.
    suffix=0
    while True:
        try:
            folder.mkdir(parents=True,exist_ok=False)
            break
        except FileExistsError:
            suffix+=1
            folder=base/f'{stamp}-{suffix:04d}'
    responses=[];observations=[];failures=[];reused=0
    for league in sorted(league_ids):
        for round in range(1,target_week):
            old=[]
            for p in sorted(base.glob(f'*/{league}-round_{round:02d}-receipt.json')):
                try:
                    item=json.loads(p.read_text());rows=validate_receipt(root,item,season,league,round,start)
                    old.append((item,rows))
                except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError):continue
            if old:
                item,rows=old[-1];responses.append(item);observations.append((item,rows));reused+=1;continue
            try:
                raw,observed=fetcher(endpoint(league,round))
                import hashlib
                blob=base/'raw'/hashlib.sha256(raw).hexdigest()
                item={**response(root,blob,f'{league}-round_{round:02d}',endpoint(league,round),raw,observed,'json'),
                      'season':season,'league_id':str(league),'round':round,'retrospective':True}
                rows=validate_receipt(root,item,season,league,round,now())
                write(folder/f'{league}-round_{round:02d}-receipt.json',item)
                responses.append(item);observations.append((item,rows))
            except Exception as error:
                import requests
                if not isinstance(error,(requests.RequestException,ValueError,KeyError,TypeError,OSError)):raise
                failures.append({'league_id':str(league),'round':round,'reason':type(error).__name__+':'+str(error)[:250]})
    cutoff=now();summary=summarize(observations,cutoff)
    value={'schema':'fie-retrospective-auction-history-v1','season':season,'target_week':target_week,
           'started_at':start,'captured_at':cutoff,'responses':responses,'failures':failures,
           'requested_responses':len(league_ids)*(target_week-1),'archived_responses':len(responses),'reused_responses':reused,
           'status':'EXPOSED_PAYLOAD_ARCHIVED' if not failures else 'PARTIAL_EXPOSED_ARCHIVE',**summary,
           'interpretation':'Observed now; not original auctions, complete rival bids, probabilities, or FIE adoption.',
           **gates(['BLOCKED_COMPLETE_COMPETING_BID_EVIDENCE','BLOCKED_CALIBRATED_SURVIVAL_AND_RESERVE_VALUE'])}
    path=folder/'auction-history.json';write(path,value)
    return {'path':str(path),'archived_responses':len(responses),'requested_responses':value['requested_responses'],
            'unique_observations':summary['unique_league_transaction_count'],'reused_responses':reused,'failures':len(failures)}
