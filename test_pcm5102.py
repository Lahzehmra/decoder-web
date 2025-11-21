import subprocess
import struct
import math
import tempfile
import os

sample_rate = 44100
duration = 2.0
freq = 440

# Generate tone
samples = []
for i in range(int(sample_rate * duration)):
    t = i / sample_rate
    val = 0.7 * math.sin(2 * math.pi * freq * t)
    samples.extend([int(val * 32767), int(val * 32767)])

audio_bytes = struct.pack('<' + 'h' * len(samples), *samples)

# Test with different devices
devices = ['hw:0,0', 'plughw:0,0', 'default']

for dev in devices:
    print(f'\nTesting device: {dev}')
    with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f:
        f.write(audio_bytes)
        temp_file = f.name
    
    result = subprocess.run([
        'aplay', '-D', dev, '-r', '44100', '-c', '2', '-f', 'S16_LE', temp_file
    ], capture_output=True, text=True, timeout=5)
    
    if result.returncode == 0:
        print(f'  [OK] {dev} - played successfully!')
    else:
        print(f'  [FAIL] {dev} - {result.stderr[:100]}')
    
    os.unlink(temp_file)
    os.system('sleep 0.5')

print('\nDone testing!')
