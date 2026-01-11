# Scanner Troubleshooting Guide

## Common Issues

### 1. "RuntimeError: no running event loop" (MQTT callback)

**Symptom:**
```
Exception in thread paho-mqtt-client-scanner-*:
RuntimeError: no running event loop
```

**Cause:** MQTT callbacks run in a separate thread and can't directly create async tasks.

**Status:** Fixed in latest commit - initial status publish removed from MQTT connect callback.

---

### 2. "[org.bluez.Error.NotReady] Resource Not Ready"

**Symptom:**
```
Scanner error: [org.bluez.Error.NotReady] Resource Not Ready
```

**Cause:** Bluetooth adapter is in an inconsistent state or needs reset.

**Solutions:**

#### Option 1: Reset the Bluetooth adapter
```bash
sudo hciconfig hci0 down
sudo hciconfig hci0 up
```

#### Option 2: Restart Bluetooth service
```bash
sudo systemctl restart bluetooth
```

#### Option 3: Power cycle the adapter (USB adapters)
```bash
# Unplug and replug the USB Bluetooth adapter
```

#### Option 4: Check adapter status
```bash
# List all adapters
hciconfig -a

# Should show something like:
# hci0:	Type: Primary  Bus: USB
# 	BD Address: AA:BB:CC:DD:EE:FF  ACL MTU: 1021:8  SCO MTU: 64:1
# 	UP RUNNING 
# 	...
```

If the adapter doesn't show "UP RUNNING", bring it up:
```bash
sudo hciconfig hci0 up
```

---

### 3. Permission Denied

**Symptom:**
```
PermissionError: [Errno 13] Permission denied
```

**Cause:** User doesn't have permission to access Bluetooth adapter.

**Solutions:**

#### Option 1: Add user to bluetooth group (recommended)
```bash
# Add your user to bluetooth group
sudo usermod -a -G bluetooth $USER

# Log out and log back in for changes to take effect
# Or run: newgrp bluetooth
```

#### Option 2: Run with sudo (not recommended for production)
```bash
sudo uv run python -m scanner
```

---

### 4. "No such file or directory: hci0"

**Symptom:**
```
FileNotFoundError: No such file or directory: '/sys/class/bluetooth/hci0'
```

**Cause:** Bluetooth adapter not found or wrong adapter name.

**Solutions:**

#### Check available adapters
```bash
hciconfig
# or
ls /sys/class/bluetooth/
```

#### Update config if using different adapter
Edit `config/scanner.yaml`:
```yaml
scanner:
  bluetooth_adapter: hci1  # Use correct adapter name
```

---

### 5. MQTT Connection Failed

**Symptom:**
```
Failed to connect to MQTT broker: [Errno 111] Connection refused
```

**Cause:** MQTT broker not accessible.

**Solutions:**

#### Test MQTT broker connectivity
```bash
# Test with mosquitto_pub
mosquitto_pub -h mqtt.shypan.st -t test -m "hello"

# Test with ping
ping mqtt.shypan.st
```

#### Use local broker for testing
```bash
# Install mosquitto
sudo apt install mosquitto mosquitto-clients

# Update config/scanner.yaml:
mqtt:
  broker: localhost
  port: 1883
```

---

### 6. No Advertisements Received

**Symptom:** Scanner runs but no advertisements are logged or published.

**Possible Causes & Solutions:**

#### No BLE devices nearby
- Turn on Bluetooth on your phone
- Move closer to BLE devices
- Try a BLE beacon or sensor

#### Enable debug logging
Edit `config/scanner.yaml`:
```yaml
logging:
  level: DEBUG
```

This will show when advertisements are received (even if not published).

#### Check MQTT subscription
In another terminal:
```bash
mosquitto_sub -h mqtt.shypan.st -t 'bt-mqtt/raw/#' -v
```

---

### 7. Scanner Crashes on Startup

**Symptom:** Scanner immediately exits with error.

**Possible Causes:**

#### Missing configuration file
```
Error: No configuration file found
```

**Solution:** Create `config/scanner.yaml`:
```bash
cp config/scanner.example.yaml config/scanner.yaml
nano config/scanner.yaml
```

#### Invalid YAML syntax
```
yaml.scanner.ScannerError: ...
```

**Solution:** Validate your YAML:
```bash
# Install yamllint
pip install yamllint

# Check config file
yamllint config/scanner.yaml
```

---

## Debugging Steps

### 1. Enable Debug Logging

Edit `config/scanner.yaml`:
```yaml
logging:
  level: DEBUG
  format: text  # Easier to read than JSON for debugging
```

### 2. Check Bluetooth Status

```bash
# Check if Bluetooth is enabled
sudo systemctl status bluetooth

# Check adapter status
hciconfig -a

# Scan for devices manually
sudo hcitool lescan
# Press Ctrl+C to stop
```

### 3. Monitor MQTT Messages

```bash
# Subscribe to all topics
mosquitto_sub -h mqtt.shypan.st -t '#' -v

# Subscribe to just scanner messages
mosquitto_sub -h mqtt.shypan.st -t 'bt-mqtt/raw/#' -v
```

### 4. Test Components Individually

#### Test MQTT publishing
```bash
# Publish a test message
mosquitto_pub -h mqtt.shypan.st -t 'bt-mqtt/raw/test' -m '{"test": true}'

# Subscribe to see it
mosquitto_sub -h mqtt.shypan.st -t 'bt-mqtt/raw/test'
```

#### Test BLE scanning with bleak
```python
import asyncio
from bleak import BleakScanner

async def scan():
    devices = await BleakScanner.discover(timeout=5.0)
    for device in devices:
        print(f"{device.address}: {device.name} (RSSI: {device.rssi})")

asyncio.run(scan())
```

---

## System Requirements

### Minimum Requirements
- Python 3.11+
- Bluetooth 4.0+ adapter
- Linux with BlueZ stack
- Network access to MQTT broker

### Tested Platforms
- Raspberry Pi Zero W / Zero 2 W
- Raspberry Pi 3/4/5
- Ubuntu 22.04+ (x86_64)
- Debian 12+

### Known Issues
- **macOS:** bleak works but may have permission dialogs
- **Windows:** Not officially supported (BlueZ required)
- **Python 3.13:** Works but may have threading warnings (harmless)

---

## Getting Help

### Check Logs
```bash
# If running with systemd
journalctl -u bt-mqtt-scanner -f

# If running directly
# Logs are printed to stdout/stderr
```

### Include in Bug Reports
1. Scanner version: Check `pyproject.toml`
2. Python version: `python --version`
3. OS version: `uname -a`
4. Bluetooth adapter: `hciconfig -a`
5. Full error output with DEBUG logging
6. Configuration file (sanitize sensitive data)

### Useful Commands
```bash
# Check Python version
python --version

# Check installed packages
uv pip list

# Check Bluetooth service
sudo systemctl status bluetooth

# Check kernel modules
lsmod | grep bluetooth

# Check USB devices (for USB adapters)
lsusb
```
