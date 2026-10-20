#!/usr/bin/env python3
"""Partition Code: project-scoped Codex agents. Python 3.11+, no dependencies."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib

SOURCE = Path(__file__).resolve().parent
BEGIN = '<!-- partition-code:begin -->'
END = '<!-- partition-code:end -->'
BLOCK = BEGIN + '\nFollow `.relay/ROUTING.md` for coding model and agent routing.\n' + END

class RelayError(Exception):
    pass

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def safe(root, rel):
    p = Path(rel)
    if p.is_absolute() or '..' in p.parts or '.git' in p.parts:
        raise RelayError('Unsafe managed path.')
    out = root
    for part in p.parts:
        out = out / part
        if out.is_symlink():
            raise RelayError('Symlinked managed paths are not supported.')
    return out

def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(raw.encode() if isinstance(raw, str) else raw)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def sources():
    return {'.relay/ROUTING.md': (SOURCE/'ROUTING.md').read_bytes(),
            '.relay/models.json': (SOURCE/'models.json').read_bytes(),
            **{'.codex/agents/'+f.name:f.read_bytes() for f in sorted((SOURCE/'agents').glob('*.toml'))}}

def load_state(root):
    p = safe(root,'.relay/state.json')
    if not p.exists(): return {'version':1,'files':{}}
    state = json.loads(p.read_text())
    if state.get('version') != 1 or not isinstance(state.get('files'),dict):
        raise RelayError('Invalid install manifest.')
    allowed = set(sources())
    for rel, entry in state['files'].items():
        if rel not in allowed or not isinstance(entry,dict) or not isinstance(entry.get('sha256'),str):
            raise RelayError('Invalid managed manifest entry.')
        if entry.get('backup'):
            if not entry['backup'].startswith('.relay/backups/'):
                raise RelayError('Invalid backup path.')
            safe(root,entry['backup'])
    return state

def install(root):
    if (root/'AGENTS.override.md').exists():
        raise RelayError('AGENTS.override.md takes precedence; integrate ROUTING.md there explicitly first.')
    state = load_state(root); planned = sources()
    # Preflight everything before creating or replacing any file.
    for rel, raw in planned.items():
        p = safe(root,rel)
        if p.exists() and p.read_bytes()!=raw:
            owned = state['files'].get(rel)
            if not owned or digest(p.read_bytes()) != owned['sha256']:
                raise RelayError('Preserving modified or unowned file: '+rel)
    agents = safe(root,'AGENTS.md'); text = agents.read_text() if agents.exists() else ''
    if BEGIN in text or END in text:
        if text.count(BEGIN)!=1 or text.count(END)!=1 or text.index(END)<text.index(BEGIN):
            raise RelayError('Repair the Partition Code markers in AGENTS.md.')
        updated = text[:text.index(BEGIN)]+BLOCK+text[text.index(END)+len(END):]
    else: updated = text.rstrip()+'\n\n'+BLOCK+'\n'
    ignore = safe(root,'.gitignore'); ignored = ignore.read_text() if ignore.exists() else ''
    for rel in ['.relay/state.json','.relay/backups/']:
        if rel not in ignored.splitlines(): ignored += '\n'+rel+'\n'
    for rel, raw in planned.items():
        p=safe(root,rel)
        if p.exists() and p.read_bytes()==raw and rel not in state['files']:
            continue  # Identical preexisting files remain user-owned.
        state['files'][rel]={'sha256':digest(raw)}
        write(p,raw)
    write(agents,updated); write(ignore,ignored)
    write(safe(root,'.relay/state.json'),json.dumps(state,indent=2)+'\n')
    return {'installed':len(planned),'project':str(root),'global_config_changed':False}

def uninstall(root):
    state=load_state(root); kept=[]
    for rel,entry in state['files'].items():
        p=safe(root,rel)
        if p.exists():
            if digest(p.read_bytes())==entry['sha256']: p.unlink()
            else: kept.append(rel)
    agents=safe(root,'AGENTS.md')
    if agents.exists():
        t=agents.read_text()
        if BLOCK in t: write(agents,t.replace(BLOCK,'').strip()+'\n')
    manifest=safe(root,'.relay/state.json')
    if manifest.exists(): manifest.unlink()
    return {'preserved_modified_files':kept}

def settings(root):
    raw=json.loads(safe(root,'.relay/models.json').read_text())
    for key in ['coordinator','deep','frontier']:
        if not isinstance(raw.get(key),dict) or not all(isinstance(raw[key].get(k),str) for k in ['model','effort']):
            raise RelayError('Invalid model policy: '+key)
    return raw

def roles(root):
    result=[]
    for rel in sources():
        if not rel.endswith('.toml'): continue
        f=safe(root,rel); d=tomllib.loads(f.read_text())
        if not re.fullmatch(r'relay_[a-z_]+',d.get('name','')) or not all(isinstance(d.get(k),str) and d[k] for k in ['description','developer_instructions','model','model_reasoning_effort']):
            raise RelayError('Invalid role: '+rel)
        if any(k in d for k in ['approval_policy','sandbox_mode','model_provider','mcp_servers']):
            raise RelayError('A role cannot override inherited session permissions or providers.')
        result.append((f,d))
    return result

def models_available():
    r=subprocess.run(['codex','debug','models'],capture_output=True,text=True,timeout=30)
    if r.returncode: raise RelayError('Could not inspect Codex models. Run codex login and check your installation.')
    return {m['slug']:{v['effort'] for v in m['supported_reasoning_levels']} for m in json.loads(r.stdout)['models']}

def validate_models(pairs):
    catalog=models_available()
    for model,effort in pairs:
        if model not in catalog or effort not in catalog[model]:
            raise RelayError(f'Unavailable model/effort in this client: {model}/{effort}. Edit .relay/models.json or the role TOML.')

def command(root,args):
    p=settings(root)[args.quality]
    argv=['codex','--ask-for-approval','on-request','--enable','multi_agent_v2']
    if args.exec: argv+=['exec','--skip-git-repo-check']
    argv+=['--cd',str(root),'--model',p['model'],'-c','model_reasoning_effort='+json.dumps(p['effort']),
           '--sandbox','read-only' if args.read_only else 'workspace-write','-c','agents.max_concurrent_threads_per_session=2']
    for f,d in roles(root):
        argv+=['-c',f'agents.{d["name"]}.description='+json.dumps(d['description']),'-c',f'agents.{d["name"]}.config_file='+json.dumps(str(f))]
    if args.search: argv+=['-c','web_search="live"']
    prompt='Follow .relay/ROUTING.md. Use the relay_* specialists only when useful and honor all repository instructions.'
    if args.read_only: prompt+=' Analysis only: do not edit or perform external mutations.'
    if args.prompt: prompt+='\n\nUser request:\n'+args.prompt
    return argv+[prompt],p

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='action',required=True)
    for name in ['install','uninstall','doctor','run']:
        a=sub.add_parser(name);a.add_argument('--project',default='.')
        if name=='doctor': a.add_argument('--check-models',action='store_true')
        if name=='run':
            a.add_argument('prompt',nargs='?');a.add_argument('--quality',choices=['coordinator','deep','frontier'],default='coordinator')
            for flag in ['dry-run','read-only','exec','search']: a.add_argument('--'+flag,action='store_true')
    args=p.parse_args(argv)
    try:
        root=Path(args.project).expanduser().resolve()
        if not root.is_dir(): raise RelayError('Choose an existing project directory.')
        if args.action=='install': result=install(root)
        elif args.action=='uninstall': result=uninstall(root)
        elif args.action=='doctor':
            s=load_state(root)
            if not s['files']: raise RelayError('Run install first.')
            rs=roles(root); cfg=settings(root)
            if args.check_models: validate_models([(d['model'],d['model_reasoning_effort']) for _,d in rs]+[(cfg[k]['model'],cfg[k]['effort']) for k in ['coordinator','deep','frontier']])
            result={'ok':True,'agents':len(rs),'models_checked':args.check_models}
        else:
            cmd,cfg=command(root,args)
            if args.dry_run: result={'argv':cmd,'model':cfg['model'],'effort':cfg['effort']}
            else:
                validate_models([(cfg['model'],cfg['effort'])]+[(d['model'],d['model_reasoning_effort']) for _,d in roles(root)])
                return subprocess.run(cmd).returncode
        print(json.dumps(result,indent=2));return 0
    except (RelayError,OSError,ValueError,subprocess.TimeoutExpired) as e:
        print('partition-code: '+str(e),file=sys.stderr);return 1
if __name__=='__main__': raise SystemExit(main())
