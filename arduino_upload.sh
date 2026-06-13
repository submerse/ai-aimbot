#!/usr/bin/env bash
set -e

FQBN="arduino:avr:leonardo"
PORT="/dev/ttyACM0"
SKETCH="/home/sub/claude/logitech_superlight_mouse"

BUILD_DIR="/tmp/arduino_build"
mkdir -p "$BUILD_DIR"
arduino-cli compile --fqbn "$FQBN" --output-dir "$BUILD_DIR" "$SKETCH"
sudo arduino-cli upload -p "$PORT" --fqbn "$FQBN" --input-dir "$BUILD_DIR" "$SKETCH"
