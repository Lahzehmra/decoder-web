#!/usr/bin/env python3
import time, socket, subprocess, os, sys
from PIL import ImageFont
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1309, ssd1327, sh1106
try:
    from luma.oled.device import sh1107
except Exception:
    sh1107 = None

I2C_BUS = 1
CANDIDATE_ADDRS = [0x3C, 0x3D]
ROTATE = int(os.environ.get('OLED_ROTATE','3'))  # default 270° portrait


def get_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and ip != '127.0.0.1':
            return ip
    except Exception:
        pass
    try:
        out = subprocess.check_output(['hostname','-I'], text=True).strip().split()
        for token in out:
            if token and token != '127.0.0.1':
                return token
    except Exception:
        pass
    return '0.0.0.0'


def get_player_status() -> str:
    try:
        for name in ('cvlc','vlc'):
            if subprocess.run(['pgrep','-x',name], stdout=subprocess.DEVNULL).returncode == 0:
                return 'Playing'
        ff = subprocess.run(['pgrep','-x','ffmpeg'], stdout=subprocess.DEVNULL).returncode == 0
        ap = subprocess.run(['pgrep','-x','aplay'], stdout=subprocess.DEVNULL).returncode == 0
        return 'Playing' if (ff and ap) else 'Stopped'
    except Exception:
        return 'Unknown'


def open_device():
    # Prefer SH1107/SH1106 for 64x128 panels; try width/height combos
    ctors = []
    if sh1107:
        ctors.append(sh1107)
    ctors.append(sh1106)
    ctors.extend([ssd1309, ssd1306, ssd1327])
    sizes = [(64,128), (128,64)]  # handle tall or wide variants
    for addr in CANDIDATE_ADDRS:
        for w,h in sizes:
            try:
                serial = i2c(port=I2C_BUS, address=addr)
            except Exception:
                continue
            for ctor in ctors:
                try:
                    dev = ctor(serial, rotate=ROTATE, width=w, height=h)
                    # quick draw test
                    with canvas(dev) as draw:
                        draw.rectangle(dev.bounding_box, outline=255, fill=0)
                    return dev
                except Exception:
                    continue
    raise RuntimeError('No supported OLED device found on I2C bus')


def main():
    try:
        device = open_device()
    except Exception as e:
        print('OLED init failed:', e)
        time.sleep(3)
        sys.exit(1)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    while True:
        ip = get_ip()
        status = get_player_status()
        with canvas(device) as draw:
            draw.text((0, 0), f"IP: {ip}", fill=255, font=font)
            draw.text((0, device.height//2 - 8), f"Status: {status}", fill=255, font=font)
        time.sleep(1.0)

if __name__ == '__main__':
    import socket
    main()
