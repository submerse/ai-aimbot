#!/bin/bash
set -e

echo "=== Step 1: Installing arduino-cli and picocom ==="
sudo pacman -S arduino-cli picocom --noconfirm

echo "=== Step 2: Updating core index ==="
arduino-cli core update-index

echo "=== Step 3: Installing Arduino AVR core (Leonardo support) ==="
arduino-cli core install arduino:avr

echo "=== Step 4: Installing USB Host Shield library ==="
arduino-cli lib install "USB Host Shield Library 2.0"

echo "=== Step 5: Detecting connected boards ==="
arduino-cli board list

echo "=== Done! Paste the board list output so we can get your port. ==="
