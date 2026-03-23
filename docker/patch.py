#!/usr/bin/env python3
import sys
import os
import subprocess
import xml.etree.ElementTree as ET
import shutil
import re

def main():
    if len(sys.argv) < 5:
        print("Usage: patch.py <apk_path> <title> <message> <image_url>")
        sys.exit(1)

    apk_path = sys.argv[1]
    title = sys.argv[2]
    message = sys.argv[3]
    image_url = sys.argv[4]

    work_dir = "/work"
    decompiled_dir = os.path.join(work_dir, "decompiled")
    output_apk = os.path.join(work_dir, "patched.apk")
    keystore_path = os.path.join(work_dir, "my-release-key.keystore")

    # 1. פירוק ה‑APK
    print("[1] Decompiling APK...")
    subprocess.run(["apktool", "d", apk_path, "-o", decompiled_dir, "-f"], check=True)

    # 2. מציאת ה‑MainActivity
    print("[2] Finding MainActivity...")
    manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
    tree = ET.parse(manifest_path)
    root = tree.getroot()
    main_activity = None
    for activity in root.findall("activity"):
        intent_filters = activity.findall("intent-filter")
        for intent_filter in intent_filters:
            actions = intent_filter.findall("action")
            categories = intent_filter.findall("category")
            is_main = False
            for action in actions:
                if action.get("{http://schemas.android.com/apk/res/android}name") == "android.intent.action.MAIN":
                    is_main = True
            for category in categories:
                if category.get("{http://schemas.android.com/apk/res/android}name") == "android.intent.category.LAUNCHER":
                    is_main = True
            if is_main:
                main_activity = activity.get("{http://schemas.android.com/apk/res/android}name")
                break
        if main_activity:
            break

    if not main_activity:
        print("Error: Could not find MainActivity")
        sys.exit(1)

    print(f"MainActivity found: {main_activity}")

    # 3. המרת שם ה‑Activity לנתיב (דוטים לשלושים)
    activity_smali_path = main_activity.replace(".", "/") + ".smali"
    activity_file = os.path.join(decompiled_dir, "smali", activity_smali_path)
    if not os.path.exists(activity_file):
        print(f"Error: Activity smali file not found: {activity_file}")
        sys.exit(1)

    # 4. הוספת קבצי ה‑DialogHelper
    print("[3] Adding DialogHelper smali files...")
    target_smali_dir = os.path.join(decompiled_dir, "smali", "my", "app")
    os.makedirs(target_smali_dir, exist_ok=True)

    # העתקת קבצי התבנית עם החלפת placeholders
    with open("/smali_templates/DialogHelper.smali", "r") as f:
        helper_template = f.read()
    helper_content = helper_template
    # אין placeholders מיוחדים בקובץ הזה, אבל נוכל להוסיף בעתיד

    helper_path = os.path.join(target_smali_dir, "DialogHelper.smali")
    with open(helper_path, "w") as f:
        f.write(helper_content)

    with open("/smali_templates/DialogHelper$1.smali", "r") as f:
        onclick_template = f.read()
    onclick_path = os.path.join(target_smali_dir, "DialogHelper$1.smali")
    with open(onclick_path, "w") as f:
        f.write(onclick_template)

    # 5. הוספת הקריאה ל‑onCreate
    print("[4] Injecting dialog call into onCreate...")
    with open(activity_file, "r") as f:
        activity_lines = f.readlines()

    # נמצא את המתודה onCreate
    in_oncreate = False
    method_start = -1
    method_end = -1
    for i, line in enumerate(activity_lines):
        if ".method protected onCreate(Landroid/os/Bundle;)V" in line:
            method_start = i
            in_oncreate = True
        if in_oncreate and line.strip() == ".end method":
            method_end = i
            break

    if method_start == -1 or method_end == -1:
        print("Error: Could not find onCreate method")
        sys.exit(1)

    # נוסיף את הקריאה לפני ה‑return-void או לפני ה‑.end method
    injection_code = [
        "    # === INJECTED DIALOG ===\n",
        f'    const-string v0, "{title}"\n',
        f'    const-string v1, "{message}"\n',
        f'    const-string v2, "{image_url}"\n',
        "    invoke-static {p0, v0, v1, v2}, Lmy/app/DialogHelper;->showDialog(Landroid/content/Context;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V\n",
        "    # === END INJECTION ===\n"
    ]

    # נחפש return-void או סיום המתודה
    inserted = False
    for i in range(method_end - 1, method_start, -1):
        line = activity_lines[i]
        if "return-void" in line or ".end method" in line:
            activity_lines.insert(i, "".join(injection_code))
            inserted = True
            break

    if not inserted:
        print("Warning: Could not find good insertion point, adding before .end method")
        activity_lines.insert(method_end, "".join(injection_code))

    with open(activity_file, "w") as f:
        f.writelines(activity_lines)

    # 6. הרכבה מחדש
    print("[5] Rebuilding APK...")
    subprocess.run(["apktool", "b", decompiled_dir, "-o", output_apk], check=True)

    # 7. חתימה
    print("[6] Signing APK...")
    # יצירת keystore זמני
    if not os.path.exists(keystore_path):
        subprocess.run([
            "keytool", "-genkey", "-v", "-keystore", keystore_path,
            "-alias", "alias_name", "-keyalg", "RSA", "-keysize", "2048",
            "-validity", "10000", "-dname", "CN=Unknown, OU=Unknown, O=Unknown, L=Unknown, ST=Unknown, C=Unknown",
            "-storepass", "password", "-keypass", "password"
        ], check=True)

    # חתימה עם jarsigner
    subprocess.run([
        "jarsigner", "-verbose", "-sigalg", "SHA1withRSA", "-digestalg", "SHA1",
        "-keystore", keystore_path, output_apk, "alias_name",
        "-storepass", "password"
    ], check=True)

    print(f"[7] Done! Patched APK saved to {output_apk}")

if __name__ == "__main__":
    main()
