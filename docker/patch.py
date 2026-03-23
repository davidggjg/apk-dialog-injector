#!/usr/bin/env python3
import sys
import os
import subprocess
import shutil
import re

def parse_manifest(manifest_path):
    """מחזיר את שם ה-MainActivity מתוך AndroidManifest.xml."""
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        ns = "http://schemas.android.com/apk/res/android"
        for activity in root.iter("activity"):
            for intent_filter in activity.findall("intent-filter"):
                has_main = any(
                    a.get(f"{{{ns}}}name") == "android.intent.action.MAIN"
                    for a in intent_filter.findall("action")
                )
                has_launcher = any(
                    c.get(f"{{{ns}}}name") == "android.intent.category.LAUNCHER"
                    for c in intent_filter.findall("category")
                )
                if has_main and has_launcher:
                    name = activity.get(f"{{{ns}}}name")
                    if name:
                        return name
    except Exception as e:
        print(f"  [WARN] XML parse failed: {e}")

    # fallback: grep על הטקסט הגולמי
    print("  [INFO] Falling back to grep for MainActivity...")
    with open(manifest_path, "r", errors="replace") as f:
        content = f.read()
    match = re.search(r'android:name="([^"]+Activity[^"]*)"', content)
    if match:
        return match.group(1)
    return None


def find_smali_file(decompiled_dir, activity_name):
    """מחפש את ה-.smali בכל תיקיות smali* (תמיכה ב-multidex)."""
    rel_path = activity_name.lstrip(".").replace(".", "/") + ".smali"
    for entry in os.scandir(decompiled_dir):
        if entry.is_dir() and entry.name.startswith("smali"):
            candidate = os.path.join(entry.path, rel_path)
            if os.path.exists(candidate):
                return candidate
    return None


def inject_dialog_call(activity_file, title, message, image_url):
    with open(activity_file, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    method_start = -1
    method_end = -1
    depth = 0

    for i, line in enumerate(lines):
        # regex גמיש - מוצא onCreate ללא קשר ל-modifier
        if re.search(r'\.method\s+\S.*\sonCreate\(Landroid/os/Bundle;\)V', line):
            method_start = i
            depth = 1
            continue
        if method_start != -1:
            if ".method" in line:
                depth += 1
            if ".end method" in line:
                depth -= 1
                if depth == 0:
                    method_end = i
                    break

    if method_start == -1 or method_end == -1:
        print("  [ERROR] Could not find onCreate method in smali file.")
        for i, l in enumerate(lines):
            if "onCreate" in l:
                print(f"    line {i}: {l.rstrip()}")
        sys.exit(1)

    def smali_escape(s):
        return s.replace("\\", "\\\\").replace('"', '\\"').replace('\n', '\\n')

    injection = (
        "    # === INJECTED DIALOG START ===\n"
        f'    const-string v0, "{smali_escape(title)}"\n'
        f'    const-string v1, "{smali_escape(message)}"\n'
        f'    const-string v2, "{smali_escape(image_url)}"\n'
        "    invoke-static {p0, v0, v1, v2}, "
        "Lmy/app/DialogHelper;->showDialog("
        "Landroid/content/Context;"
        "Ljava/lang/String;"
        "Ljava/lang/String;"
        "Ljava/lang/String;)V\n"
        "    # === INJECTED DIALOG END ===\n"
    )

    inserted = False
    for i in range(method_start, method_end):
        if "return-void" in lines[i]:
            lines.insert(i, injection)
            inserted = True
            break

    if not inserted:
        lines.insert(method_end, injection)
        print("  [WARN] Inserted before .end method (no return-void found)")

    with open(activity_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"  [OK] Injected dialog call into {os.path.basename(activity_file)}")


def sign_apk(unsigned_apk, output_apk, work_dir):
    keystore_path = os.path.join(work_dir, "release.keystore")
    aligned_apk   = os.path.join(work_dir, "aligned.apk")

    if not os.path.exists(keystore_path):
        print("  [INFO] Generating keystore...")
        subprocess.run([
            "keytool", "-genkey", "-v",
            "-keystore", keystore_path,
            "-alias", "mykey",
            "-keyalg", "RSA", "-keysize", "2048",
            "-validity", "10000",
            "-dname", "CN=APKPatcher, OU=Dev, O=Dev, L=City, ST=State, C=US",
            "-storepass", "patchpass", "-keypass", "patchpass",
            "-noprompt"
        ], check=True)

    print("  [INFO] Running zipalign...")
    subprocess.run(["zipalign", "-v", "-p", "4", unsigned_apk, aligned_apk], check=True)

    print("  [INFO] Signing with apksigner...")
    subprocess.run([
        "apksigner", "sign",
        "--ks", keystore_path,
        "--ks-key-alias", "mykey",
        "--ks-pass", "pass:patchpass",
        "--key-pass", "pass:patchpass",
        "--out", output_apk,
        aligned_apk
    ], check=True)

    print("  [INFO] Verifying signature...")
    subprocess.run(["apksigner", "verify", "--verbose", output_apk], check=True)


def main():
    if len(sys.argv) < 5:
        print("Usage: patch.py <apk_path> <title> <message> <image_url>")
        sys.exit(1)

    apk_path  = sys.argv[1]
    title     = sys.argv[2]
    message   = sys.argv[3]
    image_url = sys.argv[4] or ""

    work_dir     = "/work"
    decompiled   = os.path.join(work_dir, "decompiled")
    unsigned_apk = os.path.join(work_dir, "unsigned.apk")
    output_apk   = os.path.join(work_dir, "patched.apk")

    print("\n[1/6] Decompiling APK...")
    if os.path.exists(decompiled):
        shutil.rmtree(decompiled)
    subprocess.run(["apktool", "d", apk_path, "-o", decompiled, "-f"], check=True)

    print("\n[2/6] Finding MainActivity...")
    manifest = os.path.join(decompiled, "AndroidManifest.xml")
    main_activity = parse_manifest(manifest)
    if not main_activity:
        print("  [ERROR] Could not find MainActivity")
        sys.exit(1)
    print(f"  [OK] Found: {main_activity}")

    print("\n[3/6] Locating smali file...")
    activity_file = find_smali_file(decompiled, main_activity)
    if not activity_file:
        print(f"  [ERROR] Smali file not found for {main_activity}")
        sys.exit(1)
    print(f"  [OK] Found: {activity_file}")

    print("\n[4/6] Copying DialogHelper smali files...")
    target_dir = os.path.join(decompiled, "smali", "my", "app")
    os.makedirs(target_dir, exist_ok=True)
    for fname in ["DialogHelper.smali", "DialogHelper$1.smali"]:
        shutil.copy(os.path.join("/smali_templates", fname),
                    os.path.join(target_dir, fname))
        print(f"  [OK] Copied {fname}")

    print("\n[5/6] Injecting dialog call into onCreate...")
    inject_dialog_call(activity_file, title, message, image_url)

    print("\n[6/6] Rebuilding and signing APK...")
    subprocess.run(["apktool", "b", decompiled, "-o", unsigned_apk], check=True)
    sign_apk(unsigned_apk, output_apk, work_dir)

    print(f"\n✅ Done! Patched APK saved to {output_apk}")


if __name__ == "__main__":
    main()
