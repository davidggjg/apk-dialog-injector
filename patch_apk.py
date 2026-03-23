#!/usr/bin/env python3
import os, sys, json, shutil, subprocess, re
from pathlib import Path

CONFIG_FILE = "config.json"
APKTOOL_JAR = "apktool.jar"
WORK_DIR = "apk_work"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def run(cmd):
    print(f"[RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"Failed: {' '.join(cmd)}")
    return result

def decompile(apk, out):
    if os.path.exists(out):
        shutil.rmtree(out)
    run(["java", "-jar", APKTOOL_JAR, "d", apk, "-o", out, "-f"])

def recompile(src, out):
    run(["java", "-jar", APKTOOL_JAR, "b", src, "-o", out])

def sign(apk, signed):
    ks = "keystore.jks"
    if not os.path.exists(ks):
        run(["keytool", "-genkeypair", "-v",
             "-keystore", ks, "-alias", "patcher",
             "-keyalg", "RSA", "-keysize", "2048",
             "-validity", "10000",
             "-storepass", "patcher123",
             "-keypass", "patcher123",
             "-dname", "CN=Patcher,O=Patcher,C=US"])
    run(["apksigner", "sign",
         "--ks", ks,
         "--ks-pass", "pass:patcher123",
         "--key-pass", "pass:patcher123",
         "--out", signed, apk])

def find_main_smali(src):
    manifest = os.path.join(src, "AndroidManifest.xml")
    with open(manifest, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'<activity[^>]+android:name="([^"]+)"[^>]*>.*?MAIN.*?</activity>',
                      content, re.DOTALL)
    if not match:
        raise RuntimeError("Main activity not found in manifest")
    activity = match.group(1).replace(".", "/")
    if activity.startswith("/"):
        pkg = re.search(r'package="([^"]+)"', content).group(1).replace(".", "/")
        activity = pkg + activity
    for root, _, files in os.walk(os.path.join(src, "smali")):
        for f in files:
            if activity in os.path.join(root, f):
                return os.path.join(root, f)
    raise RuntimeError(f"Smali not found for {activity}")

def build_dialog_smali(cfg):
    t = cfg["title"].replace('"', '\\"')
    m = cfg["message"].replace('"', '\\"')
    b1 = cfg["button1"].replace('"', '\\"')
    b2 = cfg["button2"].replace('"', '\\"')
    b3 = cfg["button3"].replace('"', '\\"')
    return f"""
    # --- Injected Dialog Start ---
    new-instance v0, Landroid/app/AlertDialog$Builder;
    invoke-direct {{v0, p0}}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V
    const-string v1, "{t}"
    invoke-virtual {{v0, v1}}, Landroid/app/AlertDialog$Builder;->setTitle(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;
    const-string v1, "{m}"
    invoke-virtual {{v0, v1}}, Landroid/app/AlertDialog$Builder;->setMessage(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;
    const-string v1, "{b1}"
    const/4 v2, 0x0
    invoke-virtual {{v0, v1, v2}}, Landroid/app/AlertDialog$Builder;->setPositiveButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
    const-string v1, "{b2}"
    invoke-virtual {{v0, v1, v2}}, Landroid/app/AlertDialog$Builder;->setNeutralButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
    const-string v1, "{b3}"
    invoke-virtual {{v0, v1, v2}}, Landroid/app/AlertDialog$Builder;->setNegativeButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
    invoke-virtual {{v0}}, Landroid/app/AlertDialog$Builder;->show()Landroid/app/AlertDialog;
    # --- Injected Dialog End ---
"""

def inject_dialog(smali_path, cfg):
    with open(smali_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "Injected Dialog Start" in content:
        print("[!] Dialog already injected, skipping.")
        return
    pattern = r'(\.method public onCreate\(Landroid/os/Bundle;\)V.*?\.locals\s+\d+)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise RuntimeError("onCreate method not found")
    insert_pos = match.end()
    dialog_code = build_dialog_smali(cfg)
    new_content = content[:insert_pos] + dialog_code + content[insert_pos:]
    # Fix locals count
    locals_match = re.search(r'\.locals\s+(\d+)', match.group(0))
    if locals_match:
        old_count = int(locals_match.group(1))
        new_count = max(old_count, 3)
        new_content = new_content.replace(
            f".locals {old_count}", f".locals {new_count}", 1)
    with open(smali_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("[+] Dialog injected successfully!")

def remove_dialog(smali_path):
    with open(smali_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "Injected Dialog Start" not in content:
        print("[!] No injected dialog found.")
        return
    pattern = r'\n    # --- Injected Dialog Start ---.*?# --- Injected Dialog End ---\n'
    new_content = re.sub(pattern, '', content, flags=re.DOTALL)
    with open(smali_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("[+] Dialog removed successfully!")

def process(apk_path, mode):
    cfg = load_config()
    out_dir = WORK_DIR
    decompile(apk_path, out_dir)
    smali = find_main_smali(out_dir)
    print(f"[*] Main activity smali: {smali}")
    if mode == "inject":
        inject_dialog(smali, cfg)
    elif mode == "remove":
        remove_dialog(smali)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    unsigned = "output/patched_unsigned.apk"
    signed = "output/patched_signed.apk"
    os.makedirs("output", exist_ok=True)
    recompile(out_dir, unsigned)
    sign(unsigned, signed)
    print(f"\n[✓] Done! Output: {signed}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python patch_apk.py <apk_path> <inject|remove>")
        sys.exit(1)
    process(sys.argv[1], sys.argv[2])
