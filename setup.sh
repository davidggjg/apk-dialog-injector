#!/bin/bash
echo "[*] Installing dependencies..."

# Java
apt-get install -y default-jdk

# apksigner
apt-get install -y apksigner

# Download apktool
wget -q https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar -O apktool.jar

echo "[✓] Setup complete!"
