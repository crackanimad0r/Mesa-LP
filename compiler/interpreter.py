import sys
import re
import math
import time
import random
import operator as op
import ctypes
from ctypes import c_int, c_float, c_double, c_char, c_void_p, POINTER, cast, sizeof, memmove, memset as c_memset
from .ast_nodes import *


class MesaError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class MesaRuntimeError(MesaError):
    pass


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class ThrowException(Exception):
    def __init__(self, value):
        self.value = value


class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}
        self.types = {}

    def define(self, n, v):
        self.vars[n] = v

    def get(self, n):
        if n in self.vars:
            return self.vars[n]
        if self.parent:
            return self.parent.get(n)
        raise MesaRuntimeError(f"Variable '{n}' no definida")

    def set(self, n, v):
        if n in self.vars:
            self.vars[n] = v
        elif self.parent:
            try:
                self.parent.set(n, v)
                return
            except MesaRuntimeError:
                pass
        self.vars[n] = v

    def define_type(self, n, t):
        self.types[n] = t

    def get_type(self, n):
        if n in self.types:
            return self.types[n]
        if self.parent:
            return self.parent.get_type(n)
        raise MesaRuntimeError(f"Tipo '{n}' no definido")


class MesaFunc:
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def __repr__(self):
        return f"<fn {self.name}>"


class MesaShape:
    def __init__(self, name, fields, methods):
        self.name = name
        self.fields = fields
        self.methods = methods

    def __repr__(self):
        return f"<shape {self.name}>"


class MesaInstance:
    def __init__(self, shape, fields):
        self.shape = shape
        self.fields = fields

    def get(self, n):
        if n in self.fields:
            return self.fields[n]
        raise MesaRuntimeError(f"Campo '{n}' no existe en {self.shape.name}")

    def set(self, n, v):
        self.fields[n] = v

    def get_method(self, n):
        return self.shape.methods.get(n)

    def __repr__(self):
        fs = ', '.join(f'{k}: {v}' for k, v in self.fields.items())
        return f"{self.shape.name}{{{fs}}}"


class MesaResult:
    def __init__(self, is_ok, value, error=None):
        self.is_ok = is_ok
        self.value = value
        self.error = error

    @staticmethod
    def ok(v):
        return MesaResult(True, v)

    @staticmethod
    def err(e):
        return MesaResult(False, None, e)

    def unwrap(self):
        if self.is_ok:
            return self.value
        raise MesaRuntimeError(f"Unwrap on Err: {self.error}")

    def __repr__(self):
        return f"Ok({self.value})" if self.is_ok else f"Err({self.error})"


# === BAJO NIVEL REAL - NO SIMULADO ===

class RealLowLevelMemory:
    """Acceso DIRECTO a memoria real del sistema usando ctypes"""
    
    # Cargar libc (malloc, free, memset, memcpy)
    try:
        if sys.platform == 'win32':
            libc = ctypes.CDLL('msvcrt.dll')
        else:
            libc = ctypes.CDLL('libc.so.6')
    except:
        try:
            libc = ctypes.CDLL(None)  # Fallback
        except:
            libc = None
    
    # Mapeo de tipos Mesa -> ctypes
    CTYPES_MAP = {
        'int': c_int, 'entero': c_int,
        'float': c_float, 'decimal': c_float,
        'double': c_double,
        'char': c_char,
        'void': None,
    }
    
    TYPE_SIZES = {
        'int': sizeof(c_int), 'entero': sizeof(c_int),
        'float': sizeof(c_float), 'decimal': sizeof(c_float),
        'double': sizeof(c_double),
        'char': sizeof(c_char),
        'byte': 1,
        'ptr': sizeof(c_void_p), 'puntero': sizeof(c_void_p),
    }
    
    TYPE_DEFAULTS = {
        'int': 0, 'entero': 0,
        'float': 0.0, 'decimal': 0.0,
        'double': 0.0,
        'char': b'\0',
        'byte': 0,
    }
    
    def __init__(self):
        self.allocated_blocks = {}  # Tracking de bloques asignados
        
    def sizeof(self, type_name):
        """Retorna el tamaño REAL en bytes del tipo"""
        return self.TYPE_SIZES.get(type_name, sizeof(c_void_p))
    
    def default_value(self, type_name):
        return self.TYPE_DEFAULTS.get(type_name, 0)
    
    def malloc(self, count, elem_type='int'):
        """Llama a malloc() REAL del sistema"""
        elem_size = self.sizeof(elem_type)
        total_bytes = count * elem_size
        
        if self.libc:
            # malloc() REAL
            addr = self.libc.malloc(total_bytes)
            if not addr:
                raise MesaRuntimeError(f"malloc falló: no se pudo asignar {total_bytes} bytes")
        else:
            # Fallback: usar ctypes.create_string_buffer
            buffer = ctypes.create_string_buffer(total_bytes)
            addr = ctypes.addressof(buffer)
        
        # Guardar info del bloque
        self.allocated_blocks[addr] = {
            'size': count,
            'elem_type': elem_type,
            'elem_size': elem_size,
            'total_bytes': total_bytes,
        }
        
        return addr
    
    def free(self, addr):
        """Llama a free() REAL del sistema"""
        if addr not in self.allocated_blocks:
            raise MesaRuntimeError(f"Intentando liberar memoria no asignada: 0x{addr:X}")
        
        if self.libc:
            self.libc.free(addr)
        
        del self.allocated_blocks[addr]
    
    def read(self, addr, index, elem_type):
        """Lee desde memoria REAL"""
        if addr not in self.allocated_blocks:
            raise MesaRuntimeError(f"Lectura de memoria no asignada: 0x{addr:X}")
        
        block = self.allocated_blocks[addr]
        if index < 0 or index >= block['size']:
            raise MesaRuntimeError(f"Índice {index} fuera de rango (0-{block['size']-1})")
        
        ctype = self.CTYPES_MAP.get(elem_type, c_int)
        if ctype is None:
            raise MesaRuntimeError(f"Tipo '{elem_type}' no soportado para lectura")
        
        # Crear puntero al tipo correcto
        ptr = cast(addr, POINTER(ctype))
        return ptr[index]
    
    def write(self, addr, index, value, elem_type):
        """Escribe en memoria REAL"""
        if addr not in self.allocated_blocks:
            raise MesaRuntimeError(f"Escritura en memoria no asignada: 0x{addr:X}")
        
        block = self.allocated_blocks[addr]
        if index < 0 or index >= block['size']:
            raise MesaRuntimeError(f"Índice {index} fuera de rango (0-{block['size']-1})")
        
        ctype = self.CTYPES_MAP.get(elem_type, c_int)
        if ctype is None:
            raise MesaRuntimeError(f"Tipo '{elem_type}' no soportado para escritura")
        
        # Crear puntero y escribir
        ptr = cast(addr, POINTER(ctype))
        ptr[index] = ctype(value).value
    
    def memset(self, addr, value, count):
        """memset() REAL"""
        if addr not in self.allocated_blocks:
            raise MesaRuntimeError(f"memset en memoria no asignada: 0x{addr:X}")
        
        block = self.allocated_blocks[addr]
        elem_size = block['elem_size']
        
        if self.libc:
            # memset(void *ptr, int value, size_t num)
            self.libc.memset(addr, int(value), count * elem_size)
        else:
            # Fallback manual
            ptr = cast(addr, POINTER(c_int))
            for i in range(count):
                ptr[i] = int(value)
    
    def memcpy(self, dest_addr, src_addr, count):
        """memcpy() REAL"""
        if dest_addr not in self.allocated_blocks:
            raise MesaRuntimeError(f"memcpy: destino no válido 0x{dest_addr:X}")
        if src_addr not in self.allocated_blocks:
            raise MesaRuntimeError(f"memcpy: origen no válido 0x{src_addr:X}")
        
        dest_block = self.allocated_blocks[dest_addr]
        src_block = self.allocated_blocks[src_addr]
        
        elem_size = min(dest_block['elem_size'], src_block['elem_size'])
        
        if self.libc:
            # memcpy(void *dest, const void *src, size_t n)
            self.libc.memcpy(dest_addr, src_addr, count * elem_size)
        else:
            # Fallback usando memmove de ctypes
            memmove(dest_addr, src_addr, count * elem_size)
    
    def get_info(self, addr):
        """Obtiene información de un bloque de memoria"""
        return self.allocated_blocks.get(addr, None)


class RealLowPointer:
    """Puntero REAL a memoria del sistema"""
    
    def __init__(self, addr, elem_type='int', memory=None):
        self.addr = addr  # Dirección REAL de memoria
        self.elem_type = elem_type
        self.memory = memory
    
    def deref(self, index=0):
        """Desreferencia el puntero - lee de memoria REAL"""
        if self.memory:
            return self.memory.read(self.addr, index, self.elem_type)
        raise MesaRuntimeError("Puntero sin memoria asociada")
    
    def write(self, index, value):
        """Escribe en la posición del puntero - memoria REAL"""
        if self.memory:
            self.memory.write(self.addr, index, value, self.elem_type)
        else:
            raise MesaRuntimeError("Puntero sin memoria asociada")
    
    def offset(self, n):
        """Aritmética de punteros"""
        elem_size = self.memory.sizeof(self.elem_type) if self.memory else 4
        new_addr = self.addr + (n * elem_size)
        return RealLowPointer(new_addr, self.elem_type, self.memory)
    
    def __repr__(self):
        return f"<ptr 0x{self.addr:X} ({self.elem_type})>"
    
    def __int__(self):
        return self.addr


class RealLowArray:
    """Array REAL en memoria del sistema"""
    
    def __init__(self, elem_type, size, memory=None):
        self.elem_type = elem_type
        self.size = size
        self.memory = memory
        
        # Asignar memoria REAL
        if memory:
            self.addr = memory.malloc(size, elem_type)
        else:
            raise MesaRuntimeError("Array requiere gestor de memoria")
    
    def get(self, index):
        """Lee elemento en posición index - memoria REAL"""
        return self.memory.read(self.addr, index, self.elem_type)
    
    def set(self, index, value):
        """Escribe elemento en posición index - memoria REAL"""
        self.memory.write(self.addr, index, value, self.elem_type)
    
    def as_pointer(self):
        """Convierte el array a puntero"""
        return RealLowPointer(self.addr, self.elem_type, self.memory)
    
    def free(self):
        """Libera la memoria del array"""
        if self.memory and self.addr:
            self.memory.free(self.addr)
            self.addr = None
    
    def __repr__(self):
        try:
            data = [self.get(i) for i in range(min(self.size, 10))]
            suffix = '...' if self.size > 10 else ''
            return f"<{self.elem_type}[{self.size}] @ 0x{self.addr:X} = {data}{suffix}>"
        except:
            return f"<{self.elem_type}[{self.size}] @ 0x{self.addr:X}>"
    
    def __len__(self):
        return self.size
    
    def __del__(self):
        """Libera automáticamente cuando se destruye (seguridad)"""
        if hasattr(self, 'addr') and self.addr and hasattr(self, 'memory'):
            try:
                self.memory.free(self.addr)
            except:
                pass


# === INTERPRETE ===

class Interpreter:
    def __init__(self, debug=False):
        self.debug = debug
        self.env = Environment()
        self.tests = []
        self.memory = RealLowLevelMemory()  # MEMORIA REAL
        self._builtins()

    def _eval_string_expr(self, expr_str):
        """Evalúa una expresión de Mesa dentro de interpolación {expr}"""
        try:
            # Intentar primero como variable simple (más rápido)
            stripped = expr_str.strip()
            if stripped.isidentifier():
                try:
                    return self.env.get(stripped)
                except:
                    pass
            
            from .lexer import Lexer
            from .parser import Parser
            
            lex = Lexer(expr_str)
            tokens = lex.tokenize()
            parser = Parser(tokens)
            ast_expr = parser.parse_expr()
            return self.evaluate(ast_expr)
        except:
            # Último recurso: evaluar con Python
            try:
                local_vars = {}
                env = self.env
                while env:
                    for k, v in env.vars.items():
                        if k not in local_vars:
                            local_vars[k] = v
                    env = env.parent
                return eval(expr_str, {"__builtins__": {}}, local_vars)
            except:
                return None

    def _fmt(self, v):
        if v is None:
            return 'nada'
        if isinstance(v, bool):
            return 'verdadero' if v else 'falso'
        if isinstance(v, str):
            def repl(m):
                expr_str = m.group(1).strip()
                try:
                    result = self._eval_string_expr(expr_str)
                    if result is None:
                        return m.group(0)
                    return str(self._fmt(result))
                except:
                    return m.group(0)
            return re.sub(r'\{([^}]+)\}', repl, v)
        if isinstance(v, list):
            return '[' + ', '.join(self._fmt(x) for x in v) + ']'
        if isinstance(v, dict):
            return '{' + ', '.join(f'{k}: {self._fmt(x)}' for k, x in v.items()) + '}'
        if isinstance(v, float) and v == int(v):
            return str(int(v))
        if isinstance(v, (RealLowPointer, RealLowArray)):
            return repr(v)
        if isinstance(v, MesaInstance):
            return repr(v)
        if isinstance(v, MesaResult):
            return repr(v)
        if isinstance(v, MesaFunc):
            return repr(v)
        if isinstance(v, MesaShape):
            return repr(v)
        # ctypes values
        if isinstance(v, ctypes.c_int):
            return str(v.value)
        if isinstance(v, ctypes.c_float):
            return str(v.value)
        if isinstance(v, ctypes.c_double):
            return str(v.value)
        return str(v)

    def _truthy(self, v):
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return v != 0
        if isinstance(v, (str, list, dict)):
            return len(v) > 0
        return True

    def _builtins(self):
        def say(*a):
            print(' '.join(self._fmt(x) for x in a))

        def ask(p=''):
            return input(p) if p else input()

        self.env.define('decir', say)
        self.env.define('say', say)
        self.env.define('imprimir', say)
        self.env.define('print', say)
        self.env.define('preguntar', ask)
        self.env.define('ask', ask)
        self.env.define('input', ask)
        self.env.define('leer', ask)

        self.env.define('len', lambda x: len(x))
        self.env.define('tamaño', lambda x: len(x))
        self.env.define('range', lambda *a: list(range(*[int(x) for x in a])))
        self.env.define('rango', lambda *a: list(range(*[int(x) for x in a])))
        self.env.define('int', lambda x: int(float(x)) if isinstance(x, str) else int(x))
        self.env.define('entero', lambda x: int(float(x)) if isinstance(x, str) else int(x))
        self.env.define('float', lambda x: float(x))
        self.env.define('decimal', lambda x: float(x))
        self.env.define('str', lambda x: self._fmt(x))
        self.env.define('texto', lambda x: self._fmt(x))
        self.env.define('tipo', lambda x: type(x).__name__)
        self.env.define('type', lambda x: type(x).__name__)

        self.env.define('abs', abs)
        self.env.define('absoluto', abs)
        self.env.define('min', min)
        self.env.define('max', max)
        self.env.define('round', round)
        self.env.define('redondear', round)
        self.env.define('sum', lambda x: sum(x))
        self.env.define('suma', lambda x: sum(x))
        self.env.define('sorted', lambda x: sorted(x))
        self.env.define('ordenar', lambda x: sorted(x))
        self.env.define('reversed', lambda x: list(reversed(x)))
        self.env.define('invertir', lambda x: list(reversed(x)))

        self.env.define('sqrt', math.sqrt)
        self.env.define('raiz', math.sqrt)
        self.env.define('pow', math.pow)
        self.env.define('potencia', math.pow)
        self.env.define('sin', math.sin)
        self.env.define('cos', math.cos)
        self.env.define('tan', math.tan)
        self.env.define('log', math.log)
        self.env.define('PI', math.pi)
        self.env.define('E', math.e)

        self.env.define('random', random.random)
        self.env.define('aleatorio', random.random)
        self.env.define('randint', random.randint)

        self.env.define('time', time.time)
        self.env.define('tiempo', time.time)
        self.env.define('sleep', time.sleep)
        self.env.define('dormir', time.sleep)

        self.env.define('ok', lambda v: MesaResult.ok(v))
        self.env.define('Ok', lambda v: MesaResult.ok(v))
        self.env.define('err', lambda e: MesaResult.err(e))
        self.env.define('Err', lambda e: MesaResult.err(e))
        self.env.define('error', lambda e: MesaResult.err(e))
        self.env.define('es_ok', lambda r: isinstance(r, MesaResult) and r.is_ok)
        self.env.define('is_ok', lambda r: isinstance(r, MesaResult) and r.is_ok)
        self.env.define('es_error', lambda r: isinstance(r, MesaResult) and not r.is_ok)
        self.env.define('is_err', lambda r: isinstance(r, MesaResult) and not r.is_ok)

        def _verificar(c, m="Fallo de verificacion"):
            if not c:
                raise MesaRuntimeError(m)
            return True

        self.env.define('verificar', _verificar)
        self.env.define('check', _verificar)
        self.env.define('afirmar', _verificar)

        self.env.define('exit', lambda c=0: sys.exit(c))
        self.env.define('salir', lambda c=0: sys.exit(c))

        self.env.define('upper', lambda s: s.upper())
        self.env.define('lower', lambda s: s.lower())
        self.env.define('split', lambda s, d=None: s.split(d))
        self.env.define('join', lambda d, l: d.join(str(x) for x in l))
        self.env.define('replace', lambda s, a, b: s.replace(a, b))
        self.env.define('contains', lambda c, i: i in c)
        self.env.define('contiene', lambda c, i: i in c)
        # === REGISTRAR STDLIB (Filesystem, HTTP, JSON) ===
        from .stdlib import register_stdlib
        register_stdlib(self)
        # === X86 ASSEMBLER INTEGRADO ===
        from .x86 import register_x86
        register_x86(self)

    def interpret(self, program):
        try:
            r = None
            for s in program.statements:
                r = self.execute(s)
            return r
        except ReturnException as e:
            return e.value
        except MesaError as e:
            print(f"\n❌ Error: {e.message}", file=sys.stderr)
            sys.exit(1)
        except ThrowException as e:
            print(f"\n❌ Error lanzado: {self._fmt(e.value)}", file=sys.stderr)
            sys.exit(1)
        except (BreakException, ContinueException):
            pass
        except SystemExit:
            raise
        except Exception as e:
            print(f"\n❌ Error interno: {e}", file=sys.stderr)
            if self.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)

    def execute(self, node):
        if node is None:
            return None
        name = type(node).__name__
        method = getattr(self, f'exec_{name}', None)
        if method:
            return method(node)
        return self.evaluate(node)

    def evaluate(self, node):
        if node is None:
            return None
        name = type(node).__name__
        method = getattr(self, f'eval_{name}', None)
        if method:
            return method(node)
        raise MesaRuntimeError(f"No se puede evaluar nodo de tipo: {name}")

    # === EJECUTORES ===

    def exec_Program(self, n):
        r = None
        for s in n.statements:
            r = self.execute(s)
        return r

    def exec_Block(self, n):
        r = None
        for s in n.statements:
            r = self.execute(s)
        return r

    def exec_LevelBlock(self, n):
        for s in n.statements:
            self.execute(s)

    def exec_FunctionDef(self, n):
        f = MesaFunc(n.name, n.params, n.body, self.env)
        self.env.define(n.name, f)

    def exec_ShapeDef(self, n):
        methods = {}
        for m in n.methods:
            methods[m.name] = MesaFunc(m.name, m.params, m.body, self.env)
        shape = MesaShape(n.name, n.fields, methods)
        self.env.define_type(n.name, shape)
        self.env.define(n.name, shape)

    def exec_Assignment(self, n):
        v = self.evaluate(n.value)
        if isinstance(n.target, Identifier):
            self.env.set(n.target.name, v)
        elif isinstance(n.target, MemberAccess):
            obj = self.evaluate(n.target.object)
            if isinstance(obj, MesaInstance):
                obj.set(n.target.member, v)
            elif isinstance(obj, dict):
                obj[n.target.member] = v
        elif isinstance(n.target, IndexAccess):
            obj = self.evaluate(n.target.object)
            idx = self.evaluate(n.target.index)
            if isinstance(obj, RealLowArray):
                obj.set(int(idx), v)
            elif isinstance(obj, RealLowPointer):
                obj.write(int(idx), v)
            else:
                obj[idx] = v
        return v

    def exec_VariableDecl(self, n):
        v = self.evaluate(n.value) if n.value else None
        self.env.define(n.name, v)

    def exec_Return(self, n):
        raise ReturnException(self.evaluate(n.value))

    def exec_Break(self, n):
        raise BreakException()

    def exec_Continue(self, n):
        raise ContinueException()

    def exec_Throw(self, n):
        raise ThrowException(self.evaluate(n.value))

    def exec_IfStatement(self, n):
        if self._truthy(self.evaluate(n.condition)):
            for s in n.then_body:
                self.execute(s)
            return
        if n.elif_parts:
            for cond, body in n.elif_parts:
                if self._truthy(self.evaluate(cond)):
                    for s in body:
                        self.execute(s)
                    return
        if n.else_body:
            for s in n.else_body:
                self.execute(s)

    def exec_WhileLoop(self, n):
        try:
            while self._truthy(self.evaluate(n.condition)):
                try:
                    for s in n.body:
                        self.execute(s)
                except ContinueException:
                    continue
        except BreakException:
            pass

    def exec_ForLoop(self, n):
        it = self.evaluate(n.iterable)
        if isinstance(it, range):
            it = list(it)
        try:
            for i, item in enumerate(it):
                self.env.set(n.variable, item)
                if n.index_var:
                    self.env.set(n.index_var, i)
                try:
                    for s in n.body:
                        self.execute(s)
                except ContinueException:
                    continue
        except BreakException:
            pass

    def exec_RepeatLoop(self, n):
        times = int(self.evaluate(n.times))
        try:
            for i in range(times):
                if n.index_var:
                    self.env.set(n.index_var, i)
                try:
                    for s in n.body:
                        self.execute(s)
                except ContinueException:
                    continue
        except BreakException:
            pass

    def exec_InfiniteLoop(self, n):
        try:
            while True:
                try:
                    for s in n.body:
                        self.execute(s)
                except ContinueException:
                    continue
        except BreakException:
            pass

    def exec_MatchStatement(self, n):
        val = self.evaluate(n.value)
        for case in n.cases:
            if isinstance(case.pattern, WildcardPattern):
                for s in case.body:
                    self.execute(s)
                return
            pv = self.evaluate(case.pattern)
            if isinstance(pv, range):
                if val in pv:
                    for s in case.body:
                        self.execute(s)
                    return
            elif val == pv:
                for s in case.body:
                    self.execute(s)
                return

    def exec_TryStatement(self, n):
        try:
            for s in n.try_body:
                self.execute(s)
        except ThrowException as e:
            if n.catch_var and n.catch_body:
                self.env.define(n.catch_var, e.value)
                for s in n.catch_body:
                    self.execute(s)
        except MesaError as e:
            if n.catch_var and n.catch_body:
                self.env.define(n.catch_var, e.message)
                for s in n.catch_body:
                    self.execute(s)
        except Exception as e:
            if n.catch_var and n.catch_body:
                self.env.define(n.catch_var, str(e))
                for s in n.catch_body:
                    self.execute(s)
        finally:
            if n.finally_body:
                for s in n.finally_body:
                    self.execute(s)

    def exec_TestDef(self, n):
        self.tests.append((n.name, n.body))

    def exec_ImportStmt(self, n):
        pass

    def exec_ModuleDef(self, n):
        pass

    # === BAJO NIVEL REAL ===

    def exec_LowBlock(self, n):
        """Ejecuta bloque de bajo nivel con memoria REAL"""
        for s in n.statements:
            self.execute(s)

    def exec_LowVarDecl(self, n):
        """Declara variable de bajo nivel - MEMORIA REAL"""
        if n.is_array:
            # Array REAL en memoria
            size = int(self.evaluate(n.array_size)) if n.array_size else 0
            arr = RealLowArray(n.var_type, size, self.memory)
            
            # Inicializar si hay valor
            if n.value:
                val = self.evaluate(n.value)
                if isinstance(val, list):
                    for i, v in enumerate(val):
                        if i < size:
                            arr.set(i, v)
            
            self.env.define(n.name, arr)
            
        elif n.is_pointer:
            # Puntero REAL
            if n.value:
                val = self.evaluate(n.value)
                if isinstance(val, RealLowPointer):
                    self.env.define(n.name, val)
                elif isinstance(val, RealLowArray):
                    self.env.define(n.name, val.as_pointer())
                elif isinstance(val, int):
                    self.env.define(n.name, RealLowPointer(val, n.var_type, self.memory))
                else:
                    self.env.define(n.name, val)
            else:
                self.env.define(n.name, RealLowPointer(0, n.var_type, self.memory))
        else:
            # Variable escalar
            if n.value:
                val = self.evaluate(n.value)
            else:
                val = self.memory.default_value(n.var_type)
            
            val = self._low_cast(val, n.var_type)
            self.env.define(n.name, val)

    def exec_LowMalloc(self, n):
        """malloc() REAL del sistema"""
        size = int(self.evaluate(n.size))
        addr = self.memory.malloc(size, n.element_type)
        return RealLowPointer(addr, n.element_type, self.memory)

    def exec_LowFree(self, n):
        """free() REAL del sistema"""
        ptr = self.evaluate(n.pointer)
        if isinstance(ptr, RealLowPointer):
            self.memory.free(ptr.addr)
        elif isinstance(ptr, RealLowArray):
            ptr.free()
        elif isinstance(ptr, int):
            self.memory.free(ptr)
        else:
            raise MesaRuntimeError(f"No se puede liberar: {type(ptr).__name__}")

    def exec_LowSizeof(self, n):
        """sizeof() REAL"""
        return self.memory.sizeof(n.target)

    def exec_LowPrintAddr(self, n):
        """Imprime dirección de memoria REAL"""
        val = self.evaluate(n.operand)
        if isinstance(val, RealLowPointer):
            print(f"0x{val.addr:X}")
        elif isinstance(val, RealLowArray):
            print(f"0x{val.addr:X}")
        elif isinstance(val, int):
            print(f"0x{val:X}")
        else:
            # Obtener dirección usando ctypes
            try:
                addr = id(val)
                print(f"0x{addr:X}")
            except:
                print("0x0")

    def exec_LowMemset(self, n):
        """memset() REAL del sistema"""
        ptr = self.evaluate(n.pointer)
        val = self.evaluate(n.value)
        size = int(self.evaluate(n.size))
        
        if isinstance(ptr, RealLowPointer):
            self.memory.memset(ptr.addr, val, size)
        elif isinstance(ptr, RealLowArray):
            self.memory.memset(ptr.addr, val, size)
        else:
            raise MesaRuntimeError("memset requiere un puntero")

    def exec_LowMemcpy(self, n):
        """memcpy() REAL del sistema"""
        dest = self.evaluate(n.dest)
        src = self.evaluate(n.src)
        size = int(self.evaluate(n.size))
        
        dest_addr = dest.addr if isinstance(dest, (RealLowPointer, RealLowArray)) else dest
        src_addr = src.addr if isinstance(src, (RealLowPointer, RealLowArray)) else src
        
        self.memory.memcpy(dest_addr, src_addr, size)

    def exec_LowPointerOp(self, n):
        if n.operator == '&':
            if isinstance(n.operand, Identifier):
                # Obtener dirección de una variable
                # En bajo nivel simulamos esto
                val = self.env.get(n.operand.name)
                if isinstance(val, RealLowArray):
                    return val.as_pointer()
                # Para variables normales, crear espacio
                addr = id(val)  # Dirección Python (no ideal pero funciona)
                return RealLowPointer(addr, 'int', self.memory)
            val = self.evaluate(n.operand)
            return val
        elif n.operator == '*':
            val = self.evaluate(n.operand)
            if isinstance(val, RealLowPointer):
                return val.deref()
            raise MesaRuntimeError("No se puede desreferenciar un no-puntero")
        elif n.operator == 'deref_assign':
            return self.evaluate(n.operand)
        return self.evaluate(n.operand)

    def _low_cast(self, val, type_name):
        """Castea valor a tipo de bajo nivel"""
        if val is None:
            return self.memory.default_value(type_name)
        try:
            if type_name in ('int', 'entero', 'long', 'short', 'byte'):
                return int(val) if not isinstance(val, bool) else (1 if val else 0)
            elif type_name in ('float', 'decimal', 'double'):
                return float(val)
            elif type_name in ('char',):
                if isinstance(val, str):
                    return val[0] if val else '\0'
                return chr(int(val))
            elif type_name in ('bool', 'booleano'):
                return bool(val)
        except (ValueError, TypeError):
            return self.memory.default_value(type_name)
        return val

    # === EVALUADORES ===

    def eval_NumberLiteral(self, n):
        return n.value

    def eval_StringLiteral(self, n):
        return n.value

    def eval_BoolLiteral(self, n):
        return n.value

    def eval_NoneLiteral(self, n):
        return None

    def eval_Identifier(self, n):
        return self.env.get(n.name)

    def eval_SelfExpr(self, n):
        return self.env.get('self')

    def eval_ListLiteral(self, n):
        return [self.evaluate(e) for e in n.elements]

    def eval_MapLiteral(self, n):
        r = {}
        for k, v in n.pairs:
            kv = self.evaluate(k)
            r[kv] = self.evaluate(v)
        return r

    def eval_TupleLiteral(self, n):
        return tuple(self.evaluate(e) for e in n.elements)

    def eval_BinaryOp(self, n):
        if n.operator in ('and', 'y'):
            l = self.evaluate(n.left)
            return l if not self._truthy(l) else self.evaluate(n.right)
        if n.operator in ('or', 'o'):
            l = self.evaluate(n.left)
            return l if self._truthy(l) else self.evaluate(n.right)

        l = self.evaluate(n.left)
        r = self.evaluate(n.right)

        if n.operator == '..':
            return list(range(int(l), int(r)))

        if n.operator == '+':
            if isinstance(l, str):
                return l + self._fmt(r)
            if isinstance(l, list):
                if isinstance(r, list):
                    return l + r
                return l + [r]

        ops = {
            '+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv,
            '%': op.mod, '**': op.pow, '==': op.eq, '!=': op.ne,
            '<': op.lt, '>': op.gt, '<=': op.le, '>=': op.ge,
        }
        if n.operator in ops:
            try:
                return ops[n.operator](l, r)
            except ZeroDivisionError:
                raise MesaRuntimeError("Division por cero")
            except TypeError:
                raise MesaRuntimeError(f"Operacion '{n.operator}' no soportada entre {type(l).__name__} y {type(r).__name__}")

        raise MesaRuntimeError(f"Operador desconocido: {n.operator}")

    def eval_UnaryOp(self, n):
        o = self.evaluate(n.operand)
        if n.operator == '-':
            return -o
        if n.operator in ('not', 'no'):
            return not self._truthy(o)
        return o

    def eval_CallExpr(self, n):
        callee = self.evaluate(n.callee)
        args = [self.evaluate(a) for a in n.args]

        if isinstance(callee, MesaFunc):
            return self._call_func(callee, args)
        if isinstance(callee, MesaShape):
            return self._instantiate(callee, args, n.kwargs)
        if isinstance(callee, Lambda):
            return self._call_lambda(callee, args)
        if callable(callee):
            try:
                return callee(*args)
            except TypeError as e:
                raise MesaRuntimeError(f"Error al llamar funcion: {e}")
        raise MesaRuntimeError(f"No es invocable: {self._fmt(callee)}")

    def eval_Lambda(self, n):
        return MesaFunc('<lambda>', n.params, n.body, self.env)

    def eval_MethodCall(self, n):
        obj = self.evaluate(n.object)
        args = [self.evaluate(a) for a in n.args]

        if isinstance(obj, MesaInstance):
            m = obj.get_method(n.method)
            if m:
                return self._call_method(obj, m, args)
        if isinstance(obj, list):
            return self._list_method(obj, n.method, args)
        if isinstance(obj, str):
            return self._str_method(obj, n.method, args)
        if isinstance(obj, dict):
            return self._dict_method(obj, n.method, args)
        if isinstance(obj, MesaResult):
            return self._result_method(obj, n.method, args)
        if isinstance(obj, RealLowArray):
            return self._low_array_method(obj, n.method, args)
        if isinstance(obj, RealLowPointer):
            return self._low_pointer_method(obj, n.method, args)

        raise MesaRuntimeError(f"Metodo '{n.method}' no existe en {type(obj).__name__}")

    def eval_MemberAccess(self, n):
        obj = self.evaluate(n.object)
        if isinstance(obj, MesaInstance):
            return obj.get(n.member)
        if isinstance(obj, dict):
            if n.member in obj:
                return obj[n.member]
            return None
        if isinstance(obj, MesaResult):
            if n.member in ('value', 'valor'):
                return obj.value
            if n.member in ('error', 'err'):
                return obj.error
            if n.member in ('is_ok', 'es_ok'):
                return obj.is_ok
        raise MesaRuntimeError(f"No se puede acceder a '{n.member}' en {type(obj).__name__}")

    def eval_IndexAccess(self, n):
        obj = self.evaluate(n.object)
        idx = self.evaluate(n.index)
        try:
            if isinstance(obj, RealLowArray):
                return obj.get(int(idx))
            if isinstance(obj, RealLowPointer):
                return obj.deref(int(idx))
            return obj[idx]
        except (IndexError, KeyError):
            raise MesaRuntimeError(f"Indice fuera de rango: {idx}")
        except TypeError:
            raise MesaRuntimeError(f"No se puede indexar {type(obj).__name__}")

    def eval_StructInstantiation(self, n):
        try:
            shape = self.env.get_type(n.type_name)
        except MesaRuntimeError:
            shape = self.env.get(n.type_name)

        if isinstance(shape, MesaShape):
            fields = {fn: self.evaluate(fv) for fn, fv in n.fields.items()}
            for fd in shape.fields:
                if fd.name not in fields:
                    fields[fd.name] = self.evaluate(fd.default_value) if fd.default_value else None
            return MesaInstance(shape, fields)
        raise MesaRuntimeError(f"'{n.type_name}' no es un tipo valido")

    def eval_IfExpr(self, n):
        if self._truthy(self.evaluate(n.condition)):
            return self.evaluate(n.then_value)
        return self.evaluate(n.else_value) if n.else_value else None

    def eval_LowVarDecl(self, n):
        self.exec_LowVarDecl(n)
        return None

    def eval_LowMalloc(self, n):
        return self.exec_LowMalloc(n)

    def eval_LowFree(self, n):
        self.exec_LowFree(n)
        return None

    def eval_LowSizeof(self, n):
        return self.exec_LowSizeof(n)

    def eval_LowPointerOp(self, n):
        return self.exec_LowPointerOp(n)

    def eval_LowPrintAddr(self, n):
        self.exec_LowPrintAddr(n)
        return None

    def eval_LowBlock(self, n):
        self.exec_LowBlock(n)
        return None

    def eval_LowArrayAccess(self, n):
        arr = self.evaluate(n.array)
        idx = int(self.evaluate(n.index))
        if isinstance(arr, RealLowArray):
            return arr.get(idx)
        if isinstance(arr, RealLowPointer):
            return arr.deref(idx)
        return arr[idx]

    def eval_LowCast(self, n):
        val = self.evaluate(n.expr)
        return self._low_cast(val, n.target_type)

    def eval_LowMemset(self, n):
        self.exec_LowMemset(n)
        return None

    def eval_LowMemcpy(self, n):
        self.exec_LowMemcpy(n)
        return None

    # === LLAMADAS ===

    def _call_func(self, func, args):
        fe = Environment(func.closure)
        param_idx = 0
        for p in func.params:
            pn = p.name if hasattr(p, 'name') else str(p)
            if hasattr(p, 'is_self') and p.is_self:
                continue
            if param_idx < len(args):
                fe.define(pn, args[param_idx])
            elif hasattr(p, 'default_value') and p.default_value:
                fe.define(pn, self.evaluate(p.default_value))
            else:
                fe.define(pn, None)
            param_idx += 1
        prev = self.env
        self.env = fe
        try:
            for s in func.body:
                self.execute(s)
            return None
        except ReturnException as e:
            return e.value
        finally:
            self.env = prev

    def _call_lambda(self, lam, args):
        func = MesaFunc('<lambda>', lam.params, lam.body, self.env)
        return self._call_func(func, args)

    def _call_method(self, inst, method, args):
        me = Environment(method.closure)
        me.define('self', inst)
        me.define('yo', inst)
        pi = 0
        for p in method.params:
            if hasattr(p, 'is_self') and p.is_self:
                continue
            pn = p.name if hasattr(p, 'name') else str(p)
            me.define(pn, args[pi] if pi < len(args) else None)
            pi += 1
        prev = self.env
        self.env = me
        try:
            for s in method.body:
                self.execute(s)
            return None
        except ReturnException as e:
            return e.value
        finally:
            self.env = prev

    def _instantiate(self, shape, args, kwargs):
        fields = {}
        kw = {k: self.evaluate(v) for k, v in kwargs.items()} if kwargs else {}
        for i, fd in enumerate(shape.fields):
            if fd.name in kw:
                fields[fd.name] = kw[fd.name]
            elif i < len(args):
                fields[fd.name] = args[i]
            elif fd.default_value:
                fields[fd.name] = self.evaluate(fd.default_value)
            else:
                fields[fd.name] = None
        return MesaInstance(shape, fields)

    # === METODOS DE COLECCIONES ===

    def _list_method(self, lst, m, args):
        if m in ('agregar', 'add', 'push', 'append'):
            lst.append(args[0])
            return None
        if m in ('remover', 'remove', 'pop'):
            return lst.pop(int(args[0]) if args else -1)
        if m in ('tamaño', 'len', 'size', 'length'):
            return len(lst)
        if m in ('vacío', 'vacio', 'empty', 'is_empty'):
            return len(lst) == 0
        if m in ('contiene', 'contains', 'includes'):
            return args[0] in lst
        if m in ('índice', 'indice', 'index', 'find'):
            try:
                return lst.index(args[0])
            except ValueError:
                return -1
        if m in ('invertir', 'reverse'):
            lst.reverse()
            return None
        if m in ('ordenar', 'sort'):
            lst.sort()
            return None
        if m in ('copiar', 'copy', 'clone'):
            return lst.copy()
        if m in ('primero', 'first'):
            return lst[0] if lst else None
        if m in ('último', 'ultimo', 'last'):
            return lst[-1] if lst else None
        if m in ('unir', 'join'):
            sep = args[0] if args else ''
            return sep.join(str(x) for x in lst)
        if m in ('filtrar', 'filter'):
            fn = args[0]
            return [x for x in lst if self._truthy(self._call_func(fn, [x]))]
        if m in ('mapear', 'map'):
            fn = args[0]
            return [self._call_func(fn, [x]) for x in lst]
        if m in ('insertar', 'insert'):
            if len(args) >= 2:
                lst.insert(int(args[0]), args[1])
            return None
        if m in ('limpiar', 'clear'):
            lst.clear()
            return None
        raise MesaRuntimeError(f"Metodo de lista '{m}' no existe")

    def _str_method(self, s, m, args):
        if m in ('mayúsculas', 'mayusculas', 'upper'):
            return s.upper()
        if m in ('minúsculas', 'minusculas', 'lower'):
            return s.lower()
        if m in ('dividir', 'split'):
            return s.split(args[0] if args else None)
        if m in ('unir', 'join'):
            return s.join(str(x) for x in args[0])
        if m in ('recortar', 'strip', 'trim'):
            return s.strip()
        if m in ('reemplazar', 'replace'):
            return s.replace(args[0], args[1])
        if m in ('empieza_con', 'startswith', 'starts_with'):
            return s.startswith(args[0])
        if m in ('termina_con', 'endswith', 'ends_with'):
            return s.endswith(args[0])
        if m in ('contiene', 'contains', 'includes'):
            return args[0] in s
        if m in ('encontrar', 'find', 'index'):
            return s.find(args[0])
        if m in ('tamaño', 'len', 'length'):
            return len(s)
        if m in ('capitalizar', 'capitalize'):
            return s.capitalize()
        if m in ('titulo', 'title'):
            return s.title()
        raise MesaRuntimeError(f"Metodo de string '{m}' no existe")

    def _dict_method(self, d, m, args):
        if m in ('obtener', 'get'):
            return d.get(args[0], args[1] if len(args) > 1 else None)
        if m in ('claves', 'keys'):
            return list(d.keys())
        if m in ('valores', 'values'):
            return list(d.values())
        if m in ('items', 'elementos'):
            return [[k, v] for k, v in d.items()]
        if m in ('contiene', 'contains', 'has'):
            return args[0] in d
        if m in ('tamaño', 'len', 'size'):
            return len(d)
        if m in ('eliminar', 'delete', 'remove'):
            if args[0] in d:
                del d[args[0]]
            return None
        raise MesaRuntimeError(f"Metodo de dict '{m}' no existe")

    def _result_method(self, r, m, args):
        if m in ('unwrap', 'desenvolver'):
            return r.unwrap()
        if m in ('unwrap_or', 'desenvolver_o'):
            return r.value if r.is_ok else args[0]
        if m in ('is_ok', 'es_ok'):
            return r.is_ok
        if m in ('is_err', 'es_error'):
            return not r.is_ok
        raise MesaRuntimeError(f"Metodo de Result '{m}' no existe")

    def _low_array_method(self, arr, m, args):
        if m in ('tamaño', 'len', 'size', 'length'):
            return arr.size
        if m in ('obtener', 'get'):
            return arr.get(int(args[0]))
        if m in ('poner', 'set'):
            arr.set(int(args[0]), args[1])
            return None
        if m in ('dir', 'addr', 'direccion'):
            return arr.addr
        if m in ('liberar', 'free'):
            arr.free()
            return None
        raise MesaRuntimeError(f"Metodo de array '{m}' no existe")

    def _low_pointer_method(self, ptr, m, args):
        if m in ('leer', 'read', 'deref'):
            idx = int(args[0]) if args else 0
            return ptr.deref(idx)
        if m in ('escribir', 'write'):
            ptr.write(int(args[0]), args[1])
            return None
        if m in ('dir', 'addr', 'direccion'):
            return ptr.addr
        if m in ('offset', 'desplazar'):
            return ptr.offset(int(args[0]))
        raise MesaRuntimeError(f"Metodo de puntero '{m}' no existe")

    # === TESTS ===

    def run_tests(self):
        passed = 0
        failed = 0
        print("\n🧪 Ejecutando tests...\n")
        for name, body in self.tests:
            try:
                test_env = Environment(self.env)
                prev = self.env
                self.env = test_env
                try:
                    for s in body:
                        self.execute(s)
                finally:
                    self.env = prev
                print(f"  ✅ {name}")
                passed += 1
            except MesaRuntimeError as e:
                print(f"  ❌ {name}: {e.message}")
                failed += 1
            except Exception as e:
                print(f"  ❌ {name}: {e}")
                failed += 1
        total = passed + failed
        print(f"\n📊 Resultados: {passed}/{total} pasaron, {failed} fallaron")
        return passed, failed