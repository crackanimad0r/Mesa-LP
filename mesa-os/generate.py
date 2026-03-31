#!/usr/bin/env python3
"""
MesaOS Generator - Imagen booteable para QEMU
Sin C. Sin ensamblador externo.
"""
import os
import sys
import struct

LOAD_ADDR = 0x7C00
DISK_SIZE = 1474560  # 1.44 MB
BOOT_SIG  = b'\x55\xAA'

# ============================================================
# STRINGS CORTOS (caben en 512 bytes)
# ============================================================

STR_BANNER = (
    "\r\n"
    " +-----------------------------+\r\n"
    " | MesaOS v1.0 - LA CABRA     |\r\n"
    " | Mesa Language OS - x86     |\r\n"
    " +-----------------------------+\r\n"
    " h=help  i=info  r=reboot\r\n"
    "\r\n"
)

STR_PROMPT  = "\r\nmesa> "
STR_HELP    = "\r\n h=help i=info r=reboot\r\n"
STR_INFO    = "\r\n MesaOS v1.0 | x86 | Mesa v2.2\r\n"
STR_UNKNOWN = "\r\n Cmd desconocido\r\n"

# ============================================================
# ENSAMBLADOR CON LABELS
# ============================================================

class Asm:
    def __init__(self, base):
        self.base   = base
        self.buf    = bytearray()
        self.labels = {}
        self.fixups = []

    def pos(self):
        return len(self.buf)

    def emit(self, b):
        self.buf += b

    def label(self, name):
        self.labels[name] = self.pos()

    def call(self, lbl):
        p = self.pos()
        self.emit(b'\xE8\x00\x00')
        self.fixups.append(('near', p, lbl))

    def jmp(self, lbl):
        p = self.pos()
        self.emit(b'\xEB\x00')
        self.fixups.append(('short', p, lbl))

    def je(self, lbl):
        p = self.pos()
        self.emit(b'\x74\x00')
        self.fixups.append(('short', p, lbl))

    def jne(self, lbl):
        p = self.pos()
        self.emit(b'\x75\x00')
        self.fixups.append(('short', p, lbl))

    def si(self, lbl):
        """MOV SI, abs_addr(label)"""
        p = self.pos()
        self.emit(b'\xBE\x00\x00')
        self.fixups.append(('si', p, lbl))

    def strz(self, name, text):
        self.label(name)
        self.emit(text.encode('latin-1', errors='replace') + b'\x00')

    def resolve(self):
        for kind, p, lbl in self.fixups:
            if isinstance(lbl, str):
                if lbl not in self.labels:
                    raise ValueError(f"Label no definido: '{lbl}'")
                t = self.labels[lbl]
            else:
                t = lbl

            if kind == 'near':
                rel = t - (p + 3)
                struct.pack_into('<h', self.buf, p + 1, rel)
            elif kind == 'short':
                rel = t - (p + 2)
                if not (-128 <= rel <= 127):
                    raise ValueError(f"JMP short fuera de rango: {rel} ('{lbl}')")
                self.buf[p + 1] = rel & 0xFF
            elif kind == 'si':
                abs_addr = self.base + t
                struct.pack_into('<H', self.buf, p + 1, abs_addr)

        return bytes(self.buf)


# ============================================================
# CONSTRUCCIÓN DEL BOOTLOADER
# ============================================================

def build():
    A = Asm(LOAD_ADDR)

    # ── SETUP ────────────────────────────────────────
    A.label('start')
    A.emit(b'\xFA')              # CLI
    A.emit(b'\x31\xC0')         # XOR AX, AX
    A.emit(b'\x8E\xD8')         # MOV DS, AX
    A.emit(b'\x8E\xC0')         # MOV ES, AX
    A.emit(b'\x8E\xD0')         # MOV SS, AX
    A.emit(b'\xBC\x00\x7C')     # MOV SP, 0x7C00
    A.emit(b'\xFB')             # STI

    # Video mode 03h (80x25 color text)
    A.emit(b'\xB4\x00')         # MOV AH, 0
    A.emit(b'\xB0\x03')         # MOV AL, 3
    A.emit(b'\xCD\x10')         # INT 10h

    # Limpiar pantalla
    A.emit(b'\xB8\x00\x06')     # MOV AX, 0600h
    A.emit(b'\xB7\x1E')         # MOV BH, 1Eh (azul+amarillo)
    A.emit(b'\xB9\x00\x00')     # MOV CX, 0
    A.emit(b'\xBA\x4F\x18')     # MOV DX, 184Fh
    A.emit(b'\xCD\x10')         # INT 10h

    # Cursor 0,0
    A.emit(b'\xB4\x02')         # MOV AH, 2
    A.emit(b'\xB7\x00')         # MOV BH, 0
    A.emit(b'\xB6\x00')         # MOV DH, 0
    A.emit(b'\xB2\x00')         # MOV DL, 0
    A.emit(b'\xCD\x10')         # INT 10h

    # Imprimir banner
    A.si('str_banner')
    A.call('print_str')

    # ── SHELL LOOP ───────────────────────────────────
    A.label('shell')
    A.si('str_prompt')
    A.call('print_str')
    A.call('read_key')

    # Echo
    A.emit(b'\x50')             # PUSH AX
    A.call('print_char')
    A.emit(b'\x58')             # POP AX

    # h = help
    A.emit(b'\x3C' + bytes([ord('h')]))   # CMP AL, 'h'
    A.je('do_help')

    # i = info
    A.emit(b'\x3C' + bytes([ord('i')]))
    A.je('do_info')

    # r = reboot
    A.emit(b'\x3C' + bytes([ord('r')]))
    A.je('do_reboot')

    # desconocido
    A.si('str_unknown')
    A.call('print_str')
    A.jmp('shell')

    A.label('do_help')
    A.si('str_help')
    A.call('print_str')
    A.jmp('shell')

    A.label('do_info')
    A.si('str_info')
    A.call('print_str')
    A.jmp('shell')

    A.label('do_reboot')
    A.emit(b'\xCD\x19')         # INT 19h (reboot)

    A.label('halt')
    A.emit(b'\xF4')             # HLT
    A.jmp('halt')

    # ── FUNCIÓN: print_str ───────────────────────────
    # Input: SI → string null-terminated
    A.label('print_str')
    A.emit(b'\x50')             # PUSH AX
    A.emit(b'\x53')             # PUSH BX
    A.label('ps_loop')
    A.emit(b'\xAC')             # LODSB
    A.emit(b'\x08\xC0')         # OR AL, AL
    A.je('ps_done')
    A.emit(b'\xB4\x0E')         # MOV AH, 0Eh
    A.emit(b'\xBB\x07\x00')     # MOV BX, 7
    A.emit(b'\xCD\x10')         # INT 10h
    A.jmp('ps_loop')
    A.label('ps_done')
    A.emit(b'\x5B')             # POP BX
    A.emit(b'\x58')             # POP AX
    A.emit(b'\xC3')             # RET

    # ── FUNCIÓN: print_char ──────────────────────────
    # Input: AL = char
    A.label('print_char')
    A.emit(b'\x53')             # PUSH BX
    A.emit(b'\xB4\x0E')         # MOV AH, 0Eh
    A.emit(b'\xBB\x07\x00')     # MOV BX, 7
    A.emit(b'\xCD\x10')         # INT 10h
    A.emit(b'\x5B')             # POP BX
    A.emit(b'\xC3')             # RET

    # ── FUNCIÓN: read_key ────────────────────────────
    # Output: AL = ASCII
    A.label('read_key')
    A.emit(b'\xB4\x00')         # MOV AH, 0
    A.emit(b'\xCD\x16')         # INT 16h
    A.emit(b'\xC3')             # RET

    # ── STRINGS ──────────────────────────────────────
    A.strz('str_banner',  STR_BANNER)
    A.strz('str_prompt',  STR_PROMPT)
    A.strz('str_help',    STR_HELP)
    A.strz('str_info',    STR_INFO)
    A.strz('str_unknown', STR_UNKNOWN)

    # ── RESOLVER ─────────────────────────────────────
    code = bytearray(A.resolve())

    size = len(code)
    print(f"   Código generado: {size} bytes (máx 510)")

    if size > 510:
        raise ValueError(
            f"Bootloader demasiado grande: {size} bytes.\n"
            f"   Acorta los strings {size - 510} bytes más."
        )

    # Padding + firma
    code += b'\x00' * (510 - size)
    code += BOOT_SIG
    assert len(code) == 512
    return bytes(code)


# ============================================================
# MAIN
# ============================================================

def main():
    out = 'mesa-os/mesa_os.img'
    os.makedirs('mesa-os', exist_ok=True)

    print("🐐 MesaOS Generator")
    print("=" * 42)
    print("Construyendo imagen de disco...")

    try:
        boot = build()
    except (ValueError, AssertionError) as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # Imagen completa de 1.44 MB
    disk = bytearray(DISK_SIZE)
    disk[0:512] = boot

    with open(out, 'wb') as f:
        f.write(disk)

    print(f"✅ Imagen: {out}")
    print(f"   Disco:  {DISK_SIZE // 1024} KB")
    print(f"   Boot:   512 bytes")
    print(f"   Firma:  0x{boot[510]:02X} 0x{boot[511]:02X} ✅")
    print()
    print("Primeros 32 bytes:")
    print("  " + ' '.join(f'{b:02X}' for b in boot[:32]))
    print()
    print("─" * 42)
    print("EJECUTAR EN QEMU:")
    print()
    print(f"  qemu-system-x86_64 \\")
    print(f"    -drive format=raw,file={out},if=floppy \\")
    print(f"    -m 32")
    print()
    print("Sin GUI (terminal):")
    print(f"  qemu-system-x86_64 \\")
    print(f"    -drive format=raw,file={out},if=floppy \\")
    print(f"    -m 32 -nographic")
    print()
    print("─" * 42)
    print("CONTROLES DENTRO DE QEMU:")
    print("  h → ayuda")
    print("  i → info del sistema")
    print("  r → reboot")
    print("  Ctrl+A X → salir (modo nographic)")
    print("─" * 42)


if __name__ == '__main__':
    main()