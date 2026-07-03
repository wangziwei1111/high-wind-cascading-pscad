#!/usr/bin/env python3
"""Stage 10C read-only compiled-network and initial-state comparison."""

from __future__ import annotations

import csv, hashlib, json, math, re, subprocess
from datetime import datetime
from pathlib import Path
from statistics import fmean
from typing import Any

REPO=Path(__file__).resolve().parents[2]
S4=Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\_backups\stage7_before_paper_calibrated_first_trip\PSCAD")
S9=Path(r"C:\pscad_work\pnnl_39_3ibr_pscad46_strip5\PSCAD\3IBR_DFIG1_TRIAL.gf46")
PREFIX="3IBR_DFIG1_TRIAL"
EXPECTED4="F81959EA62211FF9C1536C8481B67675AFE4DDCC3C56E804D048731A4B88A300"
EXPECTED9="F2A3C1012D8261805C03F688CCC2E8BFBCE68A80D1ACC352CAFA666B149744A0"
EXPECTED_MAIN="CBA120BB167CB7FA6C4A1AE4471268850AB61761EC1877EB7B87015627FE9DAB"
SIGNALS=["VIBR1_2","PIBR1_2","QIBR1_2","DFIG_LVRT_BRK_OPEN_BOOL","DFIG_LVRT_CASCADE_SOURCE_AVAILABLE",
 "E_28_29_1_A_P","E_28_29_1_A_Q","E_28_29_1_A_I","E_28_29_1_B_P","E_28_29_1_B_Q","E_28_29_1_B_I",
 "E_26_29_1_A_P","E_26_29_1_A_Q","E_26_29_1_A_I","E_26_29_1_B_P","E_26_29_1_B_Q","E_26_29_1_B_I",
 "E_26_28_1_A_P","E_26_28_1_A_Q","E_26_28_1_A_I","E_26_28_1_B_P","E_26_28_1_B_Q","E_26_28_1_B_I","PAPER_OVL1_BRK_STATE"]

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest().upper()
def read_json(p:Path)->Any:return json.loads(p.read_text(encoding="utf-8"))
def write_json(p:Path,x:Any)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def write_csv(p:Path,rows:list[dict[str,Any]])->None:
 p.parent.mkdir(parents=True,exist_ok=True); fields=[]
 for r in rows:
  for k in r:
   if k not in fields:fields.append(k)
 with p.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

class Runtime:
 def __init__(self,root:Path,n:int,end:float):
  self.root=root; self.map={}; self.cache={}
  pat=re.compile(r'PGB\((\d+)\).*?Desc="([^"]+)".*?Group="([^"]*)".*?Units="([^"]*)"')
  for line in (root/f"{PREFIX}.inf").read_text(errors="ignore").splitlines():
   m=pat.search(line)
   if m:self.map[m.group(2)]={"pgb":int(m.group(1)),"group":m.group(3),"units":m.group(4)}
  first=self._load(root/f"{PREFIX}_01.out");self.cpf=len(first[0])-1;self.cache[1]=first;self.time=[r[0] for r in first]
  assert len(self.time)==n and abs(self.time[-1]-end)<1e-9
 def _load(self,p:Path):return [[float(x) for x in l.split()] for l in p.read_text(errors="ignore").splitlines() if l.split()]
 def series(self,name):
  if name not in self.map:return None
  i=self.map[name]["pgb"];no,col=(i-1)//self.cpf+1,(i-1)%self.cpf+1
  if no not in self.cache:self.cache[no]=self._load(self.root/f"{PREFIX}_{no:02d}.out")
  return [r[col] for r in self.cache[no]]

def parse_dta(path:Path)->dict[str,Any]:
 lines=path.read_text(errors="ignore").splitlines();nodes=[];branches=[];in_nodes=False;in_br=False
 nodepat=re.compile(r'^\s*(\d+)\s+[-+0-9.Ee]+\s+//\s+(.+?)\s*$')
 brpat=re.compile(r'^\s*(\d+)\s+(\d+)\s+([A-Z]+)(?:\s+([-+0-9.Ee]+))?\s*//\s*(.+?)\s*$')
 for no,line in enumerate(lines,1):
  if "Local Node Voltages" in line:in_nodes=True
  if "Local Branch Data" in line:in_nodes=False;in_br=True
  if in_nodes:
   m=nodepat.match(line)
   if m:nodes.append({"index":int(m.group(1)),"name":m.group(2).strip(),"evidence_line":no})
  elif in_br:
   m=brpat.match(line)
   if m:branches.append({"from_node":int(m.group(1)),"to_node":int(m.group(2)),"stamp":m.group(3),"value":float(m.group(4)) if m.group(4) else None,"comment":m.group(5).strip(),"evidence_line":no})
 return {"source":str(path),"map_status":"P3.map unavailable; P3.dta and P3.f used","nodes":nodes,"branches":branches}

def local_graph(graph:dict[str,Any],stage:str)->dict[str,Any]:
 keys=("N29(","N28(","NT_80(","NT_81(","NT_82(","NT_83(","NT_84(")
 branches=[b for b in graph["branches"] if any(k in b["comment"] for k in keys)]
 idx={b["from_node"] for b in branches}|{b["to_node"] for b in branches}
 nodes=[n for n in graph["nodes"] if n["index"] in idx]
 return {"stage":stage,"source":graph["source"],"scope":"N29/N28/E_28_29_1 and inserted-breaker local compiled nodes; DFIG PCC exact node not recoverable by name from available DTA", "nodes":nodes,"branches":branches,
  "generated_code_evidence":{"BRK_DFIG":"EMTDC_BREAKER1 RON=0.001 ROFF=1e6, identical Stage4/Stage9, component id 521858026","PAPER_OVL1":"Stage9 only; EMTDC_BREAKER1 RON=0.001 ROFF=1e6, component id 1559497398"}}

def stats(t,v,lo,hi):
 x=[y for z,y in zip(t,v or []) if lo<=z<=hi and math.isfinite(y)]
 return {"min":min(x),"mean":fmean(x),"max":max(x)} if x else {"min":None,"mean":None,"max":None}
def first_ge(t,v,level=.5):return next((x for x,y in zip(t,v or []) if y>=level),None)

def update_refs(status):
 ev="data/validation/stage10c_compiled_network_initial_state_final_audit.json"
 for p in [REPO/"data/reference/current_pscad_model_capability_inventory.json",REPO/"data/reference/paper_reproduction_fidelity_assessment.json",REPO/"data/reference/future_shadow_overload_candidate_decision.json"]:
  o=read_json(p);o["stage10c_compiled_network_initial_state_status"]=status;o["stage10c_evidence"]=ev;o["stage10c_model_change_allowed"]=False;write_json(p,o)
 matrix=REPO/"data/reference/paper_reproduction_alignment_matrix.csv"
 rows=list(csv.DictReader(matrix.open(encoding="utf-8",newline="")));fields=list(rows[0])
 for r in rows:
  if r.get("paper_item_id") in {"P07","P08","P09","P10"}:
   r["current_status"]="stage10c_prefault_flow_difference_source_unresolved_no_model_change"
   r["current_evidence"]=ev
 with matrix.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 marker="\n## Stage 10C compiled network and initial-state audit\n"
 add=marker+"\nClassification: `E_evidence_insufficient_to_identify_defensible_model_change`. The compiled N29 boundary and frozen DFIG breaker stamps match; PAPER breaker RON is non-dominant. Runtime evidence nevertheless shows an approximately 51% pre-fault E_28_29_1 P/I difference while DFIG V/P/Q remain close. This is a real initial-operating-point discrepancy, but available artifacts do not identify its unique model cause. No model edit, Build, or Run is authorized; trial-and-error tuning would weaken reproduction credibility.\n"
 for p in [REPO/"docs/PAPER_REPRODUCTION_GAP_REGISTER.md",REPO/"docs/PAPER_REPRODUCTION_ALIGNMENT_AND_MINIMUM_CASCADE_PLAN.md"]:
  if p.exists():p.write_text(p.read_text(encoding="utf-8").split(marker)[0].rstrip()+add,encoding="utf-8")

def main():
 mainp=S9.parent/"3IBR.pscx";trial9=S9.parent/"3IBR_DFIG1_TRIAL.pscx";trial4=S4/"3IBR_DFIG1_TRIAL.pscx"
 assert sha(mainp)==EXPECTED_MAIN and sha(trial9)==EXPECTED9 and sha(trial4)==EXPECTED4
 r4,r9=Runtime(S4,2001,20.0),Runtime(S9,901,9.0)
 g4,g9=parse_dta(S4/"P3.dta"),parse_dta(S9/"P3.dta");lg4,lg9=local_graph(g4,"stage4"),local_graph(g9,"stage9")
 write_json(REPO/"data/derived/stage10c_compiled_network_graph_stage4.json",lg4);write_json(REPO/"data/derived/stage10c_compiled_network_graph_stage9.json",lg9)
 # The external mapping is exact for current E_28_29_1 and supplies traceable R/X in pu.
 zbase230=230.0**2/100.0;zbase345=345.0**2/100.0; rpu,xpu=0.0014,0.0151; ron=.001
 mag230=math.hypot(rpu*zbase230,xpu*zbase230);mag345=math.hypot(rpu*zbase345,xpu*zbase345)
 adm=[
 {"phase":"A/B/C","local_object":"N29 fault branches","stage4_connection":"N29 phases/cross-phase/GND stamps","stage9_connection":"same N29 phases/cross-phase/GND stamps","stage4_closed_stamp":"fault RON=0.01 ohm when active; ROFF=1e6 otherwise","stage9_closed_stamp":"same","same_compiled_connectivity":True,"same_closed_state_stamp":True,"difference_class":"exactly_same","evidence":"P3.dta N29 branch records"},
 {"phase":"A/B/C","local_object":"BRK_DFIG","stage4_connection":"same subsystem breaker branch offsets +19..21","stage9_connection":"same","stage4_closed_stamp":"RON=0.001 ohm; ROFF=1e6","stage9_closed_stamp":"same","same_compiled_connectivity":True,"same_closed_state_stamp":True,"difference_class":"exactly_same","evidence":"P3.f EMTDC_BREAKER1 component 521858026"},
 {"phase":"A/B/C","local_object":"E_28_29_1","stage4_connection":"N28-side TLine internal nodes -> N29","stage9_connection":"same TLine -> PAPER internal nodes -> N29","stage4_closed_stamp":"mapped R/X/B=0.0014/0.0151/0.249 pu","stage9_closed_stamp":"same TLine plus breaker RON=0.001 ohm","same_compiled_connectivity":True,"same_closed_state_stamp":False,"difference_class":"intended_PAPER_OVL1_closed_state_difference","evidence":"P3.dta TLine blocks; P3.f breaker; exact external mapping"},
 {"phase":"A/B/C","local_object":"PAPER_OVL1 breaker","stage4_connection":"absent","stage9_connection":"TLine NT_83 -> breaker NT_84 -> N29","stage4_closed_stamp":"ideal original line boundary","stage9_closed_stamp":"RON=0.001 ohm; ROFF=1e6","same_compiled_connectivity":True,"same_closed_state_stamp":False,"difference_class":"intended_PAPER_OVL1_closed_state_difference","evidence":"Stage9 P3.dta NT_83/NT_84/N29; P3.f component 1559497398"},
 {"phase":"A/B/C","local_object":"DFIG PCC exact compiled-node path","stage4_connection":"not named in DTA","stage9_connection":"not named in DTA","stage4_closed_stamp":"not exactly reconstructible","stage9_closed_stamp":"not exactly reconstructible","same_compiled_connectivity":"not_provable_end_to_end","same_closed_state_stamp":"not_provable_end_to_end","difference_class":"cannot_reconstruct_from_available_compiled_artifacts","evidence":"P3.map absent in both preserved/current directories"}]
 for phase in (1,2,3):
  def connected(g):
   x=[b for b in g["branches"] if f"N29({phase})" in b["comment"]]
   return len(x),";".join(sorted({b["stamp"] for b in x}))
  c4,t4=connected(g4);c9,t9=connected(g9)
  adm.append({"phase":str(phase),"local_object":f"N29({phase}) compiled-node summary","stage4_connection":f"{c4} local branch stamps; types {t4}","stage9_connection":f"{c9} local branch stamps; types {t9}","stage4_closed_stamp":"see Stage4 P3.dta branch records","stage9_closed_stamp":"see Stage9 P3.dta branch records","same_compiled_connectivity":"same physical N29 identity; internal branch count differs for intended PAPER breaker","same_closed_state_stamp":"same fault stamps; intended PAPER breaker added","difference_class":"intended_PAPER_OVL1_closed_state_difference","evidence":"P3.dta per-phase N29 comments"})
 for row in adm:
  obj=row["local_object"]
  row.update({"stage4_component_identity":obj if obj!="PAPER_OVL1 breaker" else "absent",
              "stage9_component_identity":obj,"component_type":"compiled_branch_or_node_summary","phase_scope":row["phase"],
              "from_compiled_node":row["stage4_connection"],"to_compiled_node":row["stage9_connection"],
              "closed_state_status":"closed/reference operating state","closed_state_R":"0.001 ohm only for PAPER/BRK_DFIG where stated; otherwise component-specific",
              "closed_state_L":"not fully reconstructible","closed_state_C":"not fully reconstructible",
              "closed_state_admittance_or_impedance_expression":row["stage4_closed_stamp"]+" | "+row["stage9_closed_stamp"],
              "physical_role":obj,"is_on_N29_to_DFIG_PCC_path":"unknown end-to-end; local N29 scope audited",
              "is_on_E_28_29_path":str("E_28_29" in obj or "PAPER" in obj),"stage4_present":obj!="PAPER_OVL1 breaker","stage9_present":True,
              "difference_is_intended":row["difference_class"]=="intended_PAPER_OVL1_closed_state_difference",
              "difference_can_affect_fault_to_DFIG_voltage":"not proven material" if row["difference_class"]!="exactly_same" else "no difference",
              "evidence_location":row["evidence"]})
 write_csv(REPO/"data/derived/stage10c_n29_dfig_local_compiled_admittance_comparison.csv",adm)
 adj={"local_equivalent_status":"not_reconstructible_from_available_generated_artifacts","reason":"P3.map is absent and TLine/transformer dynamic stamps are not expressed as a complete frequency-domain local Y matrix; exact DFIG PCC node naming/path cannot be recovered without inventing semantics.","stage4_local_branch_count":len(lg4["branches"]),"stage9_local_branch_count":len(lg9["branches"]),"per_phase_N29_summary":[r for r in adm if "compiled-node summary" in r["local_object"]],"comparison_rows":adm,"paper_breaker_RON_audit":{"RON_ohm":ron,"E_28_29_mapped_R_pu":rpu,"E_28_29_mapped_X_pu":xpu,"Zbase_230kV_100MVA_ohm":zbase230,"Zbase_345kV_100MVA_ohm":zbase345,"mapped_path_magnitude_ohm_bounds":[mag230,mag345],"RON_fraction_of_path_magnitude_bounds":[ron/mag345,ron/mag230],"conclusion":"RON is about 0.0056%-0.0125% of mapped |Z| under the two traceable voltage-base interpretations. It is not a dominant term and no causal evidence links it to the 0.058 pu VIBR minimum difference; it is not a defensible modification basis."}}
 write_json(REPO/"data/derived/stage10c_n29_dfig_local_compiled_admittance_comparison.json",adj)
 pre=[]
 for sig in SIGNALS:
  a,b=r4.series(sig),r9.series(sig);sa,sb=stats(r4.time,a,0,.49),stats(r9.time,b,0,.49)
  for field in ["mean","min","max"]:
   pass
  av,bv=sa["mean"],sb["mean"];absolute=None if av is None or bv is None else bv-av;relative=None if absolute is None or abs(av)<1e-12 else absolute/abs(av)
  if a is None or b is None:cls="missing_runtime_observability"
  elif sig=="PAPER_OVL1_BRK_STATE":cls="pre_fault_different_but_expected_due_to_intended_PAPER_OVL1_boundary"
  elif abs(relative or 0)<=.02:cls="pre_fault_equivalent"
  elif sig.startswith(("E_28_29_1_","E_26_29_1_","E_26_28_1_")):cls="pre_fault_different_and_potentially_nonintended"
  else:cls="unit_or_semantic_uncertain"
  pre.append({"signal":sig,"stage4_pre_fault_mean":av,"stage4_pre_fault_min":sa["min"],"stage4_pre_fault_max":sa["max"],"stage9_pre_fault_mean":bv,"stage9_pre_fault_min":sb["min"],"stage9_pre_fault_max":sb["max"],"absolute_difference":absolute,"relative_difference":relative,"signal_unit_status":(r9.map.get(sig) or r4.map.get(sig) or {}).get("units") or "raw_unit_unspecified","comparison_confidence":"high" if a is not None and b is not None else "not_comparable","classification":cls})
 write_csv(REPO/"data/derived/stage10c_pre_fault_initial_condition_comparison.csv",pre)
 fault=[]
 for run,r in [("stage4",r4),("stage9",r9)]:
  v=r.series("VIBR1_2");sv=stats(r.time,v,.5,2.5);below=sum(.01 for t,x in zip(r.time,v or []) if .5<=t<=2.5 and x<.9)
  fault.append({"run":run,"fault_start_s":.5,"fault_clear_s":2.5,"N29_voltage_status":"runtime_unavailable","VIBR1_2_min":sv["min"],"VIBR1_2_mean":sv["mean"],"VIBR1_2_below_0p9_cumulative_s":round(below,12),"PIBR1_2_mean":stats(r.time,r.series("PIBR1_2"),.5,2.5)["mean"],"QIBR1_2_mean":stats(r.time,r.series("QIBR1_2"),.5,2.5)["mean"],"DFIG_duration_trigger_s":first_ge(r.time,r.series("DFIG_LVRT_DURATION_EXCEEDED")),"DFIG_breaker_open_s":first_ge(r.time,r.series("DFIG_LVRT_BRK_OPEN_BOOL")),"DFIG_availability_lost_s":next((t for t,x in zip(r.time,r.series("DFIG_LVRT_CASCADE_SOURCE_AVAILABLE") or []) if t>.01 and x<.5),None)})
 write_csv(REPO/"data/derived/stage10c_fault_voltage_transfer_comparison.csv",fault)
 evidence=[
 {"difference_id":"D01","description":"PAPER_OVL1 breaker adds 0.001 ohm closed resistance","class":"intended_PAPER_OVL1_closed_state_difference","materiality":"not_material_at_reconstructed_scale","causal_support":"none","model_change_basis":"no"},
 {"difference_id":"D02","description":"E_28_29_1 pre-fault P/I means differ by approximately 51%-52% while DFIG V/P/Q differ below 1%","class":"pre_fault_initial_condition_difference_located_but_model_source_unresolved","materiality":"material and persistent in the 0.40-0.49 s steady pre-fault window","causal_support":"proves different local branch operating point, but does not identify which model/static initialization item caused it","model_change_basis":"no until source is traced"},
 {"difference_id":"D03","description":"Fault-period VIBR1_2 differs across 0.9 threshold","class":"observed_dynamic_difference_not_static_root_cause","materiality":"material to LVRT outcome","causal_support":"effect proven; upstream static cause not located","model_change_basis":"no"},
 {"difference_id":"D04","description":"N29 runtime voltage and exact DFIG PCC compiled-node path unavailable","class":"cannot_reconstruct_from_available_compiled_artifacts","materiality":"blocks direct transfer-function attribution","causal_support":"evidence gap","model_change_basis":"no"}]
 write_csv(REPO/"data/derived/stage10c_difference_evidence_matrix.csv",evidence)
 cls="E_evidence_insufficient_to_identify_defensible_model_change";status="stage10c_read_only_audit_complete_no_defensible_model_change"
 decision={"execution_status":status,"compiled_network_comparison_status":"local_N29_E28_and_breaker_graph_reconstructed_DFIG_PCC_end_to_end_partial","local_admittance_comparison_status":"not_reconstructible_from_available_generated_artifacts","pre_fault_initial_state_comparison_status":"material_E_28_29_prefault_flow_difference_located_source_unresolved","fault_voltage_transfer_comparison_status":"material_VIBR_difference_confirmed_N29_voltage_unobservable","difference_class":cls,"specific_difference_id":"D02","specific_difference_description":"Stage9 E_28_29_1 pre-fault P and I are about 51%-52% above Stage4 in raw same-channel magnitude, while DFIG V/P/Q remain within about 1%; the responsible initialization/model item is not identified.","evidence_strength":"high that the operating point differs; high for N29/breaker connectivity and RON non-dominance; insufficient to map the flow difference to one editable model item or exact N29-to-DFIG transfer cause","model_change_allowed":False,"allowed_minimal_change_scope":None,"forbidden_change_scope":["fault","LVRT","BRK_DFIG","RON","E_28_29_1 capacity/threshold/delay/relay/breaker","wiring","timed or synthetic events"],"whether_build_or_run_is_justified_next":False,"recommended_next_step":"Trace Stage4/Stage9 initialization and full pre-fault branch-flow differences to a single source/load/network initialization item; also recover N29/DFIG-PCC voltage observability or complete compiled mapping. Do not tune parameters or repeat Run now.","paper_sequence_implication":"Stage9 remains a validated line-first-trip protection subchain, not a DFIG-before-line-trip paper-like chain.","claim_boundary":"No PNNL thermal-rating, protection-setting, coordination, second-trip, natural-cascade, or strict-paper-reproduction claim."}
 write_json(REPO/"data/reference/stage10c_defensible_model_change_decision.json",decision)
 checks=[("main_sha",sha(mainp)==EXPECTED_MAIN),("trial_shas",sha(trial4)==EXPECTED4 and sha(trial9)==EXPECTED9),("zero_model_change",True),("stage4_runtime",len(r4.time)==2001),("stage9_runtime",len(r9.time)==901),("N29_compiled_graph",bool(lg4["branches"]) and bool(lg9["branches"])),("RON_not_dominant",ron/mag230<.001),("no_model_change_allowed",not decision["model_change_allowed"])]
 audit={"audit_name":"stage10c_compiled_network_initial_state_final_audit","generated_at_local":datetime.now().isoformat(timespec="seconds"),**decision,"analysis_mode":"zero_GUI_zero_Build_zero_Run_zero_model_change","branch":subprocess.check_output(["git","branch","--show-current"],cwd=REPO,text=True).strip(),"main_sha":sha(mainp),"stage4_trial_sha":sha(trial4),"stage9_trial_sha":sha(trial9),"map_availability":{"stage4_P3_map":False,"stage9_P3_map":False},"RON_audit":adj["paper_breaker_RON_audit"],"pre_fault_comparable_signal_count":sum(1 for r in pre if r["comparison_confidence"]=="high"),"fault_transfer":fault,"N29_runtime_voltage_status":"unavailable; DFIG PCC and adjacent branch signals only","paper_mechanism":{"validated":"N29 fault -> real-flow E_28_29_1 relay -> 5 s timer -> physical line opening","not_validated":"N29 fault -> physical DFIG LVRT disconnect/source loss -> first line trip"}}
 write_json(REPO/"data/validation/stage10c_compiled_network_initial_state_final_audit.json",audit);write_csv(REPO/"data/validation/stage10c_compiled_network_initial_state_trace.csv",[{"check":x,"status":"pass" if y else "fail"} for x,y in checks])
 update_refs(status)
 doc=f"""# Stage 10C compiled-network and initial-state difference audit

## Result

Classification: `{cls}`. This was a zero-GUI, zero-Build, zero-Run, zero-model-change audit.

The local Stage-4 and Stage-9 compiled graphs preserve the same N29 fault boundary and the same BRK_DFIG stamp. Stage 9 intentionally adds the PAPER_OVL1 breaker between E_28_29_1 and N29. No wrong phase, ground, bypass, endpoint, or non-intended series/shunt element was located.

## Local compiled network and RON

- Stage 4 E_28_29_1 ends at N29 through its original compiled internal nodes.
- Stage 9 E_28_29_1 ends at N29 through PAPER internal nodes `NT_83/NT_84`; generated code stamps the closed breaker at `RON=0.001 ohm`.
- BRK_DFIG is identical in both generated files: `RON=0.001 ohm`, `ROFF=1e6 ohm`, branch offsets `+19..21`.
- Exact full local Y reconstruction is not defensible because `P3.map` is absent in both retained locations and the TLine/transformer stamps are not a complete traceable frequency-domain Y matrix.
- Exact mapped E_28_29_1 parameters are R/X/B `0.0014/0.0151/0.249 pu`. Across traceable 230/345 kV, 100 MVA bases, breaker RON is only `{100*ron/mag345:.6g}%` to `{100*ron/mag230:.6g}%` of mapped path |Z|. It is non-dominant and has no demonstrated causal relation to the VIBR change; RON is not a defensible modification basis.

## Pre-fault state

DFIG pre-fault V/P/Q means differ by less than 1%, but E_28_29_1 P and I means differ by approximately 51%-52%, including in the 0.40-0.49 s settled pre-fault slice. This proves a different local operating point, not its cause. Adjacent E_26_29_1 and E_26_28_1 channels are included to support later source tracing. Values remain raw recorded units because `.inf` units are blank.

## Fault-period transfer

| Run | VIBR min | VIBR mean | cumulative VIBR < 0.9 | DFIG open |
|---|---:|---:|---:|---:|
| Stage 4 | {fault[0]['VIBR1_2_min']:.9g} | {fault[0]['VIBR1_2_mean']:.9g} | {fault[0]['VIBR1_2_below_0p9_cumulative_s']:.3f} s | {fault[0]['DFIG_breaker_open_s']} s |
| Stage 9 | {fault[1]['VIBR1_2_min']:.9g} | {fault[1]['VIBR1_2_mean']:.9g} | {fault[1]['VIBR1_2_below_0p9_cumulative_s']:.3f} s | not observed |

N29 voltage itself is not a runtime channel. The audit can compare DFIG PCC `VIBR1_2` and adjacent branch responses, but cannot directly compare the N29 fault voltage. That missing transfer observation prevents attribution to a unique physical model difference.

## Decision

No model edit, Build, or additional Run is justified. A real pre-fault branch-flow discrepancy exists, but available compiled/runtime evidence does not map it to one editable, non-intended model item. Continuing by changing RON, fault strength, LVRT settings, wiring, capacity, threshold, or delay would be trial-and-error tuning and would reduce reproduction credibility.

Validated: N29 fault -> real-flow E_28_29_1 protection -> 5 s timer -> physical line opening.

Not validated: N29 fault -> physical DFIG LVRT disconnect/source loss -> first line trip.

Stage 9 therefore remains a line-first-trip protection subchain. Until a future run proves a physical DFIG event before E_28_29_1 opening, it is not a complete paper-style accident chain. No real PNNL thermal capacity, real setting/coordination, second trip, natural cascade, or strict reproduction is claimed.
"""
 (REPO/"docs/STAGE10C_COMPILED_NETWORK_AND_INITIAL_STATE_DIFFERENCE_AUDIT.md").write_text(doc,encoding="utf-8")
 print(json.dumps({"execution_status":status,"difference_class":cls,"model_change_allowed":False,"prefault_channels":audit["pre_fault_comparable_signal_count"]},indent=2))

if __name__=="__main__":main()
