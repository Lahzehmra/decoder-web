#!/usr/bin/env python3
"""
PCM5102A I2S DAC Driver
Direct ALSA driver for PCM5102A
"""

import subprocess
import struct
import math
import tempfile
import os
import time

class PCM5102A_Driver:
    """Direct PCM5102A driver using ALSA"""
    
    def __init__(self, device='hw:0,0', sample_rate=44100, channels=2, format='S16_LE'):
        self.device = device
        self.sample_rate = sample_rate
        self.channels = channels
        self.format = format
    
    def play_tone(self, frequency, duration=1.0, amplitude=0.9):
        """Play a tone on PCM5102A"""
        num_samples = int(self.sample_rate * duration)
        samples = []
        
        print(f'Generating {frequency}Hz tone for {duration}s...')
        for i in range(num_samples):
            t = float(i) / self.sample_rate
            value = amplitude * math.sin(2.0 * math.pi * frequency * t)
            
            # Stereo
            for ch in range(self.channels):
                samples.append(int(value * 32767))
        
        # Convert to PCM bytes
        audio_bytes = struct.pack('<' + 'h' * len(samples), *samples)
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f:
            temp_file = f.name
            f.write(audio_bytes)
        
        # Play using aplay
        print(f'Playing on PCM5102A: {self.device}...')
        result = subprocess.run([
            'aplay', '-D', self.device,
            '-r', str(self.sample_rate),
            '-c', str(self.channels),
            '-f', self.format,
            '-v', temp_file
        ], capture_output=True, text=True, timeout=duration + 2)
        
        os.unlink(temp_file)
        
        if result.returncode == 0:
            print('[OK] Audio sent to PCM5102A')
            return True
        else:
            print(f'[ERROR] {result.stderr}')
            return False
    
    def test(self):
        """Test PCM5102A with different tones"""
        print('=== PCM5102A Driver Test ===')
        print(f'Device: {self.device}')
        print(f'Sample Rate: {self.sample_rate} Hz')
        print(f'Channels: {self.channels}')
        print(f'Format: {self.format}')
        print()
        
        # Test 1: Low frequency
        print('[Test 1/4] Playing 440Hz tone...')
        self.play_tone(440, 2.0, 0.95)
        time.sleep(0.5)
        
        # Test 2: Mid frequency
        print()
        print('[Test 2/4] Playing 1000Hz tone...')
        self.play_tone(1000, 2.0, 0.95)
        time.sleep(0.5)
        
        # Test 3: High frequency
        print()
        print('[Test 3/4] Playing 2000Hz tone...')
        self.play_tone(2000, 2.0, 0.95)
        time.sleep(0.5)
        
        # Test 4: Sweep
        print()
        print('[Test 4/4] Playing frequency sweep...')
        duration = 3.0
        num_samples = int(self.sample_rate * duration)
        samples = []
        
        for i in range(num_samples):
            t = float(i) / self.sample_rate
            progress = t / duration
            freq = 200 + (2000 - 200) * progress
            value = 0.95 * math.sin(2.0 * math.pi * freq * t)
            
            for ch in range(self.channels):
                samples.append(int(value * 32767))
        
        audio_bytes = struct.pack('<' + 'h' * len(samples), *samples)
        
        with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f:
            temp_file = f.name
            f.write(audio_bytes)
        
        print('Playing frequency sweep...')
        result = subprocess.run([
            'aplay', '-D', self.device,
            '-r', str(self.sample_rate),
            '-c', str(self.channels),
            '-f', self.format,
            '-v', temp_file
        ], capture_output=True, text=True, timeout=duration + 2)
        
        os.unlink(temp_file)
        
        if result.returncode == 0:
            print('[OK] Sweep sent to PCM5102A')
        
        print()
        print('Test complete!')
        print('If no sound, check output connections to VOUTL+ and VOUTR+')

if __name__ == '__main__':
    driver = PCM5102A_Driver('hw:0,0', 44100, 2, 'S16_LE')
    driver.test()

