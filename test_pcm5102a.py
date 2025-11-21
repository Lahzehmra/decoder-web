#!/usr/bin/env python3
"""
PCM5102A DAC Test Script
Test I2S audio output on PCM5102A chip
"""

import math
import struct
import subprocess
import tempfile
import os
import time

def test_pcm5102a():
    print("=" * 60)
    print("PCM5102A DAC Test")
    print("=" * 60)
    print()
    
    # Check devices
    print("[1] Checking audio devices...")
    result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
    print(result.stdout)
    
    # Test device hw:0,0 (PCM5102A)
    device = 'hw:0,0'
    sample_rate = 44100
    duration = 3.0
    frequency = 440
    
    print(f"[2] Generating {frequency} Hz tone for {duration} seconds...")
    
    # Generate sine wave
    num_samples = int(sample_rate * duration)
    samples = []
    
    for i in range(num_samples):
        t = float(i) / sample_rate
        value = 0.7 * math.sin(2.0 * math.pi * frequency * t)
        # Stereo
        samples.extend([value, value])
    
    # Convert to 16-bit PCM
    pcm_data = [int(s * 32767) for s in samples]
    audio_bytes = struct.pack('<' + 'h' * len(pcm_data), *pcm_data)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f:
        temp_file = f.name
        f.write(audio_bytes)
    
    print(f"[3] Playing on {device}...")
    print("    You should hear a 440 Hz tone (musical note A) now!")
    print()
    
    # Try playing
    result = subprocess.run([
        'aplay',
        '-D', device,
        '-r', str(sample_rate),
        '-c', '2',
        '-f', 'S16_LE',
        '-v',
        temp_file
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("[OK] Audio played successfully!")
    else:
        print(f"[ERROR] Failed to play audio")
        print(f"Error output: {result.stderr}")
        print()
        print("Trying with plughw:0,0...")
        
        result2 = subprocess.run([
            'aplay',
            '-D', 'plughw:0,0',
            '-r', str(sample_rate),
            '-c', '2',
            temp_file
        ], capture_output=True, text=True)
        
        if result2.returncode == 0:
            print("[OK] Audio played with plughw!")
        else:
            print(f"[ERROR] Still failed: {result2.stderr}")
    
    # Cleanup
    os.unlink(temp_file)
    
    print()
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)
    print()
    print("Troubleshooting if no sound:")
    print("1. Check I2S pin connections:")
    print("   - BCLK (Bit Clock) -> GPIO 18 (Pin 12)")
    print("   - LRCLK (Word Select) -> GPIO 19 (Pin 35)")
    print("   - DIN (Data) -> GPIO 21 (Pin 40)")
    print("   - VCC -> 3.3V or 5V")
    print("   - GND -> Ground")
    print()
    print("2. Check volume:")
    print("   alsamixer -c 0")
    print()
    print("3. Test with speaker-test:")
    print("   speaker-test -t sine -f 440 -c 2 -D hw:0,0")
    print()

if __name__ == '__main__':
    test_pcm5102a()

