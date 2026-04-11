# WinVFE (Vault file encryption)

WinVFE is a lightweight, modern encryption utility designed to keep your sensitive files private using AES-256-GCM.

Thank you very much to @Kflone5 for help with development!!

<img width="150" height="100" alt="Снимок экрана 2026-04-10 235136" src="https://github.com/user-attachments/assets/07280b3d-0764-4abb-a914-8a7987525b5d" />
<img width="150" height="100" alt="Снимок экрана 2026-04-10 235129" src="https://github.com/user-attachments/assets/875781bb-137f-4a53-8b0a-2b17fbab2a96" />
<img width="150" height="100" alt="Снимок экрана 2026-04-10 235112" src="https://github.com/user-attachments/assets/9a6d386d-254e-4c77-a5e9-8f44a1b64cc1" />
<img width="150" height="100" alt="Снимок экрана 2026-04-10 235102" src="https://github.com/user-attachments/assets/1451b839-0a78-48e9-a98f-0b9b6af7d837" />
<img width="150" height="100" alt="Снимок экрана 2026-04-10 235050" src="https://github.com/user-attachments/assets/40481b4b-422e-4f71-affe-cd1052d56661" />


Lates version:

**WinVFE v1.5.1**

_06.04.2026_

### New features
- **Right-click context menu** - Encrypt, Decrypt, Compress, Decompress with WinVFE now appear when right-clicking any file in Windows Explorer. Installed automatically via the Inno Setup installer.
- **Windows installer** - `WinVFE_Setup_v1.5.1.exe` built with Inno Setup. Installs to Program Files, writes registry keys, creates Start Menu and desktop shortcuts, includes a working uninstaller.
- **Encrypted ZIP support** - ZIP archives can now be password-protected using AES-256 encryption via `pyzipper`. Requires `pip install pyzipper`.
- **Open folder button** -After any compress/encrypt/decrypt operation, a button appears next to the result label to open the output folder directly in Explorer.
- **Progress popup** -Replaced the inline progress bar with a progress bar that appears during long operations.
- **Wizard** - Now wizard features app information.
- **New versions** - WinVFE now features new version checker, which will trigger a pop up if new release published on github.

**Compression changes**
- Removed the custom `.vz` format from the Compress tab -Compress now produces real `.zip` or `.7z` files that open in any archive tool.
- `.vz` files can still be decompressed (legacy support kept in `decompress_file`).
- Removed zlib, zstd, lz4 algorithm options from the Compress tab.
- Removed the metadata note feature from the Compress tab.

### Bug fixes
- Decompress browse filter now accepts `.zip` and `.7z` in addition to `.vz`.
- Multi-file ZIP compression no longer double-wraps (was bundling into a temp zip then recompressing into `.vz`).
- Output filenames now use the correct extension (`.zip` / `.7z`) instead of always `.vz`.
 
Algorithms:
```
# Encryption

AES-256-GCM
Blowfish-CBC

# Compression

zip
7z
vz
```


Beutiful UI: A clean interface with an easily navigatable and aesthetic UI, includes a wizard.

Portable: Available as a single standalone .exe for Windows.

Encrypt: Select a file, enter a strong password, and click "Encrypt File". This creates a .vault version of your file.
Decrypt: Select your .vault file, enter the original passphrase, and click "Decrypt File" to recover your data.

```
Language: Python 3.10_
Library: Tkinter / Cryptography_
Release Date: 29.03.2026_
```
