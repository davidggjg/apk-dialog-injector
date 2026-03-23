#!/bin/bash
set -e

echo "========================================="
echo "APK Dialog Injector - Docker Container"
echo "========================================="

# בדיקה שקיבלנו את כל הפרמטרים
if [ $# -lt 4 ]; then
    echo "Usage: $0 <apk_path> <title> <message> <image_url>"
    exit 1
fi

APK_PATH="$1"
TITLE="$2"
MESSAGE="$3"
IMAGE_URL="$4"

echo "APK Path: $APK_PATH"
echo "Title: $TITLE"
echo "Message: $MESSAGE"
echo "Image URL: $IMAGE_URL"

# בדיקה שקובץ ה‑APK קיים
if [ ! -f "$APK_PATH" ]; then
    echo "Error: APK file not found at $APK_PATH"
    exit 1
fi

# הרצת הסקריפט הראשי
echo "Starting patching process..."
python3 /patch.py "$APK_PATH" "$TITLE" "$MESSAGE" "$IMAGE_URL"

echo "Done! Patched APK is at /work/patched.apk"
