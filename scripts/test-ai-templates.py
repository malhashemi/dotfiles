#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,tempfile
r=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='pool-template-') as tmp:
 t=Path(tmp);cfg=t/'chezmoi.toml';cfg.write_text('[data.ai]\nenabled=true\nremote_access=false\n[data.machine]\nrole="laptop"\nautologin=false\n')
 paths=['dot_config/private_ai-setup/t3/profiles.json.tmpl','dot_config/opencode/private_opencode.json.tmpl','.chezmoiscripts/run_once_after_90-ai-setup.sh.tmpl','.chezmoiscripts/run_onchange_after_agent-desktop.sh.tmpl','.chezmoiignore.tmpl']
 for name in paths:
  result=subprocess.run(['chezmoi','--config',str(cfg),'--source',str(r),'--cache',str(t/'cache'),'--persistent-state',str(t/'state.db'),'execute-template','--file',str(r/name)],capture_output=True,text=True,check=True)
  if 'json.tmpl' in name:json.loads(result.stdout)
  if name.endswith('.sh.tmpl'):subprocess.run(['bash','-n'],input=result.stdout,text=True,check=True)
  print('PASS render',name)
