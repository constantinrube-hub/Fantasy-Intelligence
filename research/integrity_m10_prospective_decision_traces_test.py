from m10_prospective_decision_traces import trace_rows
from m10_prospective_capture_contract import MODELS
def main():
 rows=[]
 for m in MODELS:
  for i in range(3): rows.append({"model":m,"forecast_id":f"f{i}","canonical_player_id":f"p{i}","mean":10-i,"p10":5-i})
 out=trace_rows(rows,"fixture","chopped",2);assert len(out)==3 and len({tuple(x["legal_forecast_ids"]) for x in out})==1
 try: trace_rows([r for r in rows if r["model"]!="M10_HGB"],"fixture","start_sit",1)
 except AssertionError: pass
 else: raise AssertionError("unpaired legal set accepted")
 print("PASS deterministic paired research decision traces")
if __name__=="__main__": main()
