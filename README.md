# Crawlbot 🤖🕷️

> A commercial-grade, secure, and crash-proof MicroPython operating system for the M5StickC PLUS2 and BugC2 robot. Features omnidirectional mecanum kinematics, a forced captive portal, and an asynchronous non-blocking state-machine architecture.

---

## 🚀 Features

* **Omnidirectional "Crab Walk":** Full mecanum wheel kinematics allowing fluid forward, backward, and side-to-side lateral strafing via a mobile joystick interface.
* **Non-Blocking Automated Spins:** Background state-machine-driven 360-degree rotation sequences (CW/CCW, 1 to 5 times) that execute smoothly without freezing the processor or locking up the web UI.
* **Instant Emergency Stop:** A high-priority, dedicated E-Stop mechanism that immediately cuts motor power and intercepts active loops on command.
* **Forced Captive Portal:** Built-in DNS server (Port 53) that intercepts network health checks to automatically force mobile devices to display the login or setup page upon connecting.
* **Persistent Flash Credentialing:** Securely stores custom admin usernames and passwords in local flash memory (`creds.txt`) with immediate filesystem synchronization (`os.sync()`).
* **Dynamic Boot-Session Tokens:** Generates a cryptographic session token on every system boot to invalidate old browser cookies and protect the control interface.
* **Secret Hardware Factory Reset:** A hidden backdoor mechanism to wipe stored credentials if you ever lock yourself out.

---

## 🛠️ Hardware Requirements

1. **M5Stack M5StickC PLUS2**
2. **M5Stack BugC2 Base** (equipped with mecanum wheels and I2C motor control at address `0x38`)

---

## 📦 Full Installation & Setup Guide

### Phase 1: Flashing the Base MicroPython Firmware
1. Download and install **M5Burner** on your computer.
2. Plug your M5StickC PLUS2 into your computer via USB-C.
3. Open M5Burner, select **M5StickC PLUS2**, download the **UIFlow2** (or base MicroPython) firmware, and click **Burn** to flash your device. If using UIFlow2 it is recommended to not fill the WiFi settings.

### Phase 2: Uploading Crawlbot Firmware
1. Open your preferred MicroPython IDE (such as **Thonny IDE** or VS Code with PyMakr).
2. Create or copy the `main.py` source script.
3. Save the file directly to the root directory of your M5StickC PLUS2 flash memory as **`main.py`**.

### Phase 3: First-Time Deployment & Setup
1. Snap your M5StickC PLUS2 securely onto the **BugC2 robot base** and power it on.
2. On the M5StickC PLUS2 screen, you will see the **Crawlbot Ready** bootsplash. Press the **M5 button** once to transition into the First-Time Setup state.
3. On your phone or laptop, open Wi-Fi settings and connect to the access point:
   * **Network Name:** `BugC2_Robot`
4. A captive portal page will automatically pop up. Enter your custom **Username** and **Password**, then click **Save & Start**.
5. The robot will commit your credentials to flash memory and automatically **reboot**.

---

## 🕹️ Controls & Navigation

* **Joystick:** Drag around the virtual joystick on your mobile web browser to drive omnidirectionally (crab walk).
* **Spin Menu:** Select 1 to 5 rotations from the dropdown and tap Clockwise or Counter-Clockwise to execute automated spins.
* **E-STOP:** Instantly halts all motor movement and cancels ongoing spin sequences mid-flight.
* **Physical Button B (Top Right):** Acts as a universal physical hard-reboot shortcut from any operational screen.
* **Secret Factory Reset:** If you ever forget your password, **hold down the front M5 button for 2 seconds** on the initial boot screen. The screen will flash red, wipe the `creds.txt` file, and restart the setup wizard.

---

## ⚠️ Disclaimer & Responsibility Deflection

> **SOFTWARE PROVIDED "AS-IS" — USE AT YOUR OWN RISK.**
> 
> The author, **KostadinosK**, explicitly disclaims all warranties, express or implied, including but not limited to fitness for a particular purpose and non-infringement. 
> 
> By flashing, running, or interacting with Crawlbot, you agree that **KostadinosK** holds zero liability for:
> * Your Crawlbot deciding it has achieved sentience and attempting to escape off a desk, table, or balcony.
> * Structural damage resulting from high-speed collisions with baseboards, furniture, pets, or skeptical family members.
> * Any rogue spinning sequences that may accidentally challenge local household appliances to a dance-off.
> * Accidental world domination, temporal paradoxes, or your robot mysteriously vanishing into the digital ether.
> 
> *If your robot breaks something, it's not the authors responsibility. Happy driving!*

---

**Developed with precision by KostadinosK**
