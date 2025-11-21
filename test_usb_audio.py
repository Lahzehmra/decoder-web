#!/usr/bin/env python3
import subprocess
import struct
import math
import tempfile
import os

print('=== USB Audio Test ===')
print()

# Detect USB audio devices
print('Checking audio devices...')
result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
print(result.stdout)
print()

# Find USB audio device (card 2)
usb_device = 'hw:2,0'  # USB audio is card 2
print(f'Using USB audio device: {usb_device}')
print()

# Generate test tone
sample_rate = 44100
duration = 3.0
freq = 1000
amplitude = 0.9

print(f'Generating {freq}Hz tone for {duration}s...')
samples = []
for i in range(int(sample_rate * duration)):
    t = i / sample_rate
    val = amplitude * math.sin(2 * math.pi * freq * t)
    samples.extend([int(val * 32767), int(val * 32767)])

audio_bytes = struct.pack('<' + 'h' * len(samples), *samples)

with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f:
    temp_file = f.name
    f.write(audio_bytes)

print(f'Playing test tone on USB audio: {usb_device}')
print('You should hear a 1000Hz tone now!')
print()

result = subprocess.run([
    'aplay', '-D', usb_device, '-r', str(sample_rate),
    '-c', '2', '-f', 'S16_LE', '-v', temp_file
], capture_output=True, text=True, timeout=10)

if result.returncode == 0:
    print('[OK] USB audio test completed successfully!')
    print('If you heard sound, USB audio is working!')
else:
    print(f'Error: {result.stderr}')
    # Try plughw
    plug_device = 'plughw:2,0'
    print(f'\\nTrying {plug_device}...')
    result2 = subprocess.run([
        'aplay', '-D', plug_device, '-r', str(sample_rate),
        '-c', '2', temp_file
    ], capture_output=True, text=True, timeout=10)
    if result2.returncode == 0:
        print(f'[OK] USB audio works on {plug_device}!')
    else:
        print(f'Error on {plug_device}: {result2.stderr[:100]}')

os.unlink(temp_file)
print()
print('Test complete!')
