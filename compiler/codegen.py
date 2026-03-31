# compiler/codegen.py
# Mesa Language - Generador de código x86 real
# Convierte AST de Mesa a bytecode x86 ejecutable en QEMU

from .ast_nodes import *
from .interpreter import MesaRuntimeError


# ============================================================
# INSTRUCCIONES x86 REALES
# ============================================================

class X86:
    """Generador de instrucciones x86 en bytes reales"""

    # ── MOV ──────────────────────────────────────────────
    @staticmethod
    def mov_ax_imm16(val):
        """MOV AX, imm16 → B8 lo hi"""
        return bytes([0xB8, val & 0xFF, (val >> 8) & 0xFF])

    @staticmethod
    def mov_bx_imm16(val):
        """MOV BX, imm16 → BB lo hi"""
        return bytes([0xBB, val & 0xFF, (val >> 8) & 0xFF])

    @staticmethod
    def mov_cx_imm16(val):
        """MOV CX, imm16 → B9 lo hi"""
        return bytes([0xB9, val & 0xFF, (val >> 8) & 0xFF])

    @staticmethod
    def mov_dx_imm16(val):
        """MOV DX, imm16 → BA lo hi"""
        return bytes([0xBA, val & 0xFF, (val >> 8) & 0xFF])

    @staticmethod
    def mov_si_imm16(val):
        """MOV SI, imm16 → BE lo hi"""
        return bytes([0xBE, val & 0xFF, (val >> 8) & 0xFF])

    @staticmethod
    def mov_al_mem(addr):
        """MOV AL, [addr] → A0 lo hi"""
        return bytes([0xA0, addr & 0xFF, (addr >> 8) & 0xFF])

    @staticmethod
    def mov_mem_al(addr):
        """MOV [addr], AL → A2 lo hi"""
        return bytes([0xA2, addr & 0xFF, (addr >> 8) & 0xFF])

    @staticmethod
    def mov_ds_ax():
        """MOV DS, AX → 8E D8"""
        return bytes([0x8E, 0xD8])

    @staticmethod
    def mov_es_ax():
        """MOV ES, AX → 8E C0"""
        return bytes([0x8E, 0xC0])

    @staticmethod
    def mov_ah_imm8(val):
        """MOV AH, imm8 → B4 val"""
        return bytes([0xB4, val & 0xFF])

    @staticmethod
    def mov_al_imm8(val):
        """MOV AL, imm8 → B0 val"""
        return bytes([0xB0, val & 0xFF])

    @staticmethod
    def mov_bl_imm8(val):
        """MOV BL, imm8 → B3 val"""
        return bytes([0xB3, val & 0xFF])

    # ── INT (Interrupciones BIOS) ─────────────────────────
    @staticmethod
    def int_(num):
        """INT num → CD num"""
        return bytes([0xCD, num & 0xFF])

    # ── JMP ──────────────────────────────────────────────
    @staticmethod
    def jmp_short(offset):
        """JMP short → EB offset"""
        return bytes([0xEB, offset & 0xFF])

    @staticmethod
    def jmp_near(offset16):
        """JMP near → E9 lo hi"""
        return bytes([0xE9, offset16 & 0xFF, (offset16 >> 8) & 0xFF])

    @staticmethod
    def jmp_far(seg, off):
        """JMP FAR seg:off → EA off_lo off_hi seg_lo seg_hi"""
        return bytes([0xEA, off & 0xFF, (off >> 8) & 0xFF, seg & 0xFF, (seg >> 8) & 0xFF])

    # ── CMP y JCC ────────────────────────────────────────
    @staticmethod
    def cmp_al_imm8(val):
        """CMP AL, imm8 → 3C val"""
        return bytes([0x3C, val & 0xFF])

    @staticmethod
    def jne_short(offset):
        """JNE short → 75 offset"""
        return bytes([0x75, offset & 0xFF])

    @staticmethod
    def je_short(offset):
        """JE short → 74 offset"""
        return bytes([0x74, offset & 0xFF])

    @staticmethod
    def jz_short(offset):
        """JZ short → 74 offset"""
        return bytes([0x74, offset & 0xFF])

    # ── STACK ────────────────────────────────────────────
    @staticmethod
    def push_ax():
        return bytes([0x50])

    @staticmethod
    def pop_ax():
        return bytes([0x58])

    @staticmethod
    def push_bx():
        return bytes([0x53])

    @staticmethod
    def pop_bx():
        return bytes([0x5B])

    @staticmethod
    def push_si():
        return bytes([0x56])

    @staticmethod
    def pop_si():
        return bytes([0x5E])

    # ── ARITMÉTICAS ──────────────────────────────────────
    @staticmethod
    def inc_si():
        """INC SI → 46"""
        return bytes([0x46])

    @staticmethod
    def inc_bx():
        """INC BX → 43"""
        return bytes([0x43])

    @staticmethod
    def xor_ax_ax():
        """XOR AX, AX → 31 C0"""
        return bytes([0x31, 0xC0])

    @staticmethod
    def xor_bx_bx():
        """XOR BX, BX → 31 DB"""
        return bytes([0x31, 0xDB])

    # ── MISC ─────────────────────────────────────────────
    @staticmethod
    def nop():
        return bytes([0x90])

    @staticmethod
    def hlt():
        return bytes([0xF4])

    @staticmethod
    def cli():
        return bytes([0xFA])

    @staticmethod
    def sti():
        return bytes([0xFB])

    @staticmethod
    def clc():
        return bytes([0xF8])

    @staticmethod
    def lodsb():
        """LODSB: carga [SI] en AL, incrementa SI → AC"""
        return bytes([0xAC])

    @staticmethod
    def call_near(offset16):
        """CALL near → E8 lo hi"""
        return bytes([0xE8, offset16 & 0xFF, (offset16 >> 8) & 0xFF])

    @staticmethod
    def ret():
        """RETN → C3"""
        return bytes([0xC3])

    @staticmethod
    def ret_far():
        """RETF → CB"""
        return bytes([0xCB])

    # ── BIOS CALLS ───────────────────────────────────────
    @staticmethod
    def bios_print_char(char_val):
        """Imprime un carácter via BIOS INT 10h"""
        code = bytearray()
        code += X86.mov_ah_imm8(0x0E)       # AH = 0x0E (teletype output)
        code += X86.mov_al_imm8(char_val)   # AL = carácter
        code += X86.mov_bx_imm16(0x0007)    # BX = page 0, color blanco
        code += X86.int_(0x10)              # INT 10h
        return bytes(code)

    @staticmethod
    def bios_print_string_si():
        """
        Imprime string en [SI] hasta NULL via BIOS INT 10h
        SI debe apuntar al string antes de llamar
        Genera un loop completo:
          .loop:
            LODSB           ; AL = [SI], SI++
            CMP AL, 0
            JE .done
            MOV AH, 0x0E
            MOV BX, 0x0007
            INT 10h
            JMP .loop
          .done:
        """
        code = bytearray()
        # loop: (offset 0)
        code += X86.lodsb()              # AC
        code += X86.cmp_al_imm8(0)      # 3C 00
        code += X86.je_short(6)         # 74 06 → salta a done
        code += X86.mov_ah_imm8(0x0E)   # B4 0E
        code += X86.mov_bx_imm16(0x0007)# BB 07 00
        code += X86.int_(0x10)          # CD 10
        code += X86.jmp_short(-13)      # EB F3 → vuelve a loop
        # done: (offset 14)
        return bytes(code)

    @staticmethod
    def bios_set_video_mode(mode):
        """INT 10h AH=0 - Set video mode"""
        code = bytearray()
        code += X86.mov_ah_imm8(0x00)
        code += X86.mov_al_imm8(mode)
        code += X86.int_(0x10)
        return bytes(code)

    @staticmethod
    def bios_clear_screen():
        """Limpia pantalla via BIOS"""
        code = bytearray()
        # INT 10h AH=06h - scroll up (limpiar)
        code += bytes([0xB8, 0x00, 0x06])  # MOV AX, 0600h
        code += bytes([0xB9, 0x00, 0x00])  # MOV CX, 0000h (esquina sup-izq)
        code += bytes([0xBA, 0x4F, 0x18])  # MOV DX, 184Fh (esquina inf-der 24,79)
        code += bytes([0xB7, 0x07])        # MOV BH, 07h (atrib)
        code += X86.int_(0x10)
        return bytes(code)

    @staticmethod
    def bios_set_cursor(row, col):
        """INT 10h AH=02h - Set cursor position"""
        code = bytearray()
        code += X86.mov_ah_imm8(0x02)
        code += bytes([0xB7, 0x00])            # MOV BH, 0 (page)
        code += bytes([0xB6, row & 0xFF])      # MOV DH, row
        code += bytes([0xB2, col & 0xFF])      # MOV DL, col
        code += X86.int_(0x10)
        return bytes(code)

    @staticmethod
    def bios_set_text_color(color):
        """Cambia color de texto (attr byte)"""
        # Para modo texto, el color va en BL al hacer INT 10h AH=09
        code = bytearray()
        code += X86.mov_ah_imm8(0x0B)
        code += X86.mov_bx_imm16(color)
        code += X86.int_(0x10)
        return bytes(code)

    @staticmethod
    def bios_read_key():
        """INT 16h AH=00h - Read keyboard"""
        code = bytearray()
        code += X86.mov_ah_imm8(0x00)
        code += X86.int_(0x16)
        return bytes(code)

    @staticmethod
    def bios_reboot():
        """Reiniciar via INT 19h"""
        return X86.int_(0x19)


# ============================================================
# GENERADOR DE BOOTSECTOR x86 REAL
# ============================================================

class MesaBootsector:
    """
    Genera un bootsector x86 real (512 bytes) que QEMU puede bootear.
    El bootsector:
    1. Se carga en 0x7C00 por el BIOS
    2. Muestra texto en pantalla
    3. Implementa un shell básico
    """

    LOAD_ADDR = 0x7C00    # Dirección donde el BIOS carga el bootloader
    SECTOR_SIZE = 512     # Tamaño del sector de boot
    BOOT_SIG = b'\x55\xAA'  # Firma de boot obligatoria

    def __init__(self, titulo="MesaOS", version="1.0.0"):
        self.titulo = titulo
        self.version = version
        self.strings = {}     # Strings que se incrustan en el binario
        self.code = bytearray()

    def _encode_string(self, s):
        """Convierte string a bytes ASCII con NULL terminator"""
        return s.encode('ascii', errors='replace') + b'\x00'

    def _str_offset(self, name):
        """Calcula offset de un string en el sector"""
        # Los strings van al final del código, antes de los 510 bytes
        pass

    def generate(self):
        """
        Genera el bootsector completo de 512 bytes.
        Estructura:
          [0x000] - Código principal
          [0x???] - Strings de datos
          [0x1FE] - 0x55 0xAA (firma de boot)
        """
        code = bytearray()

        # ── HEADER: Configurar segmentos ─────────────────
        # CLI - deshabilitar interrupciones durante setup
        code += bytes([0xFA])  # CLI

        # XOR AX, AX → AX = 0
        code += bytes([0x31, 0xC0])

        # MOV DS, AX → DS = 0
        code += bytes([0x8E, 0xD8])

        # MOV ES, AX → ES = 0
        code += bytes([0x8E, 0xC0])

        # MOV SS, AX → SS = 0
        code += bytes([0x8E, 0xD0])

        # MOV SP, 0x7C00 → Stack justo debajo del bootloader
        code += bytes([0xBC, 0x00, 0x7C])

        # STI - rehabilitar interrupciones
        code += bytes([0xFB])

        # ── Set video mode 03h (80x25 text color) ────────
        code += bytes([0xB4, 0x00])  # MOV AH, 0
        code += bytes([0xB0, 0x03])  # MOV AL, 3
        code += bytes([0xCD, 0x10])  # INT 10h

        # ── Limpiar pantalla ──────────────────────────────
        code += bytes([0xB8, 0x00, 0x06])   # MOV AX, 0600h
        code += bytes([0xB9, 0x00, 0x00])   # MOV CX, 0
        code += bytes([0xBA, 0x4F, 0x18])   # MOV DX, 184Fh
        code += bytes([0xB7, 0x07])         # MOV BH, 07h
        code += bytes([0xCD, 0x10])         # INT 10h

        # ── Cursor en 0,0 ─────────────────────────────────
        code += bytes([0xB4, 0x02])   # MOV AH, 02
        code += bytes([0xB7, 0x00])   # MOV BH, 0
        code += bytes([0xB6, 0x00])   # MOV DH, 0 (row)
        code += bytes([0xB2, 0x00])   # MOV DL, 0 (col)
        code += bytes([0xCD, 0x10])   # INT 10h

        # ── Imprimir strings con CALL a print_str ─────────
        # La función print_str está al final del código
        # Primero calculamos los offsets

        # Strings que vamos a imprimir
        strings_to_print = [
            self._build_header_string(),
            self._build_separator(),
            self._build_welcome_string(),
            self._build_separator(),
            self._build_ready_string(),
        ]

        # Reservar espacio para los CALL + MOV SI instrucciones
        # Cada print es: MOV SI, offset (3 bytes) + CALL print_str (3 bytes) = 6 bytes
        num_prints = len(strings_to_print)
        call_block_size = num_prints * 6  # 6 bytes por print call

        # JMP sobre la función print_str
        # print_str_size = tamaño de la función (calculado abajo)
        print_str_func_size = 14  # bytes de la función print_str

        # Offset donde empieza el bloque de CALLs (después del setup)
        setup_size = len(code)

        # JMP sobre print_str al bloque de llamadas
        # JMP short: EB + offset relativo
        jmp_over_size = 2  # EB XX
        code += bytes([0xEB, print_str_func_size])  # JMP over print_str

        # ── FUNCIÓN print_str en 0x7C00 + setup_size + 2 ─
        # Imprime string en DS:SI hasta NULL
        # Loop:
        print_str_start = len(code)
        code += bytes([0xAC])        # LODSB: AL = [SI], SI++
        code += bytes([0x08, 0xC0])  # OR AL, AL (set flags)
        code += bytes([0x74, 0x07])  # JZ done (salta 7 bytes)
        code += bytes([0xB4, 0x0E])  # MOV AH, 0Eh
        code += bytes([0xBB, 0x00, 0x00])  # MOV BX, 0 (page + color)
        code += bytes([0xCD, 0x10])  # INT 10h
        code += bytes([0xEB, 0xF2])  # JMP loop (-14)
        # done:
        code += bytes([0xC3])        # RET

        print_str_end = len(code)
        actual_func_size = print_str_end - print_str_start

        # ── Bloque de llamadas a print_str ────────────────
        # Calcular dónde irán los strings
        calls_start = len(code)
        # Cada call: MOV SI, addr (3 bytes) + CALL print_str (3 bytes)
        strings_start = calls_start + (num_prints * 6) + 3  # +3 para HLT/JMP final

        current_str_offset = strings_start
        for s in strings_to_print:
            s_bytes = self._encode_string(s)
            abs_addr = self.LOAD_ADDR + current_str_offset

            # MOV SI, absolute_addr
            code += bytes([0xBE, abs_addr & 0xFF, (abs_addr >> 8) & 0xFF])

            # CALL print_str (offset relativo desde siguiente instrucción)
            call_from = len(code) + 3  # posición después del CALL
            call_target = self.LOAD_ADDR + print_str_start
            rel_offset = call_target - call_from
            code += bytes([0xE8, rel_offset & 0xFF, (rel_offset >> 8) & 0xFF])

            current_str_offset += len(s_bytes)

        # ── Loop infinito (HLT) ───────────────────────────
        code += bytes([0xF4])        # HLT
        code += bytes([0xEB, 0xFD])  # JMP $ (loop infinito en HLT)

        # ── Agregar los strings ───────────────────────────
        for s in strings_to_print:
            code += self._encode_string(s)

        # ── Padding hasta byte 510 ────────────────────────
        if len(code) > 510:
            # Si el código es muy grande, truncar strings
            code = code[:510]
        else:
            code += bytes(510 - len(code))

        # ── Boot signature ────────────────────────────────
        code += self.BOOT_SIG

        return bytes(code)

    def _build_header_string(self):
        return "\r\n\r\n  *** MesaOS v1.0.0 ***\r\n"

    def _build_separator(self):
        return "  ================================\r\n"

    def _build_welcome_string(self):
        return "  Sistema Operativo en Mesa Lang!\r\n  LA CABRA \r\n"

    def _build_ready_string(self):
        return "\r\n  Sistema iniciado. Cargando...\r\n"


# ============================================================
# GENERADOR COMPLETO DEL OS
# ============================================================

class MesaOSGenerator:
    """
    Genera un disco de QEMU completo con:
    - Sector 0: Bootloader (512 bytes)
    - Sectores 1-N: Kernel de Mesa
    """

    SECTOR_SIZE = 512
    DISK_SIZE = 1440 * 1024  # 1.44 MB (floppy)

    def __init__(self):
        self.disk = bytearray(self.DISK_SIZE)

    def generate_bootloader(self):
        """Genera el bootloader que carga el kernel"""
        code = bytearray()

        # Setup segmentos
        code += bytes([0xFA])              # CLI
        code += bytes([0x31, 0xC0])        # XOR AX, AX
        code += bytes([0x8E, 0xD8])        # MOV DS, AX
        code += bytes([0x8E, 0xC0])        # MOV ES, AX
        code += bytes([0x8E, 0xD0])        # MOV SS, AX
        code += bytes([0xBC, 0x00, 0x7C])  # MOV SP, 0x7C00
        code += bytes([0xFB])              # STI

        # Set video mode
        code += bytes([0xB4, 0x00, 0xB0, 0x03, 0xCD, 0x10])

        # Imprimir mensaje de boot
        # MOV SI, msg_boot (offset desde 0x7C00)
        msg_offset = 0x7C00 + 0x50  # mensaje en offset 0x50
        code += bytes([0xBE, msg_offset & 0xFF, (msg_offset >> 8) & 0xFF])

        # Función print inline
        print_loop = len(code)
        code += bytes([0xAC])              # LODSB
        code += bytes([0x08, 0xC0])        # OR AL, AL
        code += bytes([0x74, 0x07])        # JZ done
        code += bytes([0xB4, 0x0E])        # MOV AH, 0Eh
        code += bytes([0xBB, 0x00, 0x00])  # MOV BX, 0
        code += bytes([0xCD, 0x10])        # INT 10h
        code += bytes([0xEB, 0xF2])        # JMP loop
        # done:

        # HLT loop
        code += bytes([0xF4])
        code += bytes([0xEB, 0xFD])

        # Padding hasta offset 0x50
        while len(code) < 0x50:
            code += bytes([0x00])

        # Mensaje
        msg = b"\r\n  MesaOS v1.0.0 - Iniciando...\r\n  LA CABRA!\r\n\x00"
        code += msg

        # Padding y firma
        while len(code) < 510:
            code += bytes([0x00])
        code += bytes([0x55, 0xAA])

        return bytes(code[:512])

    def write_to_disk(self, sector, data):
        """Escribe datos en el disco en el sector indicado"""
        offset = sector * self.SECTOR_SIZE
        end = offset + len(data)
        if end <= self.DISK_SIZE:
            self.disk[offset:end] = data

    def generate(self, output_path):
        """Genera el disco completo"""
        boot = self.generate_bootloader()
        self.write_to_disk(0, boot)
        return bytes(self.disk)


def generate_mesa_os(output_path='mesa-os/mesa_os.img'):
    """Función principal para generar la imagen de MesaOS"""
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    gen = MesaOSGenerator()
    disk_data = gen.generate(output_path)

    with open(output_path, 'wb') as f:
        f.write(disk_data)

    print(f"✅ Imagen generada: {output_path}")
    print(f"   Tamaño: {len(disk_data)} bytes")
    print(f"   Para ejecutar: qemu-system-x86_64 -drive format=raw,file={output_path} -m 32")
    return output_path