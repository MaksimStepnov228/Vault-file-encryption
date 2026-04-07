import os
import sys
import argparse

# Crrently for windows

if sys.platform != "win32":
    print("Context menu integration is only supported on Windows.")
    sys.exit(1)

import winreg

# Right click menu features

ENTRIES = [
    ("Encrypt with WinVFE",    "--encrypt",    0),
    ("Decrypt with WinVFE",    "--decrypt",    1),
    ("Compress with WinVFE",   "--compress",   2),
    ("Decompress with WinVFE", "--decompress", 3),
]

REG_TARGETS = [
    r"*\shell",
    r"Directory\shell",
    r"Directory\Background\shell",
]

HKCR = winreg.HKEY_CLASSES_ROOT


def _exe_path(given: str | None) -> str:
    if given:
        return os.path.abspath(given)

    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "WinVFE.exe")


def install(exe: str):
    if not os.path.isfile(exe):
        sys.exit(1)

    for target in REG_TARGETS:
        for label, flag, _ in ENTRIES:
            key_path = rf"{target}\{label}\command"
            cmd = f'"{exe}" {flag} "%1"'
            try:
                with winreg.CreateKeyEx(HKCR, key_path,
                                        access=winreg.KEY_SET_VALUE) as k:
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, cmd)
                icon_key = rf"{target}\{label}"
                with winreg.OpenKey(HKCR, icon_key,
                                    access=winreg.KEY_SET_VALUE) as k:
                    winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, exe)

            except PermissionError:
                sys.exit(1)



def uninstall():
    for target in REG_TARGETS:
        for label, _, _ in ENTRIES:
            key_path = rf"{target}\{label}"
            try:
                _delete_key_tree(HKCR, key_path)
                print(f"  [-] {target}\\{label}")
            except FileNotFoundError:
                pass  # already gone
            except PermissionError:
                print(f"  [!] Permission denied — re-run as Administrator")
                sys.exit(1)

    print("\nUninstalled. WinVFE entries removed from context menu.")


def _delete_key_tree(hive, path: str):
    """Delete a registry key and all its subkeys (winreg has no recursive delete)."""
    try:
        with winreg.OpenKey(hive, path, access=winreg.KEY_ALL_ACCESS) as key:
            while True:
                try:
                    subkey = winreg.EnumKey(key, 0)
                    _delete_key_tree(hive, rf"{path}\{subkey}")
                except OSError:
                    break
        winreg.DeleteKey(hive, path)
    except FileNotFoundError:
        pass


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Install or remove WinVFE right-click menu entries.")
    sub = parser.add_subparsers(dest="command")

    inst = sub.add_parser("install", help="Add context menu entries")
    inst.add_argument("--exe", default=None,
                      help="Full path to WinVFE.exe (default: next to this script)")

    sub.add_parser("uninstall", help="Remove context menu entries")

    args = parser.parse_args()

    if args.command == "install":
        install(_exe_path(args.exe))
    elif args.command == "uninstall":
        uninstall()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()