from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


class TokenType(Enum):
    # Entrada
    INICIO = auto()
    START = auto()
    # Funciones
    FUNCION = auto()
    FUNCTION = auto()
    # Retorno
    DAR = auto()
    GIVE = auto()
    RETURN = auto()
    # Condicionales
    SI = auto()
    IF = auto()
    SINO = auto()
    ELSE = auto()
    ADEMAS = auto()
    ALSO = auto()
    ELIF = auto()
    ENTONCES = auto()
    THEN = auto()
    # Bucles
    PARA = auto()
    FOR = auto()
    MIENTRAS = auto()
    WHILE = auto()
    REPETIR = auto()
    REPEAT = auto()
    BUCLE = auto()
    LOOP = auto()
    # Control bucles
    PARAR = auto()
    BREAK = auto()
    STOP = auto()
    CONTINUAR = auto()
    CONTINUE = auto()
    SALTAR = auto()
    SKIP = auto()
    # Match
    COINCIDIR = auto()
    MATCH = auto()
    # Estructuras
    FORMA = auto()
    SHAPE = auto()
    CLASE = auto()
    CLASS = auto()
    STRUCT = auto()
    ENUMERAR = auto()
    ENUM = auto()
    RASGO = auto()
    TRAIT = auto()
    INTERFAZ = auto()
    INTERFACE = auto()
    APLICAR = auto()
    APPLY = auto()
    IMPLEMENTAR = auto()
    IMPLEMENT = auto()
    EXTENDER = auto()
    EXTEND = auto()
    # Modificadores
    PUBLICO = auto()
    PUBLIC = auto()
    PUB = auto()
    PRIVADO = auto()
    PRIVATE = auto()
    CONSTANTE = auto()
    CONST = auto()
    MUTABLE = auto()
    MUT = auto()
    ESTATICO = auto()
    STATIC = auto()
    # Memoria
    PUNTERO = auto()
    PTR = auto()
    RESERVAR = auto()
    ALLOC = auto()
    LIBERAR = auto()
    FREE = auto()
    NUEVO = auto()
    NEW = auto()
    # Modulos
    MODULO = auto()
    MODULE = auto()
    USAR = auto()
    USE = auto()
    IMPORTAR = auto()
    IMPORT = auto()
    COMO = auto()
    AS = auto()
    # Concurrencia
    TAREA = auto()
    TASK = auto()
    ESPERAR = auto()
    AWAIT = auto()
    ASYNC = auto()
    CANAL = auto()
    CHANNEL = auto()
    # Errores
    INTENTAR = auto()
    TRY = auto()
    CAPTURAR = auto()
    CATCH = auto()
    FINALMENTE = auto()
    FINALLY = auto()
    LANZAR = auto()
    THROW = auto()
    OK = auto()
    ERR = auto()
    # Testing
    PRUEBA = auto()
    TEST = auto()
    VERIFICAR = auto()
    CHECK = auto()
    AFIRMAR = auto()
    ASSERT = auto()
    # Niveles
    MEDIO = auto()
    MID = auto()
    BAJO = auto()
    LOW = auto()
    # Especiales
    YO = auto()
    SELF = auto()
    THIS = auto()
    SUPER = auto()
    VERDADERO = auto()
    TRUE = auto()
    FALSO = auto()
    FALSE = auto()
    NADA = auto()
    NONE = auto()
    NULL = auto()
    # Logicos
    Y = auto()
    AND = auto()
    O = auto()
    OR = auto()
    NO = auto()
    NOT = auto()
    # Otros
    EN = auto()
    IN = auto()
    ES = auto()
    IS = auto()
    DE = auto()
    # Tipos bajo nivel
    ENTERO = auto()
    INT = auto()
    DECIMAL = auto()
    FLOAT = auto()
    TEXTO = auto()
    STRING = auto()
    STR = auto()
    CHAR = auto()
    BOOL = auto()
    BOOLEANO = auto()
    LISTA = auto()
    LIST = auto()
    MAPA = auto()
    MAP = auto()
    CONJUNTO = auto()
    SET = auto()
    VOID = auto()
    DOUBLE = auto()
    LONG = auto()
    SHORT = auto()
    BYTE = auto()
    # sizeof
    SIZEOF = auto()
    TAMANIO = auto()
    # Literales
    NUMBER = auto()
    STRING_LIT = auto()
    IDENTIFIER = auto()
    TYPE_ID = auto()
    # Aritmeticos
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    PERCENT = auto()
    POWER = auto()
    # Comparacion
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS = auto()
    GREATER = auto()
    LESS_EQUAL = auto()
    GREATER_EQUAL = auto()
    # Asignacion
    ASSIGN = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()
    MULTIPLY_ASSIGN = auto()
    DIVIDE_ASSIGN = auto()
    # Especiales
    ARROW = auto()
    FAT_ARROW = auto()
    RANGE = auto()
    SPREAD = auto()
    PIPELINE = auto()
    QUESTION = auto()
    EXCLAMATION = auto()
    AT = auto()
    HASH = auto()
    BIT_AND = auto()
    BIT_OR = auto()
    BIT_XOR = auto()
    BIT_NOT = auto()
    LSHIFT = auto()
    RSHIFT = auto()
    DOUBLE_COLON = auto()
    AMPERSAND = auto()
    # Delimitadores
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    DOT = auto()
    COLON = auto()
    SEMICOLON = auto()
    PIPE = auto()
    # Control
    NEWLINE = auto()
    EOF = auto()


class LexerError(Exception):
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Error linea {line}, col {column}: {message}")


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line}:C{self.column})"


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.keywords = {
            'inicio': TokenType.INICIO, 'start': TokenType.START,
            'funcion': TokenType.FUNCION, 'función': TokenType.FUNCION,
            'web': TokenType.IDENTIFIER,  # Se manejará como identificador especial
            'fn': TokenType.FUNCION, 'function': TokenType.FUNCTION,
            'dar': TokenType.DAR, 'give': TokenType.GIVE, 'return': TokenType.RETURN,
            'si': TokenType.SI, 'if': TokenType.IF,
            'sino': TokenType.SINO, 'else': TokenType.ELSE,
            'ademas': TokenType.ADEMAS, 'además': TokenType.ADEMAS,
            'also': TokenType.ALSO, 'elif': TokenType.ELIF,
            'entonces': TokenType.ENTONCES, 'then': TokenType.THEN,
            'para': TokenType.PARA, 'for': TokenType.FOR,
            'mientras': TokenType.MIENTRAS, 'while': TokenType.WHILE,
            'repetir': TokenType.REPETIR, 'repeat': TokenType.REPEAT,
            'bucle': TokenType.BUCLE, 'loop': TokenType.LOOP,
            'parar': TokenType.PARAR, 'break': TokenType.BREAK, 'stop': TokenType.STOP,
            'continuar': TokenType.CONTINUAR, 'continue': TokenType.CONTINUE,
            'saltar': TokenType.SALTAR, 'skip': TokenType.SKIP,
            'coincidir': TokenType.COINCIDIR, 'match': TokenType.MATCH,
            'forma': TokenType.FORMA, 'shape': TokenType.SHAPE,
            'clase': TokenType.CLASE, 'class': TokenType.CLASS, 'struct': TokenType.STRUCT,
            'enumerar': TokenType.ENUMERAR, 'enum': TokenType.ENUM,
            'rasgo': TokenType.RASGO, 'trait': TokenType.TRAIT,
            'interfaz': TokenType.INTERFAZ, 'interface': TokenType.INTERFACE,
            'aplicar': TokenType.APLICAR, 'apply': TokenType.APPLY,
            'implementar': TokenType.IMPLEMENTAR, 'implement': TokenType.IMPLEMENT,
            'extender': TokenType.EXTENDER, 'extend': TokenType.EXTEND,
            'publico': TokenType.PUBLICO, 'público': TokenType.PUBLICO,
            'public': TokenType.PUBLIC, 'pub': TokenType.PUB,
            'privado': TokenType.PRIVADO, 'private': TokenType.PRIVATE,
            'constante': TokenType.CONSTANTE, 'const': TokenType.CONST,
            'mutable': TokenType.MUTABLE, 'mut': TokenType.MUT,
            'estatico': TokenType.ESTATICO, 'estático': TokenType.ESTATICO, 'static': TokenType.STATIC,
            'puntero': TokenType.PUNTERO, 'ptr': TokenType.PTR,
            'reservar': TokenType.RESERVAR, 'alloc': TokenType.ALLOC,
            'liberar': TokenType.LIBERAR, 'free': TokenType.FREE,
            'nuevo': TokenType.NUEVO, 'new': TokenType.NEW,
            'modulo': TokenType.MODULO, 'módulo': TokenType.MODULO, 'module': TokenType.MODULE,
            'usar': TokenType.USAR, 'use': TokenType.USE,
            'importar': TokenType.IMPORTAR, 'import': TokenType.IMPORT,
            'como': TokenType.COMO, 'as': TokenType.AS,
            'tarea': TokenType.TAREA, 'task': TokenType.TASK,
            'esperar': TokenType.ESPERAR, 'await': TokenType.AWAIT, 'async': TokenType.ASYNC,
            'canal': TokenType.CANAL, 'channel': TokenType.CHANNEL,
            'intentar': TokenType.INTENTAR, 'try': TokenType.TRY,
            'capturar': TokenType.CAPTURAR, 'catch': TokenType.CATCH,
            'finalmente': TokenType.FINALMENTE, 'finally': TokenType.FINALLY,
            'lanzar': TokenType.LANZAR, 'throw': TokenType.THROW,
            'ok': TokenType.OK, 'err': TokenType.ERR,
            'prueba': TokenType.PRUEBA, 'test': TokenType.TEST,
            'verificar': TokenType.VERIFICAR, 'check': TokenType.CHECK,
            'afirmar': TokenType.AFIRMAR, 'assert': TokenType.ASSERT,
            'medio': TokenType.MEDIO, 'mid': TokenType.MID,
            'bajo': TokenType.BAJO, 'low': TokenType.LOW,
            'yo': TokenType.YO, 'self': TokenType.SELF, 'this': TokenType.THIS,
            'super': TokenType.SUPER,
            'verdadero': TokenType.VERDADERO, 'true': TokenType.TRUE,
            'falso': TokenType.FALSO, 'false': TokenType.FALSE,
            'nada': TokenType.NADA, 'none': TokenType.NONE, 'null': TokenType.NULL,
            'y': TokenType.Y, 'and': TokenType.AND,
            'o': TokenType.O, 'or': TokenType.OR,
            'no': TokenType.NO, 'not': TokenType.NOT,
            'en': TokenType.EN, 'in': TokenType.IN,
            'es': TokenType.ES, 'is': TokenType.IS,
            'de': TokenType.DE,
            'entero': TokenType.ENTERO, 'int': TokenType.INT,
            'decimal': TokenType.DECIMAL, 'float': TokenType.FLOAT,
            'texto': TokenType.TEXTO, 'string': TokenType.STRING, 'str': TokenType.STR,
            'char': TokenType.CHAR, 'bool': TokenType.BOOL, 'booleano': TokenType.BOOLEANO,
            'lista': TokenType.LISTA, 'list': TokenType.LIST,
            'mapa': TokenType.MAPA, 'map': TokenType.MAP,
            'conjunto': TokenType.CONJUNTO, 'set': TokenType.SET,
            'void': TokenType.VOID,
            'double': TokenType.DOUBLE, 'long': TokenType.LONG,
            'short': TokenType.SHORT, 'byte': TokenType.BYTE,
            'sizeof': TokenType.SIZEOF, 'tamaño_de': TokenType.TAMANIO,
        }

    def cur(self):
        return self.source[self.pos] if self.pos < len(self.source) else None

    def pk(self, n=1):
        p = self.pos + n
        return self.source[p] if p < len(self.source) else None

    def adv(self):
        c = self.cur()
        if c:
            if c == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
        return c

    def skip_ws(self):
        while self.cur() and self.cur() in ' \t\r':
            self.adv()

    def skip_comment(self):
        if self.cur() == '-' and self.pk() == '-':
            while self.cur() and self.cur() != '\n':
                self.adv()
            return True
        if self.cur() == '/' and self.pk() == '*':
            self.adv()
            self.adv()
            d = 1
            while d > 0:
                if not self.cur():
                    raise LexerError("Comentario sin cerrar", self.line, self.column)
                if self.cur() == '/' and self.pk() == '*':
                    self.adv()
                    self.adv()
                    d += 1
                elif self.cur() == '*' and self.pk() == '/':
                    self.adv()
                    self.adv()
                    d -= 1
                else:
                    self.adv()
            return True
        return False

    def read_num(self):
        sl, sc = self.line, self.column
        s = ''
        dot = False
        if self.cur() == '0' and self.pk() and self.pk().lower() == 'x':
            self.adv()
            self.adv()
            while self.cur() and (self.cur() in '0123456789abcdefABCDEF' or self.cur() == '_'):
                if self.cur() != '_':
                    s += self.cur()
                self.adv()
            return Token(TokenType.NUMBER, int(s, 16), sl, sc)
        if self.cur() == '0' and self.pk() and self.pk().lower() == 'b':
            self.adv()
            self.adv()
            while self.cur() and (self.cur() in '01' or self.cur() == '_'):
                if self.cur() != '_':
                    s += self.cur()
                self.adv()
            return Token(TokenType.NUMBER, int(s, 2), sl, sc)
        while self.cur() and (self.cur().isdigit() or self.cur() in '._eE'):
            if self.cur() == '_':
                self.adv()
                continue
            if self.cur() == '.':
                if dot:
                    break
                if self.pk() == '.':
                    break
                dot = True
            if self.cur() in 'eE':
                dot = True
                s += self.cur()
                self.adv()
                if self.cur() and self.cur() in '+-':
                    s += self.cur()
                    self.adv()
                continue
            s += self.cur()
            self.adv()
        v = float(s) if dot else int(s)
        return Token(TokenType.NUMBER, v, sl, sc)

    def read_str(self):
        sl, sc = self.line, self.column
        q = self.cur()
        self.adv()
        s = ''
        while self.cur() and self.cur() != q:
            if self.cur() == '\\':
                self.adv()
                e = self.cur()
                if e == 'n':
                    s += '\n'
                elif e == 't':
                    s += '\t'
                elif e == 'r':
                    s += '\r'
                elif e == '\\':
                    s += '\\'
                elif e == q:
                    s += q
                else:
                    s += (e or '')
                self.adv()
            else:
                s += self.cur()
                self.adv()
        if not self.cur():
            raise LexerError("String sin cerrar", sl, sc)
        self.adv()
        return Token(TokenType.STRING_LIT, s, sl, sc)

    def read_id(self):
        sl, sc = self.line, self.column
        s = ''
        vc = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
        vc += 'áéíóúüñÁÉÍÓÚÜÑ'
        while self.cur() and (self.cur() in vc or self.cur().isalnum()):
            s += self.cur()
            self.adv()
        tt = self.keywords.get(s)
        if tt:
            return Token(tt, s, sl, sc)
        if s and s[0].isupper():
            return Token(TokenType.TYPE_ID, s, sl, sc)
        return Token(TokenType.IDENTIFIER, s, sl, sc)

    def tokenize(self):
        while self.cur():
            self.skip_ws()
            if not self.cur():
                break
            c = self.cur()
            if c == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.column))
                self.adv()
                continue
            if self.skip_comment():
                continue
            if c.isdigit():
                self.tokens.append(self.read_num())
                continue
            if c in '"\'':
                self.tokens.append(self.read_str())
                continue
            if c.isalpha() or c == '_' or c in 'áéíóúüñÁÉÍÓÚÜÑ':
                self.tokens.append(self.read_id())
                continue

            l, co = self.line, self.column

            # 3-char operators
            t3 = c + (self.pk(1) or '') + (self.pk(2) or '')
            if t3 == '..=':
                self.adv(); self.adv(); self.adv()
                self.tokens.append(Token(TokenType.RANGE, t3, l, co))
                continue
            if t3 == '...':
                self.adv(); self.adv(); self.adv()
                self.tokens.append(Token(TokenType.SPREAD, t3, l, co))
                continue

            # 2-char operators
            t2 = c + (self.pk() or '')
            ops2 = {
                '==': TokenType.EQUAL, '!=': TokenType.NOT_EQUAL,
                '<=': TokenType.LESS_EQUAL, '>=': TokenType.GREATER_EQUAL,
                '+=': TokenType.PLUS_ASSIGN, '-=': TokenType.MINUS_ASSIGN,
                '*=': TokenType.MULTIPLY_ASSIGN, '/=': TokenType.DIVIDE_ASSIGN,
                '**': TokenType.POWER, '->': TokenType.ARROW,
                '=>': TokenType.FAT_ARROW, '..': TokenType.RANGE,
                '|>': TokenType.PIPELINE, '::': TokenType.DOUBLE_COLON,
                '<<': TokenType.LSHIFT, '>>': TokenType.RSHIFT,
            }
            if t2 in ops2:
                self.adv(); self.adv()
                self.tokens.append(Token(ops2[t2], t2, l, co))
                continue

            # 1-char operators
            ops1 = {
                '+': TokenType.PLUS, '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY, '/': TokenType.DIVIDE,
                '%': TokenType.PERCENT, '<': TokenType.LESS,
                '>': TokenType.GREATER, '=': TokenType.ASSIGN,
                '&': TokenType.AMPERSAND, '|': TokenType.BIT_OR,
                '^': TokenType.BIT_XOR, '~': TokenType.BIT_NOT,
                '?': TokenType.QUESTION, '!': TokenType.EXCLAMATION,
                '@': TokenType.AT, '#': TokenType.HASH,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
                ',': TokenType.COMMA, '.': TokenType.DOT,
                ':': TokenType.COLON, ';': TokenType.SEMICOLON,
                '\\': TokenType.PIPE,
            }
            if c in ops1:
                self.adv()
                self.tokens.append(Token(ops1[c], c, l, co))
                continue

            raise LexerError(f"Caracter inesperado: '{c}'", self.line, self.column)

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens


def tokenize_string(source, debug=False):
    lex = Lexer(source)
    toks = lex.tokenize()
    if debug:
        for i, t in enumerate(toks):
            print(f"  {i}: {t}")
    return toks