#!/usr/bin/env python3
import time, socket, subprocess, os, sys, json
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
ROTATE = int(os.environ.get('OLED_ROTATE','3'))  # 3 = 270° portrait
BASE = os.path.dirname(os.path.abspath(__file__))
LEVELS_PATH = os.path.join(BASE, 'levels.json')


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


def get_status() -> str:
    # If player processes exist, assume Playing
    try:
        for name in ('cvlc','vlc'):
            if subprocess.run(['pgrep','-x',name], stdout=subprocess.DEVNULL).returncode == 0:
                return 'Playing'
        if subprocess.run(['pgrep','-x','ffmpeg'], stdout=subprocess.DEVNULL).returncode == 0:
            return 'Playing'
    except Exception:
        pass
    return 'Stopped'


def open_device():
    ctors = []
    if sh1107:
        ctors.append(sh1107)
    ctors.append(sh1106)
    ctors.extend([ssd1309, ssd1306, ssd1327])
    sizes = [(64,128), (128,64)]
    for addr in CANDIDATE_ADDRS:
        for w,h in sizes:
            try:
                serial = i2c(port=I2C_BUS, address=addr)
            except Exception:
                continue
            for ctor in ctors:
                try:
                    dev = ctor(serial, rotate=ROTATE, width=w, height=h)
                    with canvas(dev) as draw:
                        draw.rectangle(dev.bounding_box, outline=255, fill=0)
                    return dev
                except Exception:
                    continue
    raise RuntimeError('No supported OLED device found on I2C bus')


def read_levels():
    try:
        with open(LEVELS_PATH,'r',encoding='utf-8') as f:
            j=json.load(f)
        return j if (time.time()-j.get('t',0) < 0.8) else None
    except Exception:
        return None


def norm_from_db(db: float) -> float:
    # Map dBFS (-60..0) to 0..1
    if db is None:
        return 0.0
    return max(0.0, min(1.0, (db + 60.0) / 60.0))


def main():
    try:
        device = open_device()
    except Exception as e:
        time.sleep(2)
        sys.exit(1)

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    while True:
        ip = get_ip()
        status = get_status()
        j = read_levels() or {}
        L_db = j.get('L_db', -60.0)
        R_db = j.get('R_db', -60.0)
        Lp_db = j.get('L_peak_db', L_db)
        Rp_db = j.get('R_peak_db', R_db)
        L_n = norm_from_db(L_db)
        R_n = norm_from_db(R_db)
        with canvas(device) as draw:
            # Header
            draw.text((0, 0), f"IP: {ip}", fill=255, font=font)
            draw.text((0, 16), f"{status}", fill=255, font=font)
            # dB readout
            # Bars
            bw = device.width - 2
            lh = 10
            y0 = device.height - (2*lh + 6)
            # Outlines
            draw.rectangle((0, y0, bw, y0+lh), outline=255, fill=0)
            draw.rectangle((0, y0+lh+4, bw, y0+2*lh+4), outline=255, fill=0)
            # Fills
            draw.rectangle((1, y0+1, int(1+(bw-2)*L_n), y0+lh-1), outline=0, fill=255)
            draw.rectangle((1, y0+lh+5, int(1+(bw-2)*R_n), y0+2*lh+3), outline=0, fill=255)
        time.sleep(0.06)

if __name__ == '__main__':
    main()
