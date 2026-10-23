"""Load only define_system from the single bundled REP source; never run its sweep."""
import ast
from pathlib import Path
import numpy as np
SOURCE=Path(__file__).resolve().parents[1]/'vendor/REP_v1.2/main_short.py'
tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='define_system']
if len(nodes)!=1: raise RuntimeError('Expected one official define_system')
namespace={'np':np}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE),'exec'),namespace)
define_system=namespace['define_system']
