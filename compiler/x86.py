# compiler/x86.py
# Mesa Language - Ensamblador x86 integrado
# Permite generar binarios x86 directamente desde Mesa

import struct
import os

from attrs import define
from .interpreter import MesaRuntimeError


class MesaX86Assembler:
    """
    Ensamblador x86 de dos pasadas integrado en Mesa.
    Accesible desde código Mesa directamente.
    """

    def __init__(self):
        self.buf    = bytearray()
        self.labels = {}
        self.fixups = []

    def pos(self):
        return len(self.buf)

    def emit(self, data):
        if isinstance(data, list):
            self.buf += bytes(data)
        elif isinstance(data, bytes):
            self.buf += data
        elif isinstance(data, bytearray):
            self.buf += bytes(data)
        elif isinstance(data, int):
            self.buf += bytes([data & 0xFF])
        return self

    def label(self, name):
        self.labels[str(name)] = self.pos()
        return self

    def call_label(self, name):
        p = self.pos()
        self.buf += b'\xE8\x00\x00'
        self.fixups.append(('near', p, str(name)))
        return self

    def jmp_label(self, name):
        p = self.pos()
        self.buf += b'\xEB\x00'
        self.fixups.append(('short', p, str(name)))
        return self

    def je_label(self, name):
        p = self.pos()
        self.buf += b'\x74\x00'
        self.fixups.append(('short', p, str(name)))
        return self

    def jne_label(self, name):
        p = self.pos()
        self.buf += b'\x75\x00'
        self.fixups.append(('short', p, str(name)))
        return self

    def jl_label(self, name):
        p = self.pos()
        self.buf += b'\x7C\x00'
        self.fixups.append(('short', p, str(name)))
        return self

    def jg_label(self, name):
        p = self.pos()
        self.buf += b'\x7F\x00'
        self.fixups.append(('short', p, str(name)))
        return self

    def mov_si_label(self, base_addr, name):
        p = self.pos()
        self.buf += b'\xBE\x00\x00'
        self.fixups.append(('si', p, str(name), int(base_addr)))
        return self

    def string(self, name, text):
        self.label(name)
        self.buf += str(text).encode('latin-1', errors='replace') + b'\x00'
        return self

    def resolve(self):
        for fixup in self.fixups:
            kind = fixup[0]
            p    = fixup[1]
            lbl  = fixup[2]

            if lbl not in self.labels:
                raise MesaRuntimeError(f"x86: Label no definido: '{lbl}'")
            t = self.labels[lbl]

            if kind == 'near':
                rel = t - (p + 3)
                struct.pack_into('<h', self.buf, p + 1, rel)
            elif kind == 'short':
                rel = t - (p + 2)
                if not (-128 <= rel <= 127):
                    raise MesaRuntimeError(
                        f"x86: JMP short fuera de rango: {rel} bytes ('{lbl}')"
                    )
                self.buf[p + 1] = rel & 0xFF
            elif kind == 'si':
                base = fixup[3]
                abs_addr = base + t
                struct.pack_into('<H', self.buf, p + 1, abs_addr)

        return bytes(self.buf)

    def size(self):
        return len(self.buf)

    def get_bytes(self):
        return list(self.buf)

    def get_label_offset(self, name):
        return self.labels.get(str(name), -1)


def register_x86(interpreter):
    env = interpreter.env
    define = env.define

    # ══════════════════════════════════════════════════
    # CREAR ENSAMBLADOR
    # ══════════════════════════════════════════════════

    def x86_nuevo():
        """Crea un nuevo ensamblador x86"""
        return MesaX86Assembler()

    define('x86_nuevo', x86_nuevo)
    define('x86_new', x86_nuevo)
    define('asm_nuevo', x86_nuevo)
    define('asm_new', x86_nuevo)

    # ══════════════════════════════════════════════════
    # EMITIR BYTES RAW
    # ══════════════════════════════════════════════════

    def x86_bytes(asm, datos):
        """Emite bytes directamente"""
        if isinstance(datos, list):
            asm.emit(bytes([int(b) & 0xFF for b in datos]))
        elif isinstance(datos, int):
            asm.emit(bytes([datos & 0xFF]))
        return asm

    define('x86_bytes', x86_bytes)
    define('asm_bytes', x86_bytes)
    define('emitir', x86_bytes)
    define('emit', x86_bytes)

    # ══════════════════════════════════════════════════
    # LABELS
    # ══════════════════════════════════════════════════

    def x86_label(asm, nombre):
        """Define un label en la posición actual"""
        asm.label(nombre)
        return asm

    define('x86_label', x86_label)
    define('asm_label', x86_label)
    define('label', x86_label)
    define('etiqueta', x86_label)

    def x86_pos(asm):
        """Retorna la posición actual en bytes"""
        return asm.pos()

    define('x86_pos', x86_pos)
    define('asm_pos', x86_pos)
    define('posicion', x86_pos)

    # ══════════════════════════════════════════════════
    # INSTRUCCIONES x86 REALES
    # ══════════════════════════════════════════════════

    # ── Setup / Misc ──────────────────────────────────

    def x86_cli(asm):
        asm.emit(b'\xFA')
        return asm

    def x86_sti(asm):
        asm.emit(b'\xFB')
        return asm

    def x86_hlt(asm):
        asm.emit(b'\xF4')
        return asm

    def x86_nop(asm):
        asm.emit(b'\x90')
        return asm

    def x86_ret(asm):
        asm.emit(b'\xC3')
        return asm

    define('x86_cli', x86_cli); define('cli', x86_cli)
    define('x86_sti', x86_sti); define('sti', x86_sti)
    define('x86_hlt', x86_hlt); define('hlt', x86_hlt)
    define('x86_nop', x86_nop); define('nop', x86_nop)
    define('x86_ret', x86_ret); define('ret_asm', x86_ret)

    # ── MOV ───────────────────────────────────────────

    def x86_xor_ax_ax(asm):
        asm.emit(b'\x31\xC0')
        return asm

    def x86_xor_bx_bx(asm):
        asm.emit(b'\x31\xDB')
        return asm

    def x86_mov_ds_ax(asm):
        asm.emit(b'\x8E\xD8')
        return asm

    def x86_mov_es_ax(asm):
        asm.emit(b'\x8E\xC0')
        return asm

    def x86_mov_ss_ax(asm):
        asm.emit(b'\x8E\xD0')
        return asm

    def x86_mov_sp(asm, val):
        asm.emit(b'\xBC' + struct.pack('<H', int(val)))
        return asm

    def x86_mov_ax(asm, val):
        asm.emit(b'\xB8' + struct.pack('<H', int(val) & 0xFFFF))
        return asm

    def x86_mov_bx(asm, val):
        asm.emit(b'\xBB' + struct.pack('<H', int(val) & 0xFFFF))
        return asm

    def x86_mov_cx(asm, val):
        asm.emit(b'\xB9' + struct.pack('<H', int(val) & 0xFFFF))
        return asm

    def x86_mov_dx(asm, val):
        asm.emit(b'\xBA' + struct.pack('<H', int(val) & 0xFFFF))
        return asm

    def x86_mov_si(asm, val):
        asm.emit(b'\xBE' + struct.pack('<H', int(val) & 0xFFFF))
        return asm

    def x86_mov_ah(asm, val):
        asm.emit(b'\xB4' + bytes([int(val) & 0xFF]))
        return asm

    def x86_mov_al(asm, val):
        asm.emit(b'\xB0' + bytes([int(val) & 0xFF]))
        return asm

    def x86_mov_bh(asm, val):
        asm.emit(b'\xB7' + bytes([int(val) & 0xFF]))
        return asm

    def x86_mov_bl(asm, val):
        asm.emit(b'\xB3' + bytes([int(val) & 0xFF]))
        return asm

    def x86_mov_dh(asm, val):
        asm.emit(b'\xB6' + bytes([int(val) & 0xFF]))
        return asm

    def x86_mov_dl(asm, val):
        asm.emit(b'\xB2' + bytes([int(val) & 0xFF]))
        return asm

    define('x86_xor_ax_ax', x86_xor_ax_ax); define('xor_ax_ax', x86_xor_ax_ax)
    define('x86_xor_bx_bx', x86_xor_bx_bx); define('xor_bx_bx', x86_xor_bx_bx)
    define('x86_mov_ds_ax', x86_mov_ds_ax); define('mov_ds_ax', x86_mov_ds_ax)
    define('x86_mov_es_ax', x86_mov_es_ax); define('mov_es_ax', x86_mov_es_ax)
    define('x86_mov_ss_ax', x86_mov_ss_ax); define('mov_ss_ax', x86_mov_ss_ax)
    define('x86_mov_sp',    x86_mov_sp);    define('mov_sp', x86_mov_sp)
    define('x86_mov_ax',    x86_mov_ax);    define('mov_ax', x86_mov_ax)
    define('x86_mov_bx',    x86_mov_bx);    define('mov_bx', x86_mov_bx)
    define('x86_mov_cx',    x86_mov_cx);    define('mov_cx', x86_mov_cx)
    define('x86_mov_dx',    x86_mov_dx);    define('mov_dx', x86_mov_dx)
    define('x86_mov_si',    x86_mov_si);    define('mov_si', x86_mov_si)
    define('x86_mov_ah',    x86_mov_ah);    define('mov_ah', x86_mov_ah)
    define('x86_mov_al',    x86_mov_al);    define('mov_al', x86_mov_al)
    define('x86_mov_bh',    x86_mov_bh);    define('mov_bh', x86_mov_bh)
    define('x86_mov_bl',    x86_mov_bl);    define('mov_bl', x86_mov_bl)
    define('x86_mov_dh',    x86_mov_dh);    define('mov_dh', x86_mov_dh)
    define('x86_mov_dl',    x86_mov_dl);    define('mov_dl', x86_mov_dl)

    # ── STACK ─────────────────────────────────────────

    def x86_push_ax(asm): asm.emit(b'\x50'); return asm
    def x86_pop_ax(asm):  asm.emit(b'\x58'); return asm
    def x86_push_bx(asm): asm.emit(b'\x53'); return asm
    def x86_pop_bx(asm):  asm.emit(b'\x5B'); return asm
    def x86_push_cx(asm): asm.emit(b'\x51'); return asm
    def x86_pop_cx(asm):  asm.emit(b'\x59'); return asm
    def x86_push_si(asm): asm.emit(b'\x56'); return asm
    def x86_pop_si(asm):  asm.emit(b'\x5E'); return asm

    define('x86_push_ax', x86_push_ax); define('push_ax', x86_push_ax)
    define('x86_pop_ax',  x86_pop_ax);  define('pop_ax',  x86_pop_ax)
    define('x86_push_bx', x86_push_bx); define('push_bx', x86_push_bx)
    define('x86_pop_bx',  x86_pop_bx);  define('pop_bx',  x86_pop_bx)
    define('x86_push_cx', x86_push_cx); define('push_cx', x86_push_cx)
    define('x86_pop_cx',  x86_pop_cx);  define('pop_cx',  x86_pop_cx)
    define('x86_push_si', x86_push_si); define('push_si', x86_push_si)
    define('x86_pop_si',  x86_pop_si);  define('pop_si',  x86_pop_si)

    # ── INT ───────────────────────────────────────────

    def x86_int(asm, num):
        asm.emit(b'\xCD' + bytes([int(num) & 0xFF]))
        return asm

    define('x86_int', x86_int); define('int_asm', x86_int)

    # ── LODSB / OR / CMP ─────────────────────────────

    def x86_lodsb(asm):
        asm.emit(b'\xAC')
        return asm

    def x86_or_al_al(asm):
        asm.emit(b'\x08\xC0')
        return asm

    def x86_cmp_al(asm, val):
        asm.emit(b'\x3C' + bytes([int(val) & 0xFF]))
        return asm

    def x86_cmp_ah(asm, val):
        asm.emit(b'\x80\xFC' + bytes([int(val) & 0xFF]))
        return asm

    define('x86_lodsb',  x86_lodsb);  define('lodsb',  x86_lodsb)
    define('x86_or_al_al', x86_or_al_al); define('or_al_al', x86_or_al_al)
    define('x86_cmp_al', x86_cmp_al); define('cmp_al', x86_cmp_al)
    define('x86_cmp_ah', x86_cmp_ah); define('cmp_ah', x86_cmp_ah)

    # ── JUMPS CON LABELS ──────────────────────────────

    def x86_call(asm, lbl):
        asm.call_label(str(lbl))
        return asm

    def x86_jmp(asm, lbl):
        asm.jmp_label(str(lbl))
        return asm

    def x86_je(asm, lbl):
        asm.je_label(str(lbl))
        return asm

    def x86_jne(asm, lbl):
        asm.jne_label(str(lbl))
        return asm

    def x86_jl(asm, lbl):
        asm.jl_label(str(lbl))
        return asm

    def x86_jg(asm, lbl):
        asm.jg_label(str(lbl))
        return asm

    define('x86_call', x86_call); define('llamar', x86_call)
    define('x86_jmp',  x86_jmp);  define('saltar', x86_jmp)
    define('x86_je',   x86_je);   define('si_igual', x86_je)
    define('x86_jne',  x86_jne);  define('si_distinto', x86_jne)
    define('x86_jl',   x86_jl);   define('si_menor', x86_jl)
    define('x86_jg',   x86_jg);   define('si_mayor', x86_jg)
    define('jmp_a', x86_jmp)
    define('ir_a', x86_jmp)

    # ── MOV SI con label ──────────────────────────────

    def x86_si_label(asm, base, lbl):
        asm.mov_si_label(int(base), str(lbl))
        return asm

    define('x86_si_label', x86_si_label)
    define('si_label', x86_si_label)
    define('apuntar', x86_si_label)

    # ── STRING ────────────────────────────────────────

    def x86_string(asm, nombre, texto):
        asm.string(str(nombre), str(texto))
        return asm

    define('x86_string', x86_string)
    define('asm_string', x86_string)
    define('cadena', x86_string)

    # ── RESOLVER Y OBTENER BYTES ──────────────────────

    def x86_resolver(asm):
        """Resuelve todos los labels y retorna bytes"""
        try:
            result = asm.resolve()
            return list(result)
        except Exception as e:
            raise MesaRuntimeError(f"x86 resolver: {e}")

    define('x86_resolver', x86_resolver)
    define('resolver', x86_resolver)
    define('asm_resolver', x86_resolver)
    define('compilar', x86_resolver)

    def x86_tamanio(asm):
        return asm.size()

    define('x86_tamanio', x86_tamanio)
    define('x86_tamaño', x86_tamanio)
    define('asm_size', x86_tamanio)

    def x86_offset(asm, lbl):
        """Retorna el offset de un label"""
        return asm.get_label_offset(str(lbl))

    define('x86_offset', x86_offset)
    define('offset_de', x86_offset)

    # ══════════════════════════════════════════════════
    # GENERAR IMAGEN DE DISCO
    # ══════════════════════════════════════════════════

    def x86_bootsector(bytes_codigo):
        """
        Empaqueta bytes en un bootsector de 512 bytes válido.
        Agrega padding y firma 0x55 0xAA.
        """
        if isinstance(bytes_codigo, list):
            code = bytearray(bytes_codigo)
        else:
            code = bytearray(bytes_codigo)

        if len(code) > 510:
            raise MesaRuntimeError(
                f"Bootsector demasiado grande: {len(code)} bytes (máx 510)"
            )

        # Padding
        code += bytes(510 - len(code))
        # Firma
        code += bytes([0x55, 0xAA])

        return list(code)

    define('x86_bootsector', x86_bootsector)
    define('bootsector', x86_bootsector)
    define('empaquetar_boot', x86_bootsector)

    def x86_crear_imagen(boot_bytes, output_path, size_kb=1440):
        """Crea imagen de disco completa"""
        if isinstance(boot_bytes, list):
            boot = bytes(boot_bytes)
        else:
            boot = bytes(boot_bytes)

        if len(boot) != 512:
            raise MesaRuntimeError(f"Bootsector debe ser 512 bytes, tiene {len(boot)}")

        # Imagen de 1.44 MB
        disk_size = int(size_kb) * 1024
        disk = bytearray(disk_size)
        disk[0:512] = boot

        path = str(output_path)
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        with open(path, 'wb') as f:
            f.write(disk)

        return {
            'ok': True,
            'ruta': path,
            'tamanio': disk_size,
            'tamaño': disk_size,
        }

    define('x86_crear_imagen', x86_crear_imagen)
    define('crear_imagen', x86_crear_imagen)
    define('crear_disco', x86_crear_imagen)

    def x86_lanzar_qemu(imagen, args_extra=''):
        """Lanza QEMU con ventana gráfica"""
        import subprocess
        path = str(imagen)

        # Intentar con ventana gráfica primero
        cmd_gtk = [
            'qemu-system-x86_64',
            '-drive', f'format=raw,file={path},if=floppy',
            '-m', '32',
            '-name', 'MesaOS v1.0',
            '-display', 'gtk',
        ]

        cmd_sdl = [
            'qemu-system-x86_64',
            '-drive', f'format=raw,file={path},if=floppy',
            '-m', '32',
            '-name', 'MesaOS v1.0',
        ]

        cmd_i386 = [
            'qemu-system-i386',
            '-drive', f'format=raw,file={path}',
            '-m', '32',
            '-name', 'MesaOS v1.0',
        ]

        print(f"🚀 Lanzando MesaOS en QEMU...")
        print(f"   Imagen: {path}")
        print()

        # Intentar cada comando
        for cmd in [cmd_gtk, cmd_sdl, cmd_i386]:
            try:
                result = subprocess.run(
                    cmd,
                    check=False,
                    stderr=subprocess.PIPE
                )
                if result.returncode == 0 or b'Could not' not in (result.stderr or b''):
                    return True
            except FileNotFoundError:
                continue
            except Exception:
                continue

        # Fallback: nographic
        print("⚠️  Sin display gráfico, usando terminal...")
        print("   Ctrl+A X para salir")
        cmd_nographic = [
            'qemu-system-x86_64',
            '-drive', f'format=raw,file={path},if=floppy',
            '-m', '32',
            '-nographic',
        ]
        try:
            subprocess.run(cmd_nographic)
        except FileNotFoundError:
            raise MesaRuntimeError(
                "QEMU no instalado. Instala con: sudo apt install qemu-system-x86"
            )
        return True

    define('x86_lanzar_qemu', x86_lanzar_qemu)
    define('lanzar_qemu', x86_lanzar_qemu)
    define('qemu', x86_lanzar_qemu)
    define('boota', x86_lanzar_qemu)

    # ══════════════════════════════════════════════════
    # FUNCIONES BIOS PREDEFINIDAS (shortcuts)
    # ══════════════════════════════════════════════════

    def bios_print_str(asm, base_addr, str_label):
        """
        Shortcut: MOV SI, label + CALL print_str
        Requiere que 'print_str' esté definido en el asm
        """
        asm.mov_si_label(int(base_addr), str(str_label))
        asm.call_label('print_str')
        return asm

    define('bios_print_str', bios_print_str)
    define('imprimir_str', bios_print_str)

    def bios_set_video(asm, mode=0x03):
        """INT 10h AH=00 - Set video mode"""
        asm.emit(b'\xB4\x00')
        asm.emit(b'\xB0' + bytes([int(mode)]))
        asm.emit(b'\xCD\x10')
        return asm

    define('bios_set_video', bios_set_video)
    define('modo_video', bios_set_video)

    def bios_clear_screen(asm):
        """INT 10h AH=06 - Limpiar pantalla"""
        asm.emit(b'\xB8\x00\x06')   # MOV AX, 0600h
        asm.emit(b'\xB7\x1E')       # MOV BH, 1Eh (azul+amarillo)
        asm.emit(b'\xB9\x00\x00')   # MOV CX, 0
        asm.emit(b'\xBA\x4F\x18')   # MOV DX, 184Fh
        asm.emit(b'\xCD\x10')       # INT 10h
        return asm

    define('bios_limpiar_pantalla', bios_clear_screen)
    define('bios_clear_screen', bios_clear_screen)
    define('limpiar_pantalla', bios_clear_screen)

    def bios_cursor(asm, fila=0, col=0):
        """INT 10h AH=02 - Mover cursor"""
        asm.emit(b'\xB4\x02')
        asm.emit(b'\xB7\x00')
        asm.emit(b'\xB6' + bytes([int(fila)]))
        asm.emit(b'\xB2' + bytes([int(col)]))
        asm.emit(b'\xCD\x10')
        return asm

    define('bios_cursor', bios_cursor)
    define('mover_cursor', bios_cursor)

    def bios_setup_segmentos(asm):
        """Setup estándar de segmentos para bootloader"""
        asm.emit(b'\xFA')           # CLI
        asm.emit(b'\x31\xC0')       # XOR AX, AX
        asm.emit(b'\x8E\xD8')       # MOV DS, AX
        asm.emit(b'\x8E\xC0')       # MOV ES, AX
        asm.emit(b'\x8E\xD0')       # MOV SS, AX
        asm.emit(b'\xBC\x00\x7C')   # MOV SP, 0x7C00
        asm.emit(b'\xFB')           # STI
        return asm

    define('bios_setup_segmentos', bios_setup_segmentos)
    define('setup_boot', bios_setup_segmentos)
    define('iniciar_boot', bios_setup_segmentos)

    def bios_funcion_print_str(asm):
        """
        Inserta la función print_str estándar en el asm.
        Usa BIOS INT 10h AH=0Eh para imprimir.
        """
        asm.label('print_str')
        asm.emit(b'\x50')           # PUSH AX
        asm.emit(b'\x53')           # PUSH BX
        asm.label('print_str_loop')
        asm.emit(b'\xAC')           # LODSB
        asm.emit(b'\x08\xC0')       # OR AL, AL
        asm.je_label('print_str_done')
        asm.emit(b'\xB4\x0E')       # MOV AH, 0Eh
        asm.emit(b'\xBB\x07\x00')   # MOV BX, 7
        asm.emit(b'\xCD\x10')       # INT 10h
        asm.jmp_label('print_str_loop')
        asm.label('print_str_done')
        asm.emit(b'\x5B')           # POP BX
        asm.emit(b'\x58')           # POP AX
        asm.emit(b'\xC3')           # RET
        return asm

    define('bios_funcion_print_str', bios_funcion_print_str)
    define('insertar_print_str', bios_funcion_print_str)

    def bios_funcion_print_char(asm):
        """Inserta la función print_char"""
        asm.label('print_char')
        asm.emit(b'\x53')           # PUSH BX
        asm.emit(b'\xB4\x0E')       # MOV AH, 0Eh
        asm.emit(b'\xBB\x07\x00')   # MOV BX, 7
        asm.emit(b'\xCD\x10')       # INT 10h
        asm.emit(b'\x5B')           # POP BX
        asm.emit(b'\xC3')           # RET
        return asm

    define('bios_funcion_print_char', bios_funcion_print_char)
    define('insertar_print_char', bios_funcion_print_char)

    def bios_funcion_read_key(asm):
        """Inserta la función read_key"""
        asm.label('read_key')
        asm.emit(b'\xB4\x00')       # MOV AH, 0
        asm.emit(b'\xCD\x16')       # INT 16h
        asm.emit(b'\xC3')           # RET
        return asm

    define('bios_funcion_read_key', bios_funcion_read_key)
    define('insertar_read_key', bios_funcion_read_key)

    def bios_reboot(asm):
        """INT 19h - Reboot"""
        asm.emit(b'\xCD\x19')
        return asm

    define('bios_reboot', bios_reboot)
    define('reiniciar', bios_reboot)