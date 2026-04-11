import os
import sys
import ctypes
import winreg

# Script to add WinVFE to windows registry for right click operations.
# Updated as previosuly was only appearing advances options, now in right click immediately.
# Version 1.5.2 , Release: 10.04.2026

MENU_TITLE = "WinVFE Operations"
ENTRIES = [
    ("Encrypt",    "--encrypt"),
    ("Decrypt",    "--decrypt"),
    ("Compress",   "--compress"),
    ("Decompress", "--decompress"),
]

REG_TARGETS = [
    r"*\shell",
    r"Directory\shell",
    r"Directory\Background\shell",
]

HKCR = winreg.HKEY_CLASSES_ROOT

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 0
    )

def get_exe_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "WinVFE.exe")

def _delete_key_tree(hive, path):
    try:
        with winreg.OpenKey(hive, path, access=winreg.KEY_ALL_ACCESS) as key:
            while True:
                try:
                    subkey = winreg.EnumKey(key, 0)
                    _delete_key_tree(hive, rf"{path}\{subkey}")
                except OSError:
                    break
        winreg.DeleteKey(hive, path)
    except:
        pass

def install():
    exe = get_exe_path()
    for target in REG_TARGETS:
        _delete_key_tree(HKCR, rf"{target}\WinVFE")

    for target in REG_TARGETS:
        parent_path = rf"{target}\WinVFE"
        try:
            with winreg.CreateKeyEx(HKCR, parent_path, access=winreg.KEY_ALL_ACCESS) as p_key:
                winreg.SetValueEx(p_key, "MUIVerb", 0, winreg.REG_SZ, MENU_TITLE)
                winreg.SetValueEx(p_key, "Icon", 0, winreg.REG_SZ, exe)
                winreg.SetValueEx(p_key, "SubCommands", 0, winreg.REG_SZ, "")
                winreg.SetValueEx(p_key, "Position", 0, winreg.REG_SZ, "Top")

            for label, flag in ENTRIES:
                sub_path = rf"{parent_path}\shell\{label}"
                cmd_path = rf"{sub_path}\command"
                with winreg.CreateKeyEx(HKCR, sub_path, access=winreg.KEY_ALL_ACCESS) as s_key:
                    winreg.SetValueEx(s_key, "MUIVerb", 0, winreg.REG_SZ, label)
                arg = "%V" if "Background" in target else "%1"
                cmd = f'"{exe}" {flag} "{arg}"'
                with winreg.CreateKeyEx(HKCR, cmd_path, access=winreg.KEY_ALL_ACCESS) as c_key:
                    winreg.SetValueEx(c_key, "", 0, winreg.REG_SZ, cmd)
        except:
            continue

def main():
    if sys.platform != "win32":
        sys.exit()
    if not is_admin():
        run_as_admin()
        sys.exit()
    install()

if __name__ == "__main__":
    main()
