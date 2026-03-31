from .lexer import Token, TokenType
from .ast_nodes import *
from typing import List


class ParseError(Exception):
    def __init__(self, message, token=None):
        self.token = token
        loc = f" en L{token.line}:C{token.column}" if token else ""
        super().__init__(f"Error de sintaxis{loc}: {message}")


TYPE_TOKENS = {
    TokenType.INT, TokenType.ENTERO,
    TokenType.FLOAT, TokenType.DECIMAL,
    TokenType.CHAR, TokenType.BOOL, TokenType.BOOLEANO,
    TokenType.VOID, TokenType.DOUBLE, TokenType.LONG,
    TokenType.SHORT, TokenType.BYTE,
    TokenType.STR, TokenType.STRING, TokenType.TEXTO,
}

LOW_TYPE_NAMES = {
    'int', 'entero', 'float', 'decimal', 'char', 'bool', 'booleano',
    'void', 'double', 'long', 'short', 'byte', 'str', 'string', 'texto',
    'ptr', 'puntero',
}

# AMPLIADO: Todas las keywords que pueden usarse como identificadores
IDENTIFIER_LIKE_TOKENS = {
    TokenType.IDENTIFIER,
    TokenType.Y, TokenType.O, TokenType.NO,
    TokenType.EN, TokenType.ES, TokenType.DE,
    TokenType.OK, TokenType.ERR,
    TokenType.CANAL, TokenType.CHANNEL,
    TokenType.TAREA, TokenType.TASK,
    TokenType.ESPERAR, TokenType.AWAIT,
    TokenType.NUEVO, TokenType.NEW,
    TokenType.USAR, TokenType.USE,
    TokenType.MODULO, TokenType.MODULE,
    TokenType.MEDIO, TokenType.MID,
    TokenType.BAJO, TokenType.LOW,
    TokenType.MUTABLE, TokenType.MUT,
    TokenType.CONSTANTE, TokenType.CONST,
    TokenType.PUBLICO, TokenType.PUBLIC, TokenType.PUB,
    TokenType.PRIVADO, TokenType.PRIVATE,
    TokenType.ESTATICO, TokenType.STATIC,
    TokenType.PUNTERO, TokenType.PTR,
    TokenType.RESERVAR, TokenType.ALLOC,
    TokenType.LIBERAR, TokenType.FREE,
    TokenType.ASYNC,
    TokenType.RASGO, TokenType.TRAIT,
    TokenType.INTERFAZ, TokenType.INTERFACE,
    TokenType.APLICAR, TokenType.APPLY,
    TokenType.IMPLEMENTAR, TokenType.IMPLEMENT,
    TokenType.EXTENDER, TokenType.EXTEND,
    TokenType.LANZAR, TokenType.THROW,
    TokenType.VERIFICAR, TokenType.CHECK,
    TokenType.AFIRMAR, TokenType.ASSERT,
    TokenType.SIZEOF, TokenType.TAMANIO,
    TokenType.ENUMERAR, TokenType.ENUM,
    TokenType.COMO, TokenType.AS,
    TokenType.IMPORTAR, TokenType.IMPORT,
    TokenType.SUPER,
    TokenType.FINALMENTE, TokenType.FINALLY,
    TokenType.CAPTURAR, TokenType.CATCH,
    TokenType.INTENTAR, TokenType.TRY,
    # NUEVOS - Tipos que también pueden ser identificadores
    TokenType.LISTA, TokenType.LIST,
    TokenType.MAPA, TokenType.MAP,
    TokenType.CONJUNTO, TokenType.SET,
    TokenType.TEXTO, TokenType.STRING, TokenType.STR,
    TokenType.ENTERO, TokenType.INT,
    TokenType.DECIMAL, TokenType.FLOAT,
    TokenType.BOOLEANO, TokenType.BOOL,
    TokenType.CHAR, TokenType.BYTE,
    TokenType.DOUBLE, TokenType.LONG, TokenType.SHORT,
    TokenType.VOID,
}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0] if tokens else None
        self.errors = []
        self.in_low_block = False

    def advance(self):
        t = self.current_token
        self.pos += 1
        self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None
        return t

    def check(self, *types):
        return self.current_token and self.current_token.type in types

    def match(self, *types):
        if self.check(*types):
            self.advance()
            return True
        return False

    def skip_nl(self):
        while self.check(TokenType.NEWLINE):
            self.advance()

    def skip_semis(self):
        while self.check(TokenType.NEWLINE, TokenType.SEMICOLON):
            self.advance()

    def expect(self, *types):
        self.skip_nl()
        if self.check(*types):
            return self.advance()
        expected = " o ".join(t.name for t in types)
        actual = self.current_token.type.name if self.current_token else "EOF"
        raise ParseError(f"Se esperaba {expected}, se encontro {actual}", self.current_token)

    def expect_identifier(self):
        self.skip_nl()
        if self.check(*IDENTIFIER_LIKE_TOKENS):
            return self.advance()
        if self.check(TokenType.TYPE_ID):
            return self.advance()
        raise ParseError(f"Se esperaba un identificador", self.current_token)

    def check_identifier(self):
        return self.check(*IDENTIFIER_LIKE_TOKENS) or self.check(TokenType.TYPE_ID)

    def parse(self):
        stmts = []
        self.skip_nl()
        while not self.check(TokenType.EOF):
            s = self.parse_declaration()
            if s:
                stmts.append(s)
            self.skip_nl()
        return Program(stmts)

    def parse_declaration(self):
        self.skip_nl()
        if not self.current_token or self.check(TokenType.EOF):
            return None
        if self.check(TokenType.INICIO, TokenType.START):
            return self.parse_start()
        if self.check(TokenType.FUNCION, TokenType.FUNCTION):
            return self.parse_func()
        if self.check(TokenType.FORMA, TokenType.SHAPE, TokenType.CLASE, TokenType.CLASS):
            return self.parse_shape()
        if self.check(TokenType.PRUEBA, TokenType.TEST):
            return self.parse_test()
        if self.check(TokenType.USAR, TokenType.USE, TokenType.IMPORTAR, TokenType.IMPORT):
            return self.parse_import()
        if self.check(TokenType.BAJO, TokenType.LOW):
            return self.parse_low_block()
        if self.check(TokenType.MEDIO, TokenType.MID):
            return self.parse_level()
        return self.parse_stmt()

    def parse_start(self):
        self.advance()
        self.expect(TokenType.LBRACE)
        s = self.parse_block_stmts()
        self.expect(TokenType.RBRACE)
        return Program(s)

    def parse_block_stmts(self):
        stmts = []
        self.skip_nl()
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            s = self.parse_stmt()
            if s:
                stmts.append(s)
            self.skip_nl()
        return stmts

    def parse_block(self):
        self.expect(TokenType.LBRACE)
        s = self.parse_block_stmts()
        self.expect(TokenType.RBRACE)
        return Block(s)

    def parse_level(self):
        level = 'low' if self.check(TokenType.BAJO, TokenType.LOW) else 'mid'
        self.advance()
        self.skip_nl()
        b = self.parse_block()
        return LevelBlock(level, b.statements)

    def parse_low_block(self):
        self.advance()
        self.skip_nl()
        self.expect(TokenType.LBRACE)
        stmts = []
        self.skip_semis()
        old_low = self.in_low_block
        self.in_low_block = True
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            s = self.parse_low_stmt()
            if s:
                stmts.append(s)
            self.skip_semis()
        self.expect(TokenType.RBRACE)
        self.in_low_block = old_low
        return LowBlock(stmts)

    def _is_type_token(self):
        if self.check(*TYPE_TOKENS):
            return True
        if self.check(TokenType.PUNTERO, TokenType.PTR):
            return True
        if self.check(TokenType.IDENTIFIER) and self.current_token.value in LOW_TYPE_NAMES:
            return True
        return False

    def _read_type_name(self):
        tok = self.advance()
        return tok.value

    def parse_low_stmt(self):
        self.skip_semis()
        if not self.current_token or self.check(TokenType.RBRACE, TokenType.EOF):
            return None
        if self.check(TokenType.LIBERAR, TokenType.FREE):
            return self.parse_low_free_stmt()
        if self.check(TokenType.IDENTIFIER) and self.current_token.value in (
            'decir', 'say', 'imprimir', 'print', 'printf',
            'dir', 'addr', 'direccion',
            'llenar', 'memset', 'copiar_mem', 'memcpy',
        ):
            return self.parse_low_builtin_call()
        if self._is_type_token():
            return self.parse_low_var_decl()
        if self.check(TokenType.SI, TokenType.IF):
            return self.parse_if()
        if self.check(TokenType.MIENTRAS, TokenType.WHILE):
            return self.parse_while()
        if self.check(TokenType.PARA, TokenType.FOR):
            return self.parse_for()
        if self.check(TokenType.REPETIR, TokenType.REPEAT):
            return self.parse_repeat()
        if self.check(TokenType.FUNCION, TokenType.FUNCTION):
            return self.parse_func()
        if self.check(TokenType.DAR, TokenType.GIVE, TokenType.RETURN):
            return self.parse_return()
        if self.check(TokenType.PARAR, TokenType.BREAK, TokenType.STOP):
            self.advance()
            self.match(TokenType.SEMICOLON)
            return Break()
        if self.check(TokenType.CONTINUAR, TokenType.CONTINUE, TokenType.SALTAR, TokenType.SKIP):
            self.advance()
            self.match(TokenType.SEMICOLON)
            return Continue()
        return self.parse_low_assign_or_expr()

    def parse_low_var_decl(self):
        var_type = self._read_type_name()
        is_pointer = False
        if self.check(TokenType.MULTIPLY):
            self.advance()
            is_pointer = True
        name_tok = self.expect_identifier()
        name = name_tok.value
        is_array = False
        array_size = None
        if self.check(TokenType.LBRACKET):
            self.advance()
            is_array = True
            if not self.check(TokenType.RBRACKET):
                array_size = self.parse_expr()
            self.expect(TokenType.RBRACKET)
        value = None
        if self.match(TokenType.ASSIGN):
            value = self.parse_expr()
        self.match(TokenType.SEMICOLON)
        return LowVarDecl(var_type=var_type, name=name, value=value, is_pointer=is_pointer, is_array=is_array, array_size=array_size)

    def parse_low_free_stmt(self):
        self.advance()
        self.expect(TokenType.LPAREN)
        ptr = self.parse_expr()
        self.expect(TokenType.RPAREN)
        self.match(TokenType.SEMICOLON)
        return LowFree(pointer=ptr)

    def parse_low_builtin_call(self):
        name = self.advance().value
        self.expect(TokenType.LPAREN)
        args = []
        self.skip_nl()
        while not self.check(TokenType.RPAREN, TokenType.EOF):
            args.append(self.parse_expr())
            self.skip_nl()
            if not self.match(TokenType.COMMA):
                break
            self.skip_nl()
        self.expect(TokenType.RPAREN)
        self.match(TokenType.SEMICOLON)
        if name in ('dir', 'addr', 'direccion'):
            if args:
                return LowPrintAddr(operand=args[0])
        if name in ('llenar', 'memset'):
            if len(args) >= 3:
                return LowMemset(pointer=args[0], value=args[1], size=args[2])
        if name in ('copiar_mem', 'memcpy'):
            if len(args) >= 3:
                return LowMemcpy(dest=args[0], src=args[1], size=args[2])
        return CallExpr(callee=Identifier(name), args=args)

    def parse_low_assign_or_expr(self):
        if self.check(TokenType.MULTIPLY):
            self.advance()
            target_tok = self.expect_identifier()
            target_name = target_tok.value
            if self.match(TokenType.ASSIGN):
                value = self.parse_expr()
                self.match(TokenType.SEMICOLON)
                return Assignment(target=Identifier(target_name), value=LowPointerOp(operator='deref_assign', operand=value))
            self.match(TokenType.SEMICOLON)
            return LowPointerOp(operator='*', operand=Identifier(target_name))
        if self.check(TokenType.AMPERSAND):
            self.advance()
            operand = self.parse_expr()
            self.match(TokenType.SEMICOLON)
            return LowPointerOp(operator='&', operand=operand)
        expr = self.parse_expr()
        if isinstance(expr, Identifier):
            if self.match(TokenType.ASSIGN):
                v = self.parse_expr()
                self.match(TokenType.SEMICOLON)
                return Assignment(target=expr, value=v)
            if self.match(TokenType.PLUS_ASSIGN):
                v = self.parse_expr()
                self.match(TokenType.SEMICOLON)
                return Assignment(target=expr, value=BinaryOp(expr, '+', v))
            if self.match(TokenType.MINUS_ASSIGN):
                v = self.parse_expr()
                self.match(TokenType.SEMICOLON)
                return Assignment(target=expr, value=BinaryOp(expr, '-', v))
        if isinstance(expr, IndexAccess):
            if self.match(TokenType.ASSIGN):
                v = self.parse_expr()
                self.match(TokenType.SEMICOLON)
                return Assignment(target=expr, value=v)
        if isinstance(expr, MemberAccess):
            if self.match(TokenType.ASSIGN):
                v = self.parse_expr()
                self.match(TokenType.SEMICOLON)
                return Assignment(target=expr, value=v)
        self.match(TokenType.SEMICOLON)
        return expr

    def parse_func(self):
        self.advance()
        self.skip_nl()
        name_tok = self.expect_identifier()
        name = name_tok.value
        self.expect(TokenType.LPAREN)
        params = []
        self.skip_nl()
        while not self.check(TokenType.RPAREN, TokenType.EOF):
            if self.check(TokenType.YO, TokenType.SELF, TokenType.THIS):
                self.advance()
                params.append(Parameter(name='self', is_self=True))
                self.skip_nl()
                if not self.match(TokenType.COMMA):
                    break
                self.skip_nl()
                continue
            pn_tok = self.expect_identifier()
            pn = pn_tok.value
            params.append(Parameter(name=pn))
            self.skip_nl()
            if not self.match(TokenType.COMMA):
                break
            self.skip_nl()
        self.expect(TokenType.RPAREN)
        if self.match(TokenType.ARROW):
            if not self.check(TokenType.LBRACE):
                expr = self.parse_expr()
                return FunctionDef(name=name, params=params, body=[Return(expr)])
        self.skip_nl()
        b = self.parse_block()
        return FunctionDef(name=name, params=params, body=b.statements)

    def parse_shape(self):
        self.advance()
        self.skip_nl()
        name_tok = self.expect_identifier()
        name = name_tok.value
        self.skip_nl()
        self.expect(TokenType.LBRACE)
        fields = []
        methods = []
        self.skip_nl()
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            if self.check(TokenType.FUNCION, TokenType.FUNCTION):
                methods.append(self.parse_func())
            else:
                fn_tok = self.expect_identifier()
                fn = fn_tok.value
                self.expect(TokenType.COLON)
                ft = self._read_type_or_id()
                dv = None
                if self.match(TokenType.ASSIGN):
                    dv = self.parse_expr()
                fields.append(Field(name=fn, type_annotation=ft, default_value=dv))
            self.skip_nl()
        self.expect(TokenType.RBRACE)
        return ShapeDef(name=name, fields=fields, methods=methods)

    def _read_type_or_id(self):
        if self.check(*IDENTIFIER_LIKE_TOKENS):
            return self.advance().value
        if self.check(TokenType.TYPE_ID):
            return self.advance().value
        if self.check(*TYPE_TOKENS):
            return self.advance().value
        for kw_type in [TokenType.ENTERO, TokenType.INT, TokenType.DECIMAL, TokenType.FLOAT,
                       TokenType.TEXTO, TokenType.STRING, TokenType.STR, TokenType.CHAR,
                       TokenType.BOOL, TokenType.BOOLEANO, TokenType.LISTA, TokenType.LIST,
                       TokenType.MAPA, TokenType.MAP]:
            if self.check(kw_type):
                return self.advance().value
        raise ParseError(f"Se esperaba un tipo", self.current_token)

    def parse_test(self):
        self.advance()
        name = self.expect(TokenType.STRING_LIT).value
        self.skip_nl()
        b = self.parse_block()
        return TestDef(name=name, body=b.statements)

    def parse_import(self):
        self.advance()
        parts = [self.expect_identifier().value]
        while self.match(TokenType.DOT):
            parts.append(self.expect_identifier().value)
        mod = '.'.join(parts)
        alias = None
        if self.check(TokenType.COMO, TokenType.AS):
            self.advance()
            alias = self.expect_identifier().value
        return ImportStmt(module=mod, alias=alias)

    def parse_stmt(self):
        self.skip_nl()
        if not self.current_token or self.check(TokenType.EOF):
            return None
        if self.check(TokenType.SI, TokenType.IF):
            return self.parse_if()
        if self.check(TokenType.MIENTRAS, TokenType.WHILE):
            return self.parse_while()
        if self.check(TokenType.PARA, TokenType.FOR):
            return self.parse_for()
        if self.check(TokenType.REPETIR, TokenType.REPEAT):
            return self.parse_repeat()
        if self.check(TokenType.BUCLE, TokenType.LOOP):
            return self.parse_loop()
        if self.check(TokenType.DAR, TokenType.GIVE, TokenType.RETURN):
            return self.parse_return()
        if self.check(TokenType.PARAR, TokenType.BREAK, TokenType.STOP):
            self.advance()
            return Break()
        if self.check(TokenType.CONTINUAR, TokenType.CONTINUE, TokenType.SALTAR, TokenType.SKIP):
            self.advance()
            return Continue()
        if self.check(TokenType.INTENTAR, TokenType.TRY):
            return self.parse_try()
        if self.check(TokenType.COINCIDIR, TokenType.MATCH):
            return self.parse_match()
        if self.check(TokenType.LANZAR, TokenType.THROW):
            self.advance()
            v = self.parse_expr()
            return Throw(value=v)
        if self.check(TokenType.FUNCION, TokenType.FUNCTION):
            return self.parse_func()
        if self.check(TokenType.FORMA, TokenType.SHAPE, TokenType.CLASE, TokenType.CLASS):
            return self.parse_shape()
        if self.check(TokenType.BAJO, TokenType.LOW):
            return self.parse_low_block()
        return self.parse_assign_or_expr()

    def parse_if(self):
        self.advance()
        cond = self.parse_expr()
        self.skip_nl()
        b = self.parse_block()
        elifs = []
        eb = None
        self.skip_nl()
        while self.check(TokenType.ADEMAS, TokenType.ALSO, TokenType.ELIF):
            self.advance()
            ec = self.parse_expr()
            self.skip_nl()
            ebl = self.parse_block()
            elifs.append((ec, ebl.statements))
            self.skip_nl()
        if self.check(TokenType.SINO, TokenType.ELSE):
            self.advance()
            self.skip_nl()
            eblk = self.parse_block()
            eb = eblk.statements
        return IfStatement(condition=cond, then_body=b.statements, elif_parts=elifs, else_body=eb)

    def parse_while(self):
        self.advance()
        c = self.parse_expr()
        self.skip_nl()
        b = self.parse_block()
        return WhileLoop(condition=c, body=b.statements)

    def parse_for(self):
        self.advance()
        v_tok = self.expect_identifier()
        v = v_tok.value
        iv = None
        if self.match(TokenType.COMMA):
            iv_tok = self.expect_identifier()
            iv = iv_tok.value
        self.expect(TokenType.EN, TokenType.IN)
        it = self.parse_expr()
        self.skip_nl()
        b = self.parse_block()
        return ForLoop(variable=v, index_var=iv, iterable=it, body=b.statements)

    def parse_repeat(self):
        self.advance()
        t = self.parse_expr()
        iv = None
        if self.check(TokenType.COMO, TokenType.AS):
            self.advance()
            iv_tok = self.expect_identifier()
            iv = iv_tok.value
        self.skip_nl()
        b = self.parse_block()
        return RepeatLoop(times=t, index_var=iv, body=b.statements)

    def parse_loop(self):
        self.advance()
        self.skip_nl()
        b = self.parse_block()
        return InfiniteLoop(body=b.statements)

    def parse_return(self):
        self.advance()
        if self.check(TokenType.NEWLINE, TokenType.RBRACE, TokenType.EOF, TokenType.SEMICOLON):
            return Return()
        v = self.parse_expr()
        return Return(value=v)

    def parse_try(self):
        self.advance()
        self.skip_nl()
        tb = self.parse_block()
        cv = None
        cb = None
        fb = None
        self.skip_nl()
        if self.check(TokenType.CAPTURAR, TokenType.CATCH):
            self.advance()
            cv_tok = self.expect_identifier()
            cv = cv_tok.value
            self.skip_nl()
            cblk = self.parse_block()
            cb = cblk.statements
        self.skip_nl()
        if self.check(TokenType.FINALMENTE, TokenType.FINALLY):
            self.advance()
            self.skip_nl()
            fblk = self.parse_block()
            fb = fblk.statements
        return TryStatement(try_body=tb.statements, catch_var=cv, catch_body=cb, finally_body=fb)

    def parse_match(self):
        self.advance()
        v = self.parse_expr()
        self.skip_nl()
        self.expect(TokenType.LBRACE)
        cases = []
        self.skip_nl()
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            if self.check(TokenType.IDENTIFIER) and self.current_token.value == '_':
                self.advance()
                pat = WildcardPattern()
            else:
                pat = self.parse_expr()
            self.expect(TokenType.ARROW, TokenType.FAT_ARROW)
            if self.check(TokenType.LBRACE):
                bl = self.parse_block()
                body = bl.statements
            else:
                body = [self.parse_expr()]
            cases.append(MatchCase(pattern=pat, body=body))
            self.skip_nl()
        self.expect(TokenType.RBRACE)
        return MatchStatement(value=v, cases=cases)

    def parse_assign_or_expr(self):
        expr = self.parse_expr()
        if isinstance(expr, Identifier):
            if self.match(TokenType.ASSIGN):
                v = self.parse_expr()
                return Assignment(target=expr, value=v)
            if self.match(TokenType.PLUS_ASSIGN):
                v = self.parse_expr()
                return Assignment(target=expr, value=BinaryOp(expr, '+', v))
            if self.match(TokenType.MINUS_ASSIGN):
                v = self.parse_expr()
                return Assignment(target=expr, value=BinaryOp(expr, '-', v))
            if self.match(TokenType.MULTIPLY_ASSIGN):
                v = self.parse_expr()
                return Assignment(target=expr, value=BinaryOp(expr, '*', v))
            if self.match(TokenType.DIVIDE_ASSIGN):
                v = self.parse_expr()
                return Assignment(target=expr, value=BinaryOp(expr, '/', v))
            if self.match(TokenType.COLON):
                ta = self._read_type_or_id()
                val = None
                if self.match(TokenType.ASSIGN):
                    val = self.parse_expr()
                return VariableDecl(name=expr.name, type_annotation=ta, value=val)
        if isinstance(expr, MemberAccess):
            if self.match(TokenType.ASSIGN):
                v = self.parse_expr()
                return Assignment(target=expr, value=v)
            if self.match(TokenType.PLUS_ASSIGN):
                v = self.parse_expr()
                return Assignment(target=expr, value=BinaryOp(expr, '+', v))
        if isinstance(expr, IndexAccess):
            if self.match(TokenType.ASSIGN):
                v = self.parse_expr()
                return Assignment(target=expr, value=v)
        return expr

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        l = self.parse_and()
        while self.check(TokenType.O, TokenType.OR):
            self.advance()
            r = self.parse_and()
            l = BinaryOp(l, 'or', r)
        return l

    def parse_and(self):
        l = self.parse_eq()
        while self.check(TokenType.Y, TokenType.AND):
            self.advance()
            r = self.parse_eq()
            l = BinaryOp(l, 'and', r)
        return l

    def parse_eq(self):
        l = self.parse_comp()
        while self.check(TokenType.EQUAL, TokenType.NOT_EQUAL):
            op = self.advance().value
            r = self.parse_comp()
            l = BinaryOp(l, op, r)
        return l

    def parse_comp(self):
        l = self.parse_range()
        while self.check(TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL):
            op = self.advance().value
            r = self.parse_range()
            l = BinaryOp(l, op, r)
        return l

    def parse_range(self):
        l = self.parse_add()
        if self.match(TokenType.RANGE):
            r = self.parse_add()
            return BinaryOp(l, '..', r)
        return l

    def parse_add(self):
        l = self.parse_mul()
        while self.check(TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            r = self.parse_mul()
            l = BinaryOp(l, op, r)
        return l

    def parse_mul(self):
        l = self.parse_pow()
        while self.check(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.PERCENT):
            op = self.advance().value
            r = self.parse_pow()
            l = BinaryOp(l, op, r)
        return l

    def parse_pow(self):
        l = self.parse_unary()
        if self.match(TokenType.POWER):
            r = self.parse_pow()
            return BinaryOp(l, '**', r)
        return l

    def parse_unary(self):
        if self.match(TokenType.MINUS):
            o = self.parse_unary()
            return UnaryOp('-', o)
        if self.check(TokenType.NO, TokenType.NOT):
            self.advance()
            o = self.parse_unary()
            return UnaryOp('not', o)
        return self.parse_postfix()

    def parse_postfix(self):
        e = self.parse_primary()
        while True:
            if self.check(TokenType.LPAREN):
                self.advance()
                args = []
                self.skip_nl()
                while not self.check(TokenType.RPAREN, TokenType.EOF):
                    args.append(self.parse_expr())
                    self.skip_nl()
                    if not self.match(TokenType.COMMA):
                        break
                    self.skip_nl()
                self.expect(TokenType.RPAREN)
                e = CallExpr(callee=e, args=args)
            elif self.check(TokenType.DOT):
                self.advance()
                m_tok = self.expect_identifier()
                m = m_tok.value
                if self.check(TokenType.LPAREN):
                    self.advance()
                    args = []
                    self.skip_nl()
                    while not self.check(TokenType.RPAREN, TokenType.EOF):
                        args.append(self.parse_expr())
                        self.skip_nl()
                        if not self.match(TokenType.COMMA):
                            break
                        self.skip_nl()
                    self.expect(TokenType.RPAREN)
                    e = MethodCall(object=e, method=m, args=args)
                else:
                    e = MemberAccess(object=e, member=m)
            elif self.check(TokenType.LBRACKET):
                self.advance()
                self.skip_nl()
                idx = self.parse_expr()
                self.skip_nl()
                self.expect(TokenType.RBRACKET)
                e = IndexAccess(object=e, index=idx)
            else:
                break
        return e

    def parse_primary(self):
        if self.check(TokenType.NUMBER):
            return NumberLiteral(value=self.advance().value)
        if self.check(TokenType.STRING_LIT):
            return StringLiteral(value=self.advance().value)
        if self.check(TokenType.VERDADERO, TokenType.TRUE):
            self.advance()
            return BoolLiteral(value=True)
        if self.check(TokenType.FALSO, TokenType.FALSE):
            self.advance()
            return BoolLiteral(value=False)
        if self.check(TokenType.NADA, TokenType.NONE, TokenType.NULL):
            self.advance()
            return NoneLiteral()
        if self.check(TokenType.LBRACKET):
            return self.parse_list_literal()
        if self.check(TokenType.LPAREN):
            self.advance()
            self.skip_nl()
            e = self.parse_expr()
            self.skip_nl()
            self.expect(TokenType.RPAREN)
            return e
        if self.check(TokenType.YO, TokenType.SELF, TokenType.THIS):
            self.advance()
            return SelfExpr()
        if self.check(TokenType.FUNCION, TokenType.FUNCTION):
            return self.parse_lambda()
        if self.check(TokenType.RESERVAR, TokenType.ALLOC):
            return self._parse_malloc_expr()
        if self.check(TokenType.SIZEOF, TokenType.TAMANIO):
            return self._parse_sizeof_expr()
        if self.check(TokenType.TYPE_ID):
            name = self.advance().value
            if self.current_token and self.current_token.type == TokenType.LBRACE:
                return self._parse_struct_instantiation(name)
            return Identifier(name=name)
        if self.check(*IDENTIFIER_LIKE_TOKENS):
            name = self.advance().value
            return Identifier(name=name)
        if self.check(*TYPE_TOKENS):
            name = self.advance().value
            return Identifier(name=name)
        raise ParseError(f"Token inesperado: {self.current_token.type.name} ({repr(self.current_token.value)})", self.current_token)

    def parse_list_literal(self):
        self.advance()
        elems = []
        self.skip_nl()
        while not self.check(TokenType.RBRACKET, TokenType.EOF):
            elems.append(self.parse_expr())
            self.skip_nl()
            if not self.match(TokenType.COMMA):
                break
            self.skip_nl()
        self.expect(TokenType.RBRACKET)
        return ListLiteral(elements=elems)

    def _parse_struct_instantiation(self, name):
        self.advance()
        fields = {}
        self.skip_nl()
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            fn_tok = self.expect_identifier()
            fn = fn_tok.value
            self.expect(TokenType.COLON)
            fv = self.parse_expr()
            fields[fn] = fv
            self.skip_nl()
            if not self.match(TokenType.COMMA):
                break
            self.skip_nl()
        self.expect(TokenType.RBRACE)
        return StructInstantiation(type_name=name, fields=fields)

    def _parse_sizeof_expr(self):
        self.advance()
        self.expect(TokenType.LPAREN)
        if self._is_type_token():
            target = self._read_type_name()
        elif self.check_identifier():
            target = self.expect_identifier().value
        else:
            target = self.advance().value
        self.expect(TokenType.RPAREN)
        return LowSizeof(target=target)

    def _parse_malloc_expr(self):
        self.advance()
        self.expect(TokenType.LPAREN)
        size = self.parse_expr()
        elem_type = 'int'
        if self.match(TokenType.COMMA):
            if self._is_type_token():
                elem_type = self._read_type_name()
            elif self.check_identifier():
                elem_type = self.expect_identifier().value
            else:
                elem_type = self.advance().value
        self.expect(TokenType.RPAREN)
        return LowMalloc(size=size, element_type=elem_type)

    def parse_lambda(self):
        self.advance()
        self.expect(TokenType.LPAREN)
        params = []
        self.skip_nl()
        while not self.check(TokenType.RPAREN, TokenType.EOF):
            pn_tok = self.expect_identifier()
            pn = pn_tok.value
            params.append(Parameter(name=pn))
            self.skip_nl()
            if not self.match(TokenType.COMMA):
                break
            self.skip_nl()
        self.expect(TokenType.RPAREN)
        if self.match(TokenType.ARROW):
            expr = self.parse_expr()
            return Lambda(params=params, body=[Return(expr)])
        self.skip_nl()
        b = self.parse_block()
        return Lambda(params=params, body=b.statements)