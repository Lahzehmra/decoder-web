#!/usr/bin/env python3
"""
Script to update app.py and index.html on Raspberry Pi
"""
import paramiko
import os

# Files to update
files_to_update = {
    'app.py': '''#!/usr/bin/env python3
from flask import Flask, jsonify, request, render_template
import subprocess, shutil, os, time
import struct, math, tempfile
from pcm5102a_driver import PCM5102A_Driver

app = Flask(__name__)

PLAYER_PROC = None
PCM5102A_DRIVER = None

def stop_player():
    global PLAYER_PROC
    try:
        if PLAYER_PROC and PLAYER_PROC.poll() is None:
            PLAYER_PROC.terminate()
            try:
                PLAYER_PROC.wait(timeout=1)
            except Exception:
                pass
        subprocess.run(['pkill','-x','cvlc'], check=False)
        subprocess.run(['pkill','-x','ffmpeg'], check=False)
        subprocess.run(['pkill','-x','aplay'], check=False)
    except Exception:
        pass
    PLAYER_PROC = None

def start_player(url: str, out_dev: str = 'hw:0,0') -> bool:
    global PLAYER_PROC
    stop_player()
    env = os.environ.copy()
    cvlc = shutil.which('cvlc') or '/usr/bin/cvlc'
    if os.path.exists(cvlc):
        try:
            PLAYER_PROC = subprocess.Popen([
                cvlc, '--intf','dummy','--no-video','--quiet',
                '--aout','alsa', f'--alsa-audio-device={out_dev}',
                '--network-caching','8000','--live-caching','12000', url
            ], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1.5)
            if PLAYER_PROC.poll() is None:
                return True
        except Exception:
            pass
    ffmpeg = shutil.which('ffmpeg') or '/usr/bin/ffmpeg'
    aplay = shutil.which('aplay') or '/usr/bin/aplay'
    if os.path.exists(ffmpeg) and os.path.exists(aplay):
        try:
            PLAYER_PROC = subprocess.Popen([
                ffmpeg,'-nostdin','-reconnect','1','-reconnect_streamed','1','-reconnect_delay_max','10',
                '-i', url,'-f','s16le','-ac','2','-ar','44100','-'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ap = subprocess.Popen([aplay,'-D',out_dev,'-f','cd','-c','2','-r','44100'], stdin=PLAYER_PROC.stdout)
            PLAYER_PROC.stdout.close()
            time.sleep(1.5)
            if PLAYER_PROC.poll() is None and ap.poll() is None:
                return True
        except Exception:
            pass
    stop_player()
    return False

def get_pcm5102a_driver():
    global PCM5102A_DRIVER
    if PCM5102A_DRIVER is None:
        PCM5102A_DRIVER = PCM5102A_Driver('hw:0,0', 44100, 2, 'S16_LE')
    return PCM5102A_DRIVER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def api_start():
    data = request.get_json(force=True)
    url = data.get('url','').strip()
    out = data.get('device','hw:0,0').strip() or 'hw:0,0'
    if not url:
        return jsonify(success=False, message='Missing url'), 400
    ok = start_player(url, out)
    return jsonify(success=ok)

@app.route('/api/stop', methods=['POST'])
def api_stop():
    stop_player()
    return jsonify(success=True)

@app.route('/api/pcm5102a/tone', methods=['POST'])
def api_pcm5102a_tone():
    try:
        data = request.get_json(force=True)
        frequency = float(data.get('frequency', 440))
        duration = float(data.get('duration', 2.0))
        amplitude = float(data.get('amplitude', 0.9))
        
        driver = get_pcm5102a_driver()
        success = driver.play_tone(frequency, duration, amplitude)
        return jsonify(success=success, message=f'Played {frequency}Hz tone for {duration}s')
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/api/pcm5102a/voice', methods=['POST'])
def api_pcm5102a_voice():
    try:
        data = request.get_json(force=True)
        text = data.get('text', 'Hello PCM5102A is working')
        
        from test_mcp1502_audio import test_voice_simulation
        driver = get_pcm5102a_driver()
        driver.start_stream()
        test_voice_simulation(driver, text)
        driver.close()
        
        return jsonify(success=True, message=f'Played voice simulation: {text}')
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/api/pcm5102a/test', methods=['POST'])
def api_pcm5102a_test():
    try:
        driver = get_pcm5102a_driver()
        driver.test()
        return jsonify(success=True, message='PCM5102A test complete')
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@app.route('/api/audio/devices', methods=['GET'])
def api_audio_devices():
    try:
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        devices = []
        for line in result.stdout.split('\\n'):
            if 'card' in line.lower() and ':' in line:
                devices.append(line.strip())
        return jsonify(success=True, devices=devices)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
''',
    
    'templates/index.html': '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Audio Control Panel - PCM5102A DAC</title>
  <style>
    :root { --bg:#0b0f14; --card:#121822; --acc:#2eaadc; --text:#e9f1f5; --muted:#9ab3c0; }
    body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu; background:var(--bg); color:var(--text); }
    .wrap { max-width:900px; margin:6vh auto; padding:24px; background:var(--card); border-radius:16px; box-shadow:0 8px 24px rgba(0,0,0,.25); }
    h1 { margin:0 0 8px; font-size:26px; }
    h2 { margin:24px 0 12px; font-size:20px; color:var(--acc); }
    p { color:var(--muted); margin:0 0 24px; }
    label { display:block; font-size:14px; color:var(--muted); margin:10px 0 6px; }
    input, select { width:100%; padding:12px 14px; border-radius:10px; border:1px solid #213040; background:#0e141c; color:var(--text); outline:none; }
    .row { display:flex; gap:12px; align-items:center; margin-top:16px; flex-wrap:wrap; }
    button { appearance:none; border:0; padding:12px 18px; border-radius:10px; background:var(--acc); color:#022; font-weight:600; cursor:pointer; }
    button.secondary { background:#223244; color:var(--text); }
    button.test { background:#28a745; }
    .status { margin-top:18px; font-size:14px; color:var(--muted); }
    .section { margin:24px 0; padding:20px; background:#0e141c; border-radius:12px; border:1px solid #213040; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Audio Control Panel</h1>
    <p>Control PCM5102A DAC and Audio Streams</p>
    
    <div class="section">
      <h2>PCM5102A DAC Test</h2>
      <label>Frequency (Hz)</label>
      <input id="freq" type="number" value="440" min="100" max="5000" />
      <label>Duration (seconds)</label>
      <input id="duration" type="number" value="2" min="0.5" max="10" step="0.5" />
      <label>Amplitude (0.0 - 1.0)</label>
      <input id="amplitude" type="number" value="0.9" min="0.1" max="1.0" step="0.1" />
      <div class="row">
        <button class="test" onclick="playTone()">Play Tone</button>
        <button class="test" onclick="playVoice()">Play Voice</button>
        <button class="test" onclick="runTest()">Full Test</button>
      </div>
      <div class="status" id="pcmStatus"></div>
    </div>
    
    <div class="section">
      <h2>Quick Tests</h2>
      <div class="grid">
        <button class="test" onclick="quickTest(440)">440 Hz</button>
        <button class="test" onclick="quickTest(1000)">1000 Hz</button>
        <button class="test" onclick="quickTest(2000)">2000 Hz</button>
        <button class="test" onclick="quickTest(500)">500 Hz</button>
      </div>
    </div>
    
    <div class="section">
      <h2>Stream Playback</h2>
      <label>Stream URL</label>
      <input id="url" placeholder="http://example.com:8000/stream" />
      <label>Output Device</label>
      <select id="device">
        <option value="hw:0,0">PCM5102A (hw:0,0)</option>
        <option value="hw:2,0">USB Audio (hw:2,0)</option>
        <option value="default">Default</option>
      </select>
      <div class="row">
        <button onclick="startStream()">Start Stream</button>
        <button class="secondary" onclick="stopStream()">Stop</button>
      </div>
      <div class="status" id="streamStatus"></div>
    </div>
  </div>
  
  <script>
    const setStatus = (id, m) => document.getElementById(id).textContent = m;
    
    async function playTone(){
      const freq = parseFloat(document.getElementById('freq').value);
      const duration = parseFloat(document.getElementById('duration').value);
      const amp = parseFloat(document.getElementById('amplitude').value);
      setStatus('pcmStatus', 'Playing tone...');
      try{
        const r = await fetch('/api/pcm5102a/tone', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body:JSON.stringify({frequency:freq, duration:duration, amplitude:amp})
        });
        const j = await r.json();
        setStatus('pcmStatus', j.success ? `Playing ${freq}Hz tone...` : ('Failed: '+j.message));
        if(j.success) setTimeout(() => setStatus('pcmStatus', 'Tone complete'), duration*1000);
      }catch(e){ setStatus('pcmStatus', 'Error: '+e); }
    }
    
    async function playVoice(){
      setStatus('pcmStatus', 'Playing voice simulation...');
      try{
        const r = await fetch('/api/pcm5102a/voice', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body:JSON.stringify({text:'Hello PCM5102A DAC is working perfectly'})
        });
        const j = await r.json();
        setStatus('pcmStatus', j.success ? 'Playing voice...' : ('Failed: '+j.message));
      }catch(e){ setStatus('pcmStatus', 'Error: '+e); }
    }
    
    async function runTest(){
      setStatus('pcmStatus', 'Running full test...');
      try{
        const r = await fetch('/api/pcm5102a/test', {method:'POST'});
        const j = await r.json();
        setStatus('pcmStatus', j.success ? 'Test complete!' : ('Failed: '+j.message));
      }catch(e){ setStatus('pcmStatus', 'Error: '+e); }
    }
    
    function quickTest(freq){
      document.getElementById('freq').value = freq;
      playTone();
    }
    
    async function startStream(){
      const url = document.getElementById('url').value.trim();
      const device = document.getElementById('device').value;
      setStatus('streamStatus', 'Starting...');
      try{
        const r = await fetch('/api/start', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body:JSON.stringify({url:url, device:device})
        });
        const j = await r.json();
        setStatus('streamStatus', j.success ? 'Playing stream' : ('Failed: '+(j.message||'')));
      }catch(e){ setStatus('streamStatus', 'Error: '+e); }
    }
    
    async function stopStream(){
      setStatus('streamStatus', 'Stopping...');
      await fetch('/api/stop', {method:'POST'});
      setStatus('streamStatus', 'Stopped');
    }
  </script>
</body>
</html>
'''
}

