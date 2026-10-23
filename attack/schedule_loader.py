import ast,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def scenarios():
    return json.loads((ROOT/'data/verified_scenarios/cases.json').read_text())

def parse_rep_txt(path):
    records=[]
    for line in Path(path).read_text().splitlines()[1:]:
        if not line.strip():continue
        match=re.match(r'\s*(\d+)\s*,\s*([^,]+),\s*(\[[^\]]*\])',line)
        if not match: raise ValueError('Malformed REP row: '+line)
        L=int(match[1]);seq=ast.literal_eval(match[3])
        if len(seq)!=L or any(z not in (0,1) for z in seq):raise ValueError('Invalid REP schedule')
        records.append(dict(length=L,ell=L-2,objective=float(match[2]),schedule=seq,interior=seq[1:-1]))
    return records
