# Arduino Logitech Pro Superlight - Progress Log

## Goal
Read mouse input from a Logitech Pro Superlight (via LIGHTSPEED USB receiver) using an
Arduino Leonardo + USB Host Shield 2.0, and also inject simulated mouse movements from code.

## Hardware
- Arduino Leonardo (ATmega32u4, native USB HID)
- USB Host Shield 2.0 (MAX3421E-based)
- Logitech Pro Superlight + LIGHTSPEED USB receiver

## Sketch Files
- `/home/sub/claude/logitech_raw_dumper/logitech_raw_dumper.ino` — dumps raw HID bytes to serial, upload this first to discover the receiver's report format
- `/home/sub/claude/logitech_superlight_mouse/logitech_superlight_mouse.ino` — full working sketch: forwards physical mouse to PC + allows simulated movement via serial commands

## Libraries Required
- USB Host Shield Library 2.0 (by Oleg Mazurov)
- Mouse (built-in for AVR/32u4 boards)

## Setup Script
- `/home/sub/claude/arduino_setup.sh` — installs arduino-cli, picocom, AVR core, and USB Host Shield library

## Progress

### Completed
- [x] Wrote raw dumper sketch
- [x] Wrote full mouse forwarder sketch
- [x] Fixed compile error: `HID*` → `USBHID*` in Parse() signature (Arduino HID class name conflict)
- [x] Installed arduino-cli and picocom via pacman
- [x] Installed arduino:avr core and USB Host Shield Library 2.0
- [x] Board detected: Arduino Leonardo on /dev/ttyACM0
- [x] Raw dumper compiled and uploaded successfully
- [x] Fixed permissions: `sudo usermod -aG uucp $USER` (use `sudo arduino-cli upload` until re-login takes effect)
- [x] Fixed library paths: Mouse and USB Host Shield libs moved to `~/Arduino/libraries/` (arduino-cli does not search `~/.arduino15/libraries/`)
- [x] Fixed upload with sudo: compile writes hex to `/tmp/arduino_build` via `--output-dir`, sudo upload reads it via `--input-dir` (avoids root/user cache mismatch)
- [x] Confirmed raw byte layout from LIGHTSPEED receiver (13-byte reports)
- [x] Updated main sketch parser to match actual byte layout
- [x] Added `M<dx>,<dy>\n` serial command to Arduino for precise movement injection
- [x] Updated `main_onnx.py` to send movement over serial instead of win32api.mouse_event
- [x] `main_onnx.py` prompts for COM port at startup

### Scripts
- `./arduino_upload.sh` — compiles to `/tmp/arduino_build` then sudo-uploads to /dev/ttyACM0
- `./arduino_monitor.sh` — opens picocom serial monitor at 115200 baud

### Next Steps
1. Re-upload main sketch: `./arduino_upload.sh`
2. On Windows machine: `pip install pyserial`
3. Run `main_onnx.py` — enter the Arduino's COM port when prompted (e.g. COM3)
4. Hold right mouse button (0x2) + X1 button (0x6) to activate aimbot movement

## Key Notes
- Arduino IDE 2.x wouldn't open on Arch (white screen hang) — using arduino-cli instead
- DBus errors in terminal are harmless noise from Electron
- Serial port on Arch is owned by the `uucp` group (not `dialout` like Ubuntu)
- The LIGHTSPEED receiver is a composite USB device — if nothing shows in serial monitor, change `SetReportParser(0, &Dumper)` to `SetReportParser(1, &Dumper)` in the raw dumper
- Simulated mouse movement: send w/a/s/d/c/r over serial to the main sketch
