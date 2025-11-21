#!/usr/bin/env python3
import math
import struct
import subprocess
import tempfile
import os

# Generate 440 Hz tone for 2 seconds
sample_rate = 44100
duration = 2.0
frequency = 440
amplitude = 0.7

num_samples = int(sample_rate * duration)
samples = []

print(f'Generating {frequency} Hz tone for {duration} seconds...')
for i in range(num_samples):
    t = float(i) / sample_rate
    value = amplitude * math.sin(2.0 * math.pi * frequency * t)
    # Stereo
    samples.extend([value, value])

# Convert to 16-bit PCM
pcm_data = []
for sample in samples:
    pcm_data.append(int(sample * 32767))

audio_bytes = struct.pack('<' + 'h' * len(pcm_data), *pcm_data)

# Write to temp file
with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f:
    temp_file = f.name
    f.write(audio_bytes)

print(f'Playing on hw:0,0...')
print('You should hear a 440 Hz tone now!')

# Play using aplay
result = subprocess.run([
    'aplay',
    '-D', 'hw:0,0',
    '-r', '44100',
    '-c', '2',
    '-f', 'S16_LE',
    temp_file
], capture_output=True, text=True)

if result.returncode == 0:
    print('[OK] Audio played successfully!')
else:
    print(f'Error: {result.stderr}')
    print('Trying plughw:0,0...')
    result2 = subprocess.run([
        'aplay',
        '-D', 'plughw:0,0',
        '-r', '44100',
        '-c', '2',
        '-f', 'S16_LE',
        temp_file
    ], capture_output=True, text=True)
    if result2.returncode == 0:
        print('[OK] Audio played with plughw!')
    else:
        print(f'Error: {result2.stderr}')

os.unlink(temp_file)
print('Done!')

