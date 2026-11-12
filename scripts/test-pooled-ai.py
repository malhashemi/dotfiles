#!/usr/bin/env python3
"""Isolated pooled migration and mocked native OAuth tests. No live config/network."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]


def load(name, path):
    module = types.ModuleType(name); module.__file__ = str(path)
    exec(compile(path.read_text(),str(path),'exec'),module.__dict__)
    return module


class PoolTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name);self.root=self.home/'.config/cli-proxy-api'
        self.pool=load('pool',SOURCE/'dot_local/bin/executable_cpapi');self.pool.ROOT=self.root
        self.setup=load('setup',SOURCE/'dot_local/bin/executable_ai-setup')
        self.setup.HOME_DIR=self.home;self.setup.ROOT=self.root;self.setup.INPUTS=self.home/'.config/ai-setup'
        self.setup.BIN=self.home/'.local/bin'
        shutil.copytree(SOURCE/'dot_config/private_ai-setup',self.setup.INPUTS)
        shutil.copyfile(self.setup.INPUTS/'t3/profiles.json.tmpl',self.setup.INPUTS/'t3/profiles.json')
        self.setup.pool_helper=lambda:self.pool.__dict__
        self.setup.t3_running=lambda:False;self.setup.t3_desktop_running=lambda:False
        self.write(self.root/'config.yaml',{'host':'127.0.0.1','port':8317,'api-keys':['fixture-client'],'routing':{'strategy':'round-robin'},'unrelated':42})
        (self.root/'client-key').write_text('fixture-client')
        self.write(self.root/'claude-accounts.json',{'a':{'auth_file':'a.json'},'b':{'auth_file':'b.json'}})
        self.write(self.root/'auth/a.json',self.auth('a'));self.write(self.root/'auth/b.json',self.auth('b'))
        self.patches=[]
        self.pool.require_proxy_stopped=lambda:None

    def write(self,path,value): self.pool.save(path,value)
    def auth(self,name,provider='claude'):
        return {'type':provider,'account_uuid':name,'organization_uuid':'org', 'account_id':name,'sub':name,
                'access_token':'fixture-access-'+name,'refresh_token':'fixture-refresh-'+name,'expired':'2099-01-01T00:00:00+00:00'}
    def cli(self,*args):
        with patch.object(sys,'argv',['cpapi','--proxy-stopped',*args]),contextlib.redirect_stdout(io.StringIO()): self.pool.main()
    def migrate(self,apply=True):
        with contextlib.redirect_stdout(io.StringIO()): self.setup.migrate_pool({},apply)

    def test_seed_priorities_pending_backup(self):
        records=self.pool.inventory()['accounts'];self.assertEqual([records[n]['priority'] for n in ('personal','work','backup')],[300,200,100]);self.assertEqual(records['backup']['state'],'pending');self.assertFalse(records['backup']['required'])
    def test_lifecycle_persists_removal(self):
        self.cli('add','extra','openai','--priority','50');self.cli('priority','extra','250');self.cli('disable','extra');self.cli('enable','extra');self.cli('remove','extra')
        r=self.pool.inventory()['accounts']['extra'];self.assertEqual(r['state'],'removed');self.assertEqual(r['provider'],'codex');self.assertEqual(r['priority'],250)
        self.pool.migrate_accounts(True);self.assertEqual(self.pool.inventory()['accounts']['extra']['state'],'removed')
    def test_active_remove_retains_tokens(self):
        original=self.pool.read(self.root/'auth/a.json');self.cli('remove','personal');r=self.pool.inventory()['accounts']['personal'];new=self.pool.read(self.root/r['archived_auth_file']);self.assertTrue(new['disabled']);self.assertEqual(new['refresh_token'],original['refresh_token']);self.assertFalse((self.root/'auth/a.json').exists())
    def test_duplicate_disabled_without_token_replacement(self):
        original=self.pool.read(self.root/'auth/b.json');self.write(self.root/'auth/duplicate.json',original)
        self.pool.migrate_accounts(True);self.assertFalse((self.root/'auth/duplicate.json').exists());self.assertEqual(self.pool.read(self.root/'auth/b.json')['refresh_token'],original['refresh_token'])
        self.assertEqual(self.pool.migrate_accounts(False)[1],[])
    def test_separate_refresh_state_blocks_before_any_write(self):
        auth=self.auth('b');auth['refresh_token']='fixture-separate';self.write(self.root/'auth/duplicate.json',auth)
        with self.assertRaisesRegex(ValueError,'separate refresh state'):self.migrate()
        self.assertFalse((self.root/'management-key').exists());self.assertEqual(self.patches,[])
    def test_migration_preserves_preferences_and_is_idempotent(self):
        self.write(self.home/'.claude/settings.json',{'hooks':{'local':[]},'env':{'LOCAL':'keep','ANTHROPIC_DEFAULT_FABLE_MODEL':'stale'},'permissions':{'allow':['read']}})
        self.write(self.home/'.t3/userdata/settings.json',{'providerInstances':{'claude-mixed-a':{},'codex':{'config':{'binaryPath':'custom'}}},'other':1})
        self.migrate();paths=[self.root/'config.yaml',self.home/'.claude/settings.json',self.home/'.t3/userdata/settings.json'];before=[p.read_bytes() for p in paths];self.migrate();self.assertEqual(before,[p.read_bytes() for p in paths])
        claude=self.pool.read(paths[1]);self.assertEqual(claude['env']['LOCAL'],'keep');self.assertIn('hooks',claude);self.assertNotIn('ANTHROPIC_DEFAULT_FABLE_MODEL',claude['env'])
        t3=self.pool.read(paths[2]);self.assertEqual(t3['providerInstances']['codex']['config']['binaryPath'],'custom');self.assertEqual(t3['providerInstances']['claudeAgent']['environment'],[]);self.assertEqual(t3['providerInstances']['claudeAgent']['config']['homePath'],'')
        self.assertEqual((self.root/'management-key').stat().st_mode&0o777,0o600);self.assertEqual(t3['usageLimitSources']['local-cliproxy']['kind'],'cliproxy')
    def test_proxy_hash_and_t3_secret_redaction_remain_idempotent(self):
        self.migrate()
        config=self.pool.read(self.root/'config.yaml');config['remote-management']['secret-key']='$2a$fixture-hash';self.write(self.root/'config.yaml',config)
        path=self.home/'.t3/userdata/settings.json';t3=self.pool.read(path);t3['usageLimitSources']['local-cliproxy']['managementKey']='\u2022'*6;self.write(path,t3)
        self.migrate();self.assertEqual(self.pool.read(self.root/'config.yaml'),config);self.assertEqual(self.pool.read(path),t3)
    def test_dry_run_creates_nothing(self):
        before=sorted(str(p.relative_to(self.home)) for p in self.home.rglob('*'));self.migrate(False);self.assertEqual(before,sorted(str(p.relative_to(self.home)) for p in self.home.rglob('*')));self.assertEqual(self.patches,[])
    def test_running_t3_refuses_all_writes(self):
        self.setup.t3_running=lambda:True
        with self.assertRaisesRegex(ValueError,'Close T3'): self.migrate()
        self.assertFalse((self.root/'management-key').exists());self.assertEqual(self.patches,[])
    def test_metadata_refuses_running_proxy_before_write(self):
        before=(self.root/'auth/a.json').read_bytes()
        def refuse(): raise ValueError('Proxy must already be stopped')
        self.pool.require_proxy_stopped=refuse
        with self.assertRaisesRegex(ValueError,'stopped'):self.cli('priority','personal','9')
        self.assertEqual(before,(self.root/'auth/a.json').read_bytes())
    def test_metadata_reads_latest_and_preserves_all_token_fields(self):
        auth=self.auth('a');auth['refresh_token']='latest';auth['custom']={'keep':True};self.write(self.root/'auth/a.json',auth)
        self.cli('priority','personal','444');new=self.pool.read(self.root/'auth/a.json')
        self.assertEqual(new,{**auth,'priority':444,'disabled':False})
    def test_explicit_canonical_and_journal_resume(self):
        auth=self.auth('b');auth['refresh_token']='different';auth['disabled']=True;self.write(self.root/'auth/duplicate.json',auth)
        with self.assertRaisesRegex(ValueError,'separate refresh state'):self.pool.migrate_accounts(False)
        self.cli('reconcile','work','b.json')
        self.assertEqual(self.pool.inventory()['canonicalSelections']['work'],'b.json')
        self.assertFalse((self.root/'auth/duplicate.json').exists());self.assertEqual(len(self.pool.inventory()['quarantined']),1)
        self.pool.migrate_accounts(True);self.pool.migrate_accounts(True)
        data=self.pool.inventory();self.write(self.root/'auth/again.json',auth)
        moves=self.pool.archive_plan(data,['again.json']);data['quarantined'].extend(moves)
        self.write(self.root/'reconcile-journal.json',{'inventory':data,'moves':moves})
        (self.root/moves[0]['archive']).parent.mkdir(exist_ok=True)
        (self.root/'auth/again.json').rename(self.root/moves[0]['archive'])
        self.pool.migrate_accounts(True);self.assertFalse((self.root/'reconcile-journal.json').exists())
    def test_restore_readd_and_adoption_ignore_archived_identity(self):
        self.cli('remove','personal');self.cli('restore','personal');self.assertEqual(self.pool.inventory()['accounts']['personal']['state'],'active')
        self.cli('remove','personal');self.cli('add','replacement','claude')
        self.assertFalse(self.pool.inventory()['accounts']['replacement']['required'])
        with patch.object(self.pool.shutil,'which',return_value='/fixture/proxy'),patch.object(self.pool.subprocess,'run',side_effect=self.oauth('claude','a')):self.cli('login','replacement')
        with self.assertRaisesRegex(ValueError,'another active'):self.cli('restore','personal')
        self.cli('add','personal','claude');self.assertEqual(self.pool.inventory()['accounts']['personal']['state'],'pending')
    def test_nested_config_oauth_isolation_and_endpoint_keys(self):
        self.write(self.root/'config.yaml',{'server':{'host':'127.0.0.1','port':8317},'access':{'api-keys':['fixture-client']},'oauth':{'auth-dir':str(self.root/'auth')}})
        def oauth(args,check):
            cfg=self.pool.read(Path(args[args.index('-config')+1]));self.assertEqual(cfg['oauth']['auth-dir'],cfg['auth-dir']);self.assertNotEqual(cfg['auth-dir'],str(self.root/'auth'))
            self.write(Path(cfg['oauth']['auth-dir'])/'oauth.json',self.auth('backup'))
        with patch.object(self.pool.shutil,'which',return_value='/fixture/proxy'),patch.object(self.pool.subprocess,'run',side_effect=oauth):self.cli('login','backup')
        self.setup.configure_cli=lambda:None
        self.setup.ensure_runtime();self.migrate()
    def test_fresh_hooks_only_preferences_merge_connection(self):
        original={'hooks':{'local':[]},'permissions':{'allow':['read']},'env':{'KEEP':'yes'},'model':'user'}
        self.write(self.home/'.claude/settings.json',original);self.setup.configure_cli=lambda:None
        self.setup.ensure_runtime();after=self.pool.read(self.home/'.claude/settings.json')
        self.assertEqual(after['hooks'],original['hooks']);self.assertEqual(after['model'],'user');self.assertEqual(after['env']['KEEP'],'yes');self.assertEqual(after['env']['ANTHROPIC_AUTH_TOKEN'],'fixture-client')
    def test_separate_config_and_private_patch_with_t3_running(self):
        self.pool.migrate_accounts(True);self.setup.t3_running=lambda:True
        self.setup.migrate_pool({},True,phase='config')
        destination=self.home/'private-patch.json';self.setup.migrate_pool({},True,export_path=destination)
        self.assertEqual(destination.stat().st_mode&0o777,0o600)
        self.assertEqual(self.pool.read(destination)['serverSettingsPatch']['providerInstances']['claudeAgent']['environment'],[])
        self.assertFalse((self.home/'.t3/userdata/settings.json').exists())
    def test_settings_phase_refuses_unverified_accounts(self):
        with self.assertRaisesRegex(ValueError,'account phase'):self.setup.migrate_pool({},True,phase='config')
        self.assertFalse((self.root/'management-key').exists())
    def test_headless_pool_migration_does_not_create_desktop_preferences(self):
        self.setup.migrate_pool({'role':'headless'},True)
        self.assertFalse((self.home/'.t3/userdata/client-settings.json').exists())
        self.assertIn('claudeAgent',self.pool.read(self.home/'.t3/userdata/settings.json')['providerInstances'])
    def test_t3_plan_keeps_user_favorites_and_claude_menu(self):
        fable={'provider':'claudeAgent','model':'claude-fable-5-2'};menu={'hiddenModels':['claude-sonnet-5']}
        self.write(self.home/'.t3/userdata/settings.json',{'favorites':[fable,{'provider':'claude-mixed-a','model':'claude-opus-5-5'}],'providerModelPreferences':{'claudeAgent':menu}})
        self.write(self.home/'.t3/userdata/client-settings.json',{'favorites':[fable]})
        planned={str(path.name):after for path,_,after in self.setup.planned_t3({'role':'desktop'})}
        server=planned['settings.json'];self.assertIn(fable,server['favorites']);self.assertEqual(server['providerModelPreferences']['claudeAgent'],menu)
        self.assertNotIn('claude-mixed-a',[f['provider'] for f in server['favorites']])
        self.assertIn(fable,planned['client-settings.json']['favorites'])
    def test_builtin_opus_preferences_on_server_and_repeat_export(self):
        self.write(self.home/'.t3/userdata/settings.json',{'favorites':[{'provider':'claude-mixed-b','model':'fable'}], 'providerModelPreferences':{'claudeAgent':{'hidden':['claude-opus-5-5']},'codex':{'keep':True}}})
        self.migrate()
        server=self.pool.read(self.home/'.t3/userdata/settings.json')
        self.assertIn({'provider':'claudeAgent','model':'claude-opus-5-5'},server['favorites'])
        self.assertNotIn('claudeAgent',server['providerModelPreferences']);self.assertIn('codex',server['providerModelPreferences'])
        self.setup.migrate_pool({},True,export_path=self.home/'patch.json')
        self.assertEqual(self.pool.read(self.home/'patch.json')['serverSettingsPatch'],{})
        defaults=self.setup.model_defaults()
        self.assertFalse(defaults['catalog'][0].get('t3Custom',False))
        self.assertNotIn('contextWindow',[o['id'] for o in defaults['t3']['defaultModelSelection']['options']])
    def test_proxy_guard_detects_process_and_endpoint(self):
        guard=load('guard',SOURCE/'dot_local/bin/executable_cpapi');guard.ROOT=self.root
        with patch.object(guard.subprocess,'run',return_value=types.SimpleNamespace(stdout='/usr/bin/CLIProxyAPI\n')):
            with self.assertRaisesRegex(ValueError,'stopped'):guard.require_proxy_stopped()
        with patch.object(guard.subprocess,'run',return_value=types.SimpleNamespace(stdout='')),patch.object(guard.socket,'create_connection',side_effect=ConnectionRefusedError):guard.require_proxy_stopped()
        with patch.object(guard.subprocess,'run',return_value=types.SimpleNamespace(stdout='')),patch.object(guard.socket,'create_connection'):
            with self.assertRaisesRegex(ValueError,'listening'):guard.require_proxy_stopped()
    def test_legacy_launchers_retained_before_migration(self):
        removals=(SOURCE/'.chezmoiremove').read_text().splitlines()
        for name in ('claude-t3-mixed','claude-mixed-a','claude-mixed-b','claude-personal','claude-work','claude-mixed-setup'):
            self.assertNotIn('.local/bin/'+name,removals)
            self.assertTrue(any((SOURCE/'dot_local/bin'/prefix).exists() for prefix in ('executable_'+name,'symlink_'+name)))
    def test_oauth_config_override_rejected(self):
        with self.assertRaisesRegex(ValueError,'staged configuration'):self.cli('login','backup','-config','unsafe')
    def oauth(self,provider,name):
        def run(args,check):
            config=self.pool.read(Path(args[args.index('-config')+1]));self.write(Path(config['auth-dir'])/'oauth.json',self.auth(name,provider))
        return run
    def test_new_login_needs_no_proxy_stop_and_never_replaces_a_file(self):
        def refuse(): raise AssertionError('New account must not stop the proxy')
        self.pool.require_proxy_stopped = refuse
        with patch.object(self.pool.shutil, 'which', return_value='/fixture/proxy'), patch.object(self.pool.subprocess, 'run', side_effect=self.oauth('claude', 'backup')), patch.object(sys, 'argv', ['cpapi', 'login', 'backup']):
            with contextlib.redirect_stdout(io.StringIO()): self.pool.main()
        account = self.pool.inventory()['accounts']['backup']
        path = self.root/'auth'/account['auth_file']
        original = path.read_bytes()
        with self.assertRaises(FileExistsError): self.pool.save(path, {'replace':True}, exclusive=True)
        self.assertEqual(path.read_bytes(), original)
        with patch.object(sys, 'argv', ['cpapi', 'login', 'backup']):
            with self.assertRaisesRegex(ValueError, 'Changing existing credentials'): self.pool.main()

    def test_staged_oauth_for_each_provider_and_refresh_filename(self):
        for provider in ('claude','codex','xai'):
            name='new-'+provider;self.cli('add',name,provider)
            with patch.object(self.pool.shutil,'which',return_value='/fixture/proxy'),patch.object(self.pool.subprocess,'run',side_effect=self.oauth(provider,name)):
                self.cli('login',name);filename=self.pool.inventory()['accounts'][name]['auth_file'];self.cli('login',name)
            self.assertEqual(filename,self.pool.inventory()['accounts'][name]['auth_file'])
            self.assertFalse((self.home/'.t3').exists())
    def test_backup_login_and_duplicate_identity_rejection(self):
        with patch.object(self.pool.shutil,'which',return_value='/fixture/proxy'),patch.object(self.pool.subprocess,'run',side_effect=self.oauth('claude','backup')):self.cli('login','backup')
        self.assertEqual(self.pool.inventory()['accounts']['backup']['state'],'active')
        with patch.object(self.pool.shutil,'which',return_value='/fixture/proxy'),patch.object(self.pool.subprocess,'run',side_effect=self.oauth('claude','a')):
            with self.assertRaisesRegex(ValueError,'already exists'):self.cli('login','backup')
    def test_native_provider_login_aliases_work_on_fresh_inventory(self):
        for alias,provider in [('openai','codex'),('grok','xai')]:
            with patch.object(self.pool.shutil,'which',return_value='/fixture/proxy'),patch.object(self.pool.subprocess,'run',side_effect=self.oauth(provider,provider)):
                self.cli('login',alias)
            self.assertEqual(self.pool.inventory()['accounts'][provider]['state'],'active')
    def test_failed_oauth_changes_nothing(self):
        import subprocess
        with patch.object(self.pool.shutil,'which',return_value='/fixture/proxy'),patch.object(self.pool.subprocess,'run',side_effect=subprocess.CalledProcessError(1,[])):
            with self.assertRaises(subprocess.CalledProcessError):self.cli('login','backup')
        self.assertFalse((self.root/'accounts.json').exists())
    def test_native_providers_adopted_without_metadata_loss(self):
        auth=self.auth('c','codex');auth['custom']='preserve';self.write(self.root/'auth/codex-original.json',auth);self.pool.migrate_accounts(True)
        self.assertEqual(self.pool.inventory()['accounts']['codex']['auth_file'],'codex-original.json');self.assertEqual(self.pool.read(self.root/'auth/codex-original.json')['custom'],'preserve')


if __name__=='__main__':unittest.main()
