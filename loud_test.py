#!/usr/bin/env python3
import subprocess
import struct
import math
import tempfile
import os

# Generate louder test tone
sample_rate = 44100
duration = 3.0
freq = 440
amplitude = 0.9  # Louder

samples = []
for i in range(int(sample_rate * duration)):
    t = i / sample_rate
    val = amplitude * math.sin(2 * math.pi * freq * t)
    samples.extend([int(val * 32767), int(val * 32767)])

audio_bytes = struct.pack('<' + 'h' * len(samples), *samples)

with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f:
    temp_file = f.name
    f.write(audio_bytes)

print('Playing LOUD 440Hz tone for 3 seconds...')
print('Check: Are speakers connected to VOUTL+ and VOUTR+?')

result = subprocess.run([
    'aplay', '-D', 'hw:0,0', '-r', '44100', '-c', '2', '-f', 'S16_LE', temp_file
], capture_output=True, text=True)

if result.returncode == 0:
    print('[OK] Audio sent to PCM5102A')
else:
    print(f'Error: {result.stderr}')

os.unlink(temp_file)

