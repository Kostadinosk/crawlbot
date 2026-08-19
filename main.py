import M5
from M5 import Display
import network
import socket
from machine import SoftI2C, Pin
import machine
import time
import gc
import os

# ==========================================
# 1. MOTOR DIRECTION CALIBRATION
# ==========================================
M1_DIR = 1   # Front Left
M2_DIR = -1  # Front Right
M3_DIR = 1   # Rear Left
M4_DIR = -1  # Rear Right

# Dynamic boot session token (invalidates old browser cookies on every reboot)
BOOT_TOKEN = str(time.ticks_ms())

# Non-blocking spin state machine variables
spin_dir = None
spin_count = 0
spin_state = "IDLE"
spin_timer = 0

# ==========================================
# 2. CREDENTIAL STORAGE SYSTEM
# ==========================================
saved_u = ""
saved_p = ""
is_setup = False

try:
    with open('creds.txt', 'r') as f:
        saved_u = f.readline().strip()
        saved_p = f.readline().strip()
        if saved_u and saved_p:
            is_setup = True
except:
    is_setup = False

# Robust query string parser
def parse_query(query_str):
    params = {}
    for part in query_str.split('&'):
        if '=' in part:
            k, v = part.split('=', 1)
            params[k] = v
    return params

# ==========================================
# 3. PRE-COMPILED HTML & HEADERS
# ==========================================
html_setup = """<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BugC2 Setup</title>
  <style>
    body { background: #121212; color: #fff; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; display: flex; flex-direction: column; min-height: 100vh; }
    .container { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px; }
    .panel { background: #1e1e1e; padding: 30px 20px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); width: 100%; max-width: 320px; box-sizing: border-box; }
    h2 { color: #ff3b30; text-transform: uppercase; letter-spacing: 2px; margin-top: 0; }
    p { color: #aaa; font-size: 14px; margin-bottom: 20px; }
    input { width: 90%; padding: 12px; margin: 10px 0; border: none; border-radius: 8px; background: #2a2a2a; color: white; font-size: 16px; text-align: center; outline: none; transition: 0.3s; }
    input:focus { box-shadow: 0 0 10px rgba(255, 59, 48, 0.5); }
    .btn { background: linear-gradient(90deg, #ff9500, #ff3b30); color: white; padding: 14px; font-size: 16px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; text-transform: uppercase; margin-top: 15px; width: 100%; }
    .btn:active { opacity: 0.7; }
    .credit { font-size: 10px; color: #555; font-weight: bold; letter-spacing: 2px; padding: 20px; text-transform: uppercase; }
  </style>
</head>
<body>
  <div class="container">
    <div class="panel">
      <h2>First-Time Setup</h2>
      <p>Create your admin credentials to lock the robot.</p>
      <form action="/setup" method="GET">
        <input name="u" placeholder="New Username" autocapitalize="none" autocorrect="off" required><br>
        <input type="password" name="p" placeholder="New Password" required><br>
        <button class="btn">SAVE & START</button>
      </form>
    </div>
  </div>
  <div class="credit">by KostadinosK</div>
</body>
</html>"""

html_login = """<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BugC2 Login</title>
  <style>
    body { background: #121212; color: #fff; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; display: flex; flex-direction: column; min-height: 100vh; }
    .container { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px; }
    .panel { background: #1e1e1e; padding: 30px 20px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); width: 100%; max-width: 320px; box-sizing: border-box; }
    h2 { color: #00e5ff; text-transform: uppercase; letter-spacing: 2px; margin-top: 0; }
    input { width: 90%; padding: 12px; margin: 10px 0; border: none; border-radius: 8px; background: #2a2a2a; color: white; font-size: 16px; text-align: center; outline: none; transition: 0.3s; }
    input:focus { box-shadow: 0 0 10px rgba(0, 229, 255, 0.5); }
    .btn { background: linear-gradient(90deg, #0072ff, #00e5ff); color: white; padding: 14px; font-size: 16px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; text-transform: uppercase; margin-top: 15px; width: 100%; }
    .btn:active { opacity: 0.7; }
    .credit { font-size: 10px; color: #555; font-weight: bold; letter-spacing: 2px; padding: 20px; text-transform: uppercase; }
  </style>
</head>
<body>
  <div class="container">
    <div class="panel">
      <h2>BugC2 Access</h2>
      <form action="/auth" method="GET">
        <input name="u" placeholder="Username" autocapitalize="none" autocorrect="off"><br>
        <input type="password" name="p" placeholder="Password"><br>
        <button class="btn">LOGIN</button>
      </form>
    </div>
  </div>
  <div class="credit">by KostadinosK</div>
</body>
</html>"""

html_app = """<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <title>BugC2 Controller</title>
  <style>
    body { background: #121212; color: #fff; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; display: flex; flex-direction: column; min-height: 100vh; touch-action: none; overflow: hidden; }
    .container { flex: 1; padding: 15px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    h2 { color: #00e5ff; text-transform: uppercase; letter-spacing: 2px; margin: 10px 0; font-size: 22px; }
    #joy-container { width: 180px; height: 180px; background: #1e1e1e; border-radius: 50%; position: relative; margin: 15px auto; box-shadow: inset 0 5px 15px rgba(0,0,0,0.8), 0 0 15px rgba(0, 229, 255, 0.1); border: 2px solid #2a2a2a; }
    #stick { width: 60px; height: 60px; background: linear-gradient(135deg, #00e5ff, #0072ff); border-radius: 50%; position: absolute; top: 60px; left: 60px; box-shadow: 0 5px 15px rgba(0,0,0,0.5); pointer-events: none; }
    .panel { background: #1e1e1e; padding: 15px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 100%; max-width: 320px; box-sizing: border-box; }
    select { width: 100%; padding: 10px; border-radius: 8px; background: #2a2a2a; color: white; border: 1px solid #333; margin-bottom: 15px; font-size: 16px; outline: none; text-align: center; }
    .btn-row { display: flex; gap: 10px; margin-bottom: 10px; }
    .spin-btn { flex: 1; background: transparent; color: #00e5ff; border: 2px solid #00e5ff; padding: 12px; border-radius: 8px; font-weight: bold; text-transform: uppercase; font-size: 13px; }
    .spin-btn:active { background: #00e5ff; color: #000; }
    .estop-btn { flex: 1; background: #ff3b30; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; letter-spacing: 1px; cursor: pointer; }
    .estop-btn:active { background: #cc2e26; }
    .rst-btn { flex: 1; background: #ff9500; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; letter-spacing: 1px; cursor: pointer; }
    .rst-btn:active { background: #cc7700; }
    .credit { font-size: 10px; color: #555; font-weight: bold; letter-spacing: 2px; padding: 15px; text-transform: uppercase; }
  </style>
</head>
<body>
  <div class="container">
    <h2>Controller</h2>
    <div id="joy-container"><div id="stick"></div></div>
    <div class="panel">
      <select id="spinCount">
        <option value="1">Spin 1 Time</option>
        <option value="2">Spin 2 Times</option>
        <option value="3">Spin 3 Times</option>
        <option value="4">Spin 4 Times</option>
        <option value="5">Spin 5 Times</option>
      </select>
      <div class="btn-row">
        <button class="spin-btn" onclick="sendSpin('CW')">Clockwise</button>
        <button class="spin-btn" onclick="sendSpin('CCW')">Counter-CW</button>
      </div>
      <div class="btn-row">
        <button class="estop-btn" onclick="emergencyStop()">E-STOP</button>
        <button class="rst-btn" onclick="sendAction('/RST')">REBOOT</button>
      </div>
    </div>
  </div>
  <div class="credit">by KostadinosK</div>

  <script>
    const container = document.getElementById('joy-container');
    const stick = document.getElementById('stick');
    let active = false, maxDist = 60, lastSend = 0;

    function handleStart(e) { active = true; moveStick(e); }
    function handleEnd() { 
        active = false; 
        stick.style.transform = `translate(0px, 0px)`;
        sendCmd(0, 0); 
    }
    
    function moveStick(e) {
        if (!active) return;
        e.preventDefault();
        let rect = container.getBoundingClientRect();
        let clientX = e.touches ? e.touches[0].clientX : e.clientX;
        let clientY = e.touches ? e.touches[0].clientY : e.clientY;
        
        let dx = clientX - rect.left - 90;
        let dy = clientY - rect.top - 90;
        let dist = Math.hypot(dx, dy);
        if (dist > maxDist) { dx = (dx / dist) * maxDist; dy = (dy / dist) * maxDist; }
        
        stick.style.transform = `translate(${dx}px, ${dy}px)`;
        
        let x = Math.round((dx / maxDist) * 100);
        let y = Math.round((-dy / maxDist) * 100);
        
        let now = Date.now();
        if (now - lastSend > 80) { 
            sendCmd(x, y);
            lastSend = now;
        }
    }
    
    function sendCmd(x, y) { fetch(`/joy?x=${x}&y=${y}`, {credentials: 'same-origin', cache: 'no-store'}).catch(()=>{}); }
    function sendSpin(dir) {
        let count = document.getElementById('spinCount').value;
        fetch(`/spin?dir=${dir}&count=${count}`, {credentials: 'same-origin', cache: 'no-store'}).catch(()=>{});
    }
    
    function emergencyStop() {
        fetch('/STOP', {credentials: 'same-origin', cache: 'no-store'}).catch(()=>{});
    }

    function sendAction(endpoint) {
        fetch(endpoint, {credentials: 'same-origin', cache: 'no-store'}).then(() => {
            if(endpoint === '/RST') { 
                document.body.innerHTML = "<div class='container'><h2>Rebooting...</h2></div><div class='credit'>by KostadinosK</div>";
                setTimeout(() => location.reload(), 2000); 
            }
        }).catch(()=>{});
    }

    container.addEventListener('mousedown', handleStart);
    document.addEventListener('mousemove', moveStick);
    document.addEventListener('mouseup', handleEnd);
    container.addEventListener('touchstart', handleStart, {passive: false});
    document.addEventListener('touchmove', moveStick, {passive: false});
    document.addEventListener('touchend', handleEnd);
  </script>
</body>
</html>"""

# Memory Safe Pre-Compilations with Dynamic Session Token
SETUP_BYTES = html_setup.encode('utf-8')
LOGIN_BYTES = html_login.encode('utf-8')
APP_BYTES = html_app.encode('utf-8')
HDR_OK = b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n'
HDR_REDIR = b'HTTP/1.1 302 Found\r\nLocation: /\r\nConnection: close\r\n\r\n'
HDR_AUTH = f'HTTP/1.1 302 Found\r\nLocation: /\r\nSet-Cookie: auth=granted_{BOOT_TOKEN}; Path=/;\r\nConnection: close\r\n\r\n'.encode('utf-8')
HDR_CMD = b'HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n'
HDR_CP = b'HTTP/1.1 302 Found\r\nLocation: http://192.168.4.1/\r\nConnection: close\r\n\r\n'

gc.collect() 

# ==========================================
# 4. INITIALIZE SYSTEM
# ==========================================
M5.begin()
M5.Power.setExtOutput(True)

def trigger_reboot():
    global spin_count, spin_state
    spin_count = 0
    spin_state = "IDLE"
    Display.clear(0x000000)
    Display.setCursor(0, 0)
    Display.setTextSize(3)
    Display.setTextColor(0xFF0000, 0x000000)
    Display.print("Rebooting")
    time.sleep(1.0)
    machine.reset()

Display.clear(0x000000)
Display.setCursor(0, 0)
Display.setTextSize(2)
Display.setTextColor(0x00E5FF, 0x000000) 
Display.print("BugC2 Ready\n\n")
Display.setTextColor(0xFFFFFF, 0x000000)
Display.print("Press 'M5'\nto Start OS")

Display.setTextSize(1)
Display.setTextColor(0x555555, 0x000000)
Display.setCursor(0, 225) 
Display.print("by KostadinosK")

bootsplash_waiting = True
held_frames = 0

while bootsplash_waiting:
    M5.update()
    
    if M5.BtnB.wasPressed():
        trigger_reboot()
    
    if M5.BtnA.isPressed():
        held_frames += 1
        if held_frames > 40: 
            try:
                os.remove('creds.txt')
            except:
                pass
            Display.clear(0xFF0000)
            Display.setCursor(0, 80)
            Display.setTextSize(2)
            Display.setTextColor(0xFFFFFF, 0xFF0000)
            Display.print(" CREDENTIALS\n WIPED!")
            time.sleep(2)
            machine.reset()
    else:
        if held_frames > 0 and held_frames <= 40:
            bootsplash_waiting = False 
        held_frames = 0
        
    time.sleep(0.05)

if not is_setup:
    Display.clear(0x000000)
    Display.setCursor(0, 10)
    Display.setTextSize(2)
    Display.setTextColor(0xFF9500, 0x000000)
    Display.print("First Setup\n\n")
    Display.setTextColor(0xFFFFFF, 0x000000)
    Display.print("AP BugC2_Robot\n\nSetup your\ncredentials")
    
    Display.setTextSize(1)
    Display.setTextColor(0x555555, 0x000000)
    Display.setCursor(0, 225)
    Display.print("by KostadinosK")
else:
    Display.clear(0x000000)
    Display.setCursor(0, 0)
    Display.setTextSize(2)
    Display.setTextColor(0xFFFFFF, 0x000000)
    Display.print("Booting...\n")

i2c = SoftI2C(scl=Pin(26), sda=Pin(0), freq=400000)
BUGC_ADDR = 0x38

def set_motors(m1, m2, m3, m4):
    try:
        m1 = int(max(-100, min(100, m1 * M1_DIR)))
        m2 = int(max(-100, min(100, m2 * M2_DIR)))
        m3 = int(max(-100, min(100, m3 * M3_DIR)))
        m4 = int(max(-100, min(100, m4 * M4_DIR)))
        data = bytearray([0x00, m1 & 0xFF, m2 & 0xFF, m3 & 0xFF, m4 & 0xFF])
        i2c.writeto(BUGC_ADDR, data)
    except:
        pass

# ==========================================
# 5. SETUP NETWORK SERVERS
# ==========================================
if is_setup:
    Display.setTextSize(2)
    Display.setTextColor(0xFFFFFF, 0x000000)
    Display.print("Starting AP...\n")

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid="BugC2_Robot", password="m5stack_bugc")

try:
    dns_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    dns_s.bind(('', 53))
    dns_s.setblocking(False)
except OSError:
    machine.reset()

try:
    http_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    http_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    http_s.bind(('', 80))
    http_s.listen(1)
    http_s.setblocking(False) 
except OSError:
    machine.reset() 

if is_setup:
    Display.clear(0x000000)
    Display.setCursor(0, 0)
    Display.setTextSize(2)
    Display.setTextColor(0xFFFFFF, 0x000000)
    Display.print("AP Active\nBugC2_Robot\nPortal ON\nReady to Drive")

    Display.setTextSize(1)
    Display.setTextColor(0x555555, 0x000000)
    Display.setCursor(0, 225)
    Display.print("by KostadinosK")

# ==========================================
# 6. MAIN SUPER-LOOP (NON-BLOCKING STATE MACHINE)
# ==========================================
while True:
    M5.update()
    
    if M5.BtnB.wasPressed():
        trigger_reboot()

    # Handle DNS
    try:
        dns_data, dns_addr = dns_s.recvfrom(1024)
        dns_res = dns_data[:2] + b'\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00' + dns_data[12:] + b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04\xc0\xa8\x04\x01'
        dns_s.sendto(dns_res, dns_addr)
    except:
        pass 

    # Handle Web Requests
    try:
        conn, addr = http_s.accept()
        try:
            conn.settimeout(0.05) 
            request = conn.recv(1024).decode('utf-8', 'ignore')
            
            if request:
                try:
                    req_line = request.split('\n')[0]
                    path_query = req_line.split(' ')[1]
                    path = path_query.split('?')[0]
                    query_str = path_query.split('?')[1] if '?' in path_query else ''
                    q_dict = parse_query(query_str)
                except:
                    path = '/'
                    q_dict = {}

                # INSTANT E-STOP OVERRIDE
                if path == '/STOP':
                    spin_count = 0
                    spin_state = "IDLE"
                    set_motors(0, 0, 0, 0)
                    try:
                        conn.send(HDR_CMD)
                    except:
                        pass
                    conn.close()
                    continue

                # Strict session check tied to current boot token
                is_auth = f'auth=granted_{BOOT_TOKEN}' in request
                
                if path == '/setup' and not is_setup:
                    new_u = q_dict.get('u', '')
                    new_p = q_dict.get('p', '')
                    
                    if new_u and new_p:
                        with open('creds.txt', 'w') as f:
                            f.write(new_u + '\n' + new_p)
                        os.sync() 
                        
                        conn.send(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n<html><body style="background:#121212;color:#fff;font-family:sans-serif;text-align:center;padding-top:50px"><h2>Credentials Saved! Rebooting...</h2></body></html>')
                        conn.close()
                        time.sleep(1.0)
                        machine.reset()
                    else:
                        conn.send(HDR_REDIR)
                        
                elif path == '/auth':
                    u = q_dict.get('u', '')
                    p = q_dict.get('p', '')
                    
                    if u == saved_u and p == saved_p:
                        conn.send(HDR_AUTH)
                    else:
                        conn.send(HDR_REDIR)
                        
                elif path == '/joy' and is_auth:
                    if spin_count == 0:
                        try:
                            x = int(q_dict.get('x', 0))
                            y = int(q_dict.get('y', 0))
                            
                            m1_speed = y + x
                            m2_speed = y - x
                            m3_speed = y - x
                            m4_speed = y + x
                            
                            maximum = max([abs(m1_speed), abs(m2_speed), abs(m3_speed), abs(m4_speed), 100])
                            set_motors(int((m1_speed / maximum) * 100), int((m2_speed / maximum) * 100), int((m3_speed / maximum) * 100), int((m4_speed / maximum) * 100))
                        except:
                            pass
                    conn.send(HDR_CMD)
                    
                elif path == '/spin' and is_auth:
                    spin_dir = q_dict.get('dir', 'CW')
                    try:
                        spin_count = max(1, min(5, int(q_dict.get('count', 1))))
                    except:
                        spin_count = 1
                    spin_state = "IDLE"
                    conn.send(HDR_CMD)
                    
                elif path == '/RST' and is_auth:
                    conn.send(HDR_CMD)
                    conn.close()
                    trigger_reboot()
                    
                elif path == '/':
                    conn.send(HDR_OK)
                    if not is_setup:
                        conn.send(SETUP_BYTES)
                    elif is_auth:
                        conn.send(APP_BYTES)
                    else:
                        conn.send(LOGIN_BYTES)
                        
                else:
                    conn.send(HDR_CP)
        except:
            pass
        finally:
            try:
                if conn:
                    conn.close()
            except:
                pass
    except:
        pass

    # ==========================================
    # NON-BLOCKING SPIN STATE MACHINE
    # ==========================================
    if spin_count > 0:
        now = time.ticks_ms()
        if spin_state == "IDLE":
            if spin_dir == 'CW':
                set_motors(60, -60, 60, -60)
            else:
                set_motors(-60, 60, -60, 60)
            spin_state = "TURNING"
            spin_timer = now
        elif spin_state == "TURNING":
            if time.ticks_diff(now, spin_timer) > 650:
                set_motors(0, 0, 0, 0)
                spin_state = "PAUSING"
                spin_timer = now
        elif spin_state == "PAUSING":
            if time.ticks_diff(now, spin_timer) > 150:
                spin_count -= 1
                if spin_count > 0:
                    spin_state = "IDLE"
                else:
                    spin_state = "IDLE"

    time.sleep(0.01)
