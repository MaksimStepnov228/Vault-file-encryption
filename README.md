# WinVFE (Vault file encryption)

WinVFE is a lightweight, modern encryption utility designed to keep your sensitive files private using AES-256-GCM.

Thank you very much to @Kflone5 for help with development!!

<img width="150" height="100" alt="Снимок экрана 2026-04-10 235136" src="https://github.com/user-attachments/assets/07280b3d-0764-4abb-a914-8a7987525b5d" />
<img width="150" height="100" alt="Снимок экрана 2026-04-10 235129" src="https://github.com/user-attachments/assets/875781bb-137f-4a53-8b0a-2b17fbab2a96" />
<img width="150" height="100" alt="Снимок экрана 2026-04-10 235112" src="https://github.com/user-attachments/assets/9a6d386d-254e-4c77-a5e9-8f44a1b64cc1" />
<img width="150" height="100" alt="Снимок экрана 2026-04-10 235102" src="https://github.com/user-attachments/assets/1451b839-0a78-48e9-a98f-0b9b6af7d837" />
<img width="150" height="100" alt="Снимок экрана 2026-04-10 235050" src="https://github.com/user-attachments/assets/40481b4b-422e-4f71-affe-cd1052d56661" />


Latest version:

**WinVFE v1.5.2**
_10.04.2026_

Other versions:

```
WinVFE 1.5.1 - 06.04.2026
WinVFE 1.1.5 Patch - 03.04.2026
WinVFE 1.1.0 - 01.04.2026
WinVFE 1.0.0 - 26.03.2026
```

# Features

File Encryption:

```
AES-256-GCM
ChaCha20-Poly1305
```

Data Compression:
```
Zip
Rar
7z
```

- Password-based key derivation (PBKDF2, 600k iterations)
- Smart encrypted File Handling
- Automatic filename preservation and guard
- Safe overwrite handling
- Metadata support for archives
- Multi thread encryption, decryption, compression, decompresison
- File shredding (overwrite files to remove any trace of their existance)
- Efficient handling of large files

Beutiful UI: A clean interface with an easily navigatable and aesthetic UI, includes a wizard.

Portable: Available as a single standalone .exe for Windows.

Encrypt: Select a file, enter a strong password, and click "Encrypt File". This creates a .vault version of your file.
Decrypt: Select your .vault file, enter the original passphrase, and click "Decrypt File" to recover your data.

```
Language: Python 3.10_
Library: Tkinter / Cryptography_
Release Date: 29.03.2026_
```
