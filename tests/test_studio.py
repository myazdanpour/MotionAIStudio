import importlib.util, unittest, tempfile, threading, urllib.request, urllib.error, json, sys
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('studio',Path(__file__).resolve().parents[1]/'app.py'); app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
class StudioTests(unittest.TestCase):
 def setUp(self):
  app.JOBS.clear();app.VIDEOS.clear()
  self.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
  threading.Thread(target=self.server.serve_forever,daemon=True).start()
  self.url='http://127.0.0.1:'+str(self.server.server_port)
 def tearDown(self): self.server.shutdown();self.server.server_close()
 def request(self,path,data=None,headers={}):
  return urllib.request.urlopen(urllib.request.Request(self.url+path,data=json.dumps(data).encode() if data is not None else None,headers=headers),timeout=3)
 def test_sse_does_not_block_panel_and_replays(self):
  app.JOBS['j']=dict(events=[],done=False)
  app.emit('j','stage','working',stage=2)
  with self.request('/api/events?job_id=j') as stream:
   self.assertEqual(stream.readline(),b'id: 1\n')
   with self.request('/') as page:self.assertEqual(page.status,200)
   app.emit('j','complete','done')
  with self.request('/api/events?job_id=j',headers={'Last-Event-ID':'1'}) as stream:
   body=stream.read().decode();self.assertIn('id: 2',body);self.assertNotIn('working',body)
 def test_custom_video_ranges(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'out';out.mkdir();(out/'test.mp4').write_bytes(b'0123456789')
   from urllib.parse import quote
   with self.request('/api/videos?project_dir='+quote(td)) as r: url=json.load(r)[0]['url']
   with self.request(url,headers={'Range':'bytes=2-5'}) as r:self.assertEqual(r.status,206);self.assertEqual(r.read(),b'2345')
   with self.request(url,headers={'Range':'bytes=-3'}) as r:self.assertEqual(r.read(),b'789')
   with self.assertRaises(urllib.error.HTTPError) as e:self.request(url,headers={'Range':'bytes=99-'})
   self.assertEqual(e.exception.code,416);e.exception.close()
 def test_validation(self):
  for d in ({'prompt':'x','model':'test','duration':1801},[],{'prompt':''}):
   with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/generate',d)
   self.assertEqual(e.exception.code,400);e.exception.close()
 def test_offline_language_and_duration(self):
  for lang in ('fa','en'):
   d=app.validate(dict(prompt='Coffee story',duration=1800,model='test',language=lang,offline=True))
   with patch.object(app,'api',side_effect=RuntimeError()):r=app.enhance(d)
   self.assertEqual(r['source'],'template');self.assertEqual(r['scenes'][0]['start'],0);self.assertEqual(r['scenes'][-1]['end'],1800)
   self.assertIn('54000 frames',app.contract(d))
 def test_failure_never_renders_existing_output(self):
  app.JOBS['j']=dict(events=[],done=False)
  with tempfile.TemporaryDirectory() as td:
   (Path(td)/'package.json').write_text('{}')
   with patch.object(app,'run_process',side_effect=[None,RuntimeError('failed')]) as run:
    app.pipeline('j',dict(project_dir=td,prompt='test',model='test',duration=10,fps=30))
    self.assertEqual(run.call_count,2)
  self.assertEqual(app.JOBS['j']['events'][-1]['type'],'error')
 def test_stream_usage(self):
  app.JOBS['j']=dict(events=[],done=False,cancel=False)
  frames=[{'type':'assistant','message':{'id':'a','usage':{'input_tokens':100,'output_tokens':20},'content':[]}}, {'type':'result','usage':{'input_tokens':100,'output_tokens':20},'total_cost_usd':.01}]
  script='import json\n'+ '\n'.join('print('+repr(json.dumps(x))+',flush=True)' for x in frames)
  app.run_process('j',[sys.executable,'-c',script],str(Path.cwd()),None,True)
  usage=[e for e in app.JOBS['j']['events'] if e['type']=='usage']
  self.assertFalse(usage[0]['data']['final']);self.assertTrue(usage[-1]['data']['final']);self.assertEqual(usage[-1]['data']['usage']['output_tokens'],20)
 def test_browser_permission_error_is_actionable(self):
  err=app.process_error('FATAL MachPortRendezvous bootstrap_check_in Permission denied (1100)')
  self.assertEqual(err.code,'browser_permission_denied')
  self.assertIn('Terminal',str(err))
 def test_composition_detection(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'src').mkdir()
   (root/'src/Root.tsx').write_text('<Composition id="ATGOLDEN"/><Composition id="HelloWorld"/>')
   self.assertEqual(app.composition_id(root),'ATGOLDEN')
   (root/'src/Root.tsx').write_text('<Composition id="One"/><Composition id="Two"/>')
   with self.assertRaises(ValueError):app.composition_id(root)
   self.assertEqual(app.composition_id(root,'Two'),'Two')
 def test_render_only_never_calls_model(self):
  app.JOBS['j']=dict(events=[],done=False)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'package.json').write_text('{}');(root/'src').mkdir()
   (root/'src/Root.tsx').write_text('<Composition id="ATGOLDEN"/>')
   commands=[]
   def fake(job,cmd,*args):
    commands.append(cmd)
    if 'render' in cmd:Path(cmd[5]).write_bytes(b'mp4')
   with patch.object(app,'run_process',side_effect=fake):
    app.pipeline('j',dict(project_dir=td,render_only=True))
   self.assertEqual(app.JOBS['j']['events'][-1]['type'],'complete')
   self.assertFalse(any(cmd[0]=='claude' for cmd in commands))
   self.assertIn('ATGOLDEN',commands[-1])
 def test_auth_error_is_not_hidden_by_template(self):
  d=app.validate(dict(prompt='Coffee',model='test'))
  with patch.object(app,'api',side_effect=app.EnhanceError('missing key','authentication',401)) as call:
   with self.assertRaises(app.EnhanceError) as e:app.enhance(d)
   self.assertEqual(e.exception.status,401);self.assertEqual(call.call_count,1)
 def test_enhance_auth_http_status(self):
  with patch.object(app,'api',side_effect=app.EnhanceError('missing key','authentication',401)):
   with self.assertRaises(urllib.error.HTTPError) as e:self.request('/api/enhance',{'prompt':'Coffee','model':'test'})
   self.assertEqual(e.exception.code,401);self.assertEqual(json.load(e.exception)['code'],'authentication');e.exception.close()
 def test_enhance_markdown_and_prose(self):
  payload={'enhanced_prompt':'A polished brief','improvements':['Lighting'], 'scenes':[{'start':0,'end':30,'title':'Opening','description':'Coffee'}]}
  response={'choices':[{'message':{'content':'Here is the brief:\n```json\n'+json.dumps(payload)+'\n```'},'finish_reason':'stop'}]}
  self.assertEqual(app.parse_enhancement(response,'/chat/completions',30),payload)
 def test_enhance_bad_scene_and_truncation(self):
  for response in ({'choices':[{'message':{'content':'{}'},'finish_reason':'length'}]}, {'choices':[{'message':{'content':json.dumps({'enhanced_prompt':'test','improvements':[],'scenes':['invalid']})}}]}):
   with self.assertRaises(app.EnhanceError):app.parse_enhancement(response,'/chat/completions',30)
 def test_protocol_fallback(self):
  d=app.validate(dict(prompt='Coffee',model='test',duration=30))
  payload={'enhanced_prompt':'Brief','improvements':[], 'scenes':[{'start':0,'end':30,'title':'Scene','description':'Coffee'}]}
  with patch.object(app,'api',side_effect=[app.EnhanceError('unsupported','endpoint_or_model'),{'content':[{'text':json.dumps(payload)}],'usage':{'input_tokens':20,'output_tokens':40}}]) as call:
   result=app.enhance(d)
   self.assertEqual(call.call_count,2);self.assertEqual(result['source'],'ai');self.assertEqual(result['usage']['output_tokens'],40)
 def test_style_is_explicit_and_custom_direction_included(self):
  for style in app.STYLES:
   text=app.contract(dict(style=style,style_notes='Warm coffee commercial',duration=10,fps=30))
   self.assertIn('Selected visual style: '+style,text)
   self.assertIn('Warm coffee commercial',text)
   self.assertIn('Existing project scenes are not a creative brief',text)
 def test_old_scene_cannot_pass_fresh_scene_check(self):
  with tempfile.TemporaryDirectory() as td:
   project=Path(td);(project/'src').mkdir()
   (project/'src/Root.tsx').write_text('<Composition id="ATGOLDEN" component={PlatformerComposition}/>')
   with self.assertRaises(ValueError):app.verify_generated_scene(project,'MotionFilmNew')
   (project/'src/MotionFilmNew.tsx').write_text('export const MotionFilmNew=()=>null;')
   (project/'src/Root.tsx').write_text('import {MotionFilmNew} from "./MotionFilmNew"; <Composition id="MotionFilmNew" component={PlatformerComposition}/>')
   with self.assertRaises(ValueError):app.verify_generated_scene(project,'MotionFilmNew')
   (project/'src/Root.tsx').write_text('import {MotionFilmNew} from "./MotionFilmNew"; <Composition id="MotionFilmNew" component={MotionFilmNew}/>')
   app.verify_generated_scene(project,'MotionFilmNew')
 def test_successful_model_without_new_scene_never_renders(self):
  app.JOBS['j']=dict(events=[],done=False)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'package.json').write_text('{}');(root/'src').mkdir()
   (root/'src/Root.tsx').write_text('<Composition id="ATGOLDEN"/>')
   with patch.object(app,'run_process') as run:
    app.pipeline('j',dict(project_dir=td,prompt='Coffee',model='test',duration=10,fps=30,style='cinematic',composition_name='ATGOLDEN'))
    self.assertEqual(run.call_count,2)
    self.assertFalse(any('render' in c.args[1] for c in run.call_args_list))
   self.assertEqual(app.JOBS['j']['events'][-1]['type'],'error')
 def test_generation_renders_unique_scene_ignoring_old_selection(self):
  app.JOBS['j']=dict(events=[],done=False)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'package.json').write_text('{}');(root/'src').mkdir();commands=[]
   def fake(job,cmd,*args):
    commands.append(cmd)
    if cmd[0]=='claude':
     import re
     comp=re.search(r'exact literal id (MotionFilm[0-9a-f]+)',cmd[2])[1]
     (root/'src'/f'{comp}.tsx').write_text(f'export const {comp}=()=>null;')
     (root/'src/Root.tsx').write_text(f'import {{{comp}}} from "./{comp}"; <Composition id="{comp}" component={{{comp}}}/>')
    if 'render' in cmd:Path(cmd[5]).write_bytes(b'mp4')
   with patch.object(app,'run_process',side_effect=fake):
    app.pipeline('j',dict(project_dir=td,prompt='Coffee',model='test',duration=10,fps=30,style='cinematic',composition_name='ATGOLDEN'))
   self.assertEqual(app.JOBS['j']['events'][-1]['type'],'complete')
   self.assertTrue(commands[-1][4].startswith('MotionFilm'))
   self.assertNotEqual(commands[-1][4],'ATGOLDEN')
if __name__=='__main__':unittest.main()
