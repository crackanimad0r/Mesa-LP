// Mesa v4.0.0 - Native Lexer in Rust
// Tokenizes Mesa source code into a stream of tokens

#[derive(Debug, Clone, PartialEq)]
pub enum TokenKind {
    // Literals
    Number(f64),
    Str(String),
    Bool(bool),
    Null,

    // Identifiers & Keywords
    Ident(String),

    // Keywords - Spanish
    Si, Sino, Ademas, Mientras, Para, En,
    Funcion, Dar, Forma, Yo, De,
    Y, O, No, Verdadero, Falso, Nada,
    Inicio, Modulo, Usar, Importar, Como,
    Prueba, Verificar, Afirmar,
    Coincidir, Intentar, Capturar, Finalmente, Lanzar,
    Parar, Continuar, Saltar,
    Constante, Mutable, Publico, Privado,
    Bajo, Medio, Super, Tarea, Esperar,
    Repetir, Bucle,

    // Keywords - English
    If, Else, Elif, While, For, In_, 
    Function, Return, Class, Shape, Self_,
    And, Or, Not, True, False, None_,
    Start, Module, Use, Import, As,
    Test, Check, Assert,
    Match, Try, Catch, Finally, Throw,
    Break, Continue, Skip,
    Const, Mut, Pub, Private_,
    Low, Mid, Super_, Task, Await,
    Repeat, Loop_,

    // Operators
    Plus, Minus, Star, Slash, Percent, Power,
    Eq, NotEq, Lt, Le, Gt, Ge,
    Assign, PlusAssign, MinusAssign, MulAssign, DivAssign,
    Arrow, FatArrow, Pipeline, Range, Spread, RangeTo,
    Amp, BitOr, BitXor, BitNot, LShift, RShift,
    Question, Bang, At, Hash, BackSlash,
    DoubleColon,

    // Delimiters
    LParen, RParen, LBrace, RBrace, LBracket, RBracket,
    Comma, Dot, Colon, Semicolon,

    // Misc
    Newline,
    Eof,
}

#[derive(Debug, Clone)]
pub struct Token {
    pub kind: TokenKind,
    pub line: usize,
    pub col: usize,
}

impl Token {
    pub fn new(kind: TokenKind, line: usize, col: usize) -> Self {
        Token { kind, line, col }
    }
}

pub struct Lexer {
    source: Vec<char>,
    pos: usize,
    line: usize,
    col: usize,
}

impl Lexer {
    pub fn new(source: &str) -> Self {
        Lexer {
            source: source.chars().collect(),
            pos: 0,
            line: 1,
            col: 1,
        }
    }

    fn cur(&self) -> Option<char> {
        self.source.get(self.pos).copied()
    }

    fn peek(&self, offset: usize) -> Option<char> {
        self.source.get(self.pos + offset).copied()
    }

    fn advance(&mut self) -> Option<char> {
        let c = self.source.get(self.pos).copied();
        if let Some(ch) = c {
            if ch == '\n' {
                self.line += 1;
                self.col = 1;
            } else {
                self.col += 1;
            }
            self.pos += 1;
        }
        c
    }

    fn skip_ws(&mut self) {
        while let Some(c) = self.cur() {
            if c == ' ' || c == '\t' || c == '\r' {
                self.advance();
            } else {
                break;
            }
        }
    }

    fn skip_comment(&mut self) -> bool {
        if self.cur() == Some('-') && self.peek(1) == Some('-') {
            while let Some(c) = self.cur() {
                if c == '\n' { break; }
                self.advance();
            }
            return true;
        }
        false
    }

    fn read_number(&mut self, start_line: usize, start_col: usize) -> Token {
        let mut s = String::new();
        
        // Hexadecimal support
        if self.cur() == Some('0') && (self.peek(1) == Some('x') || self.peek(1) == Some('X')) {
            s.push('0'); s.push('x');
            self.advance(); self.advance(); // skip 0x
            while let Some(c) = self.cur() {
                if c.is_ascii_hexdigit() {
                    s.push(c);
                    self.advance();
                } else {
                    break;
                }
            }
            let val = u64::from_str_radix(&s[2..], 16).unwrap_or(0);
            return Token::new(TokenKind::Number(val as f64), start_line, start_col);
        }

        let mut has_dot = false;
        while let Some(c) = self.cur() {
            if c.is_ascii_digit() {
                s.push(c);
                self.advance();
            } else if c == '.' && !has_dot && self.peek(1).map_or(false, |n| n.is_ascii_digit()) {
                has_dot = true;
                s.push(c);
                self.advance();
            } else {
                break;
            }
        }
        let num: f64 = s.parse().unwrap_or(0.0);
        Token::new(TokenKind::Number(num), start_line, start_col)
    }

    fn read_string(&mut self, quote: char, start_line: usize, start_col: usize) -> Token {
        self.advance(); // skip opening quote
        let mut s = String::new();
        loop {
            match self.cur() {
                None => break,
                Some('\\') => {
                    self.advance();
                    match self.cur() {
                        Some('n') => { s.push('\n'); self.advance(); }
                        Some('t') => { s.push('\t'); self.advance(); }
                        Some('r') => { s.push('\r'); self.advance(); }
                        Some('\\') => { s.push('\\'); self.advance(); }
                        Some(c) if c == quote => { s.push(quote); self.advance(); }
                        Some(c) => { s.push(c); self.advance(); }
                        None => break,
                    }
                }
                Some(c) if c == quote => { self.advance(); break; }
                Some(c) => { s.push(c); self.advance(); }
            }
        }
        Token::new(TokenKind::Str(s), start_line, start_col)
    }

    fn read_ident(&mut self, start_line: usize, start_col: usize) -> Token {
        let mut s = String::new();
        while let Some(c) = self.cur() {
            if c.is_alphanumeric() || c == '_' || "áéíóúüñÁÉÍÓÚÜÑ".contains(c) {
                s.push(c);
                self.advance();
            } else {
                break;
            }
        }

        // Check for "sino si" or "else if" composed keywords
        if s == "sino" || s == "else" {
            let mut tmp = self.pos;
            while tmp < self.source.len() && (self.source[tmp] == ' ' || self.source[tmp] == '\t') {
                tmp += 1;
            }
            if tmp + 1 < self.source.len() && 
               ((self.source[tmp] == 's' && self.source[tmp + 1] == 'i') || 
                (self.source[tmp] == 'i' && self.source[tmp + 1] == 'f')) {
                let after = tmp + 2;
                if after >= self.source.len() || (!self.source[after].is_alphanumeric() && self.source[after] != '_') {
                    self.pos = after;
                    return if s == "sino" { Token::new(TokenKind::Ademas, start_line, start_col) } 
                           else { Token::new(TokenKind::Elif, start_line, start_col) };
                }
            }
        }

        let kind = keyword_or_ident(&s);
        Token::new(kind, start_line, start_col)
    }

    pub fn tokenize(&mut self) -> Vec<Token> {
        let mut tokens = Vec::new();

        loop {
            self.skip_ws();
            if self.skip_comment() { continue; }

            let line = self.line;
            let col = self.col;

            match self.cur() {
                None => { tokens.push(Token::new(TokenKind::Eof, line, col)); break; }
                Some('\n') => {
                    self.advance();
                    tokens.push(Token::new(TokenKind::Newline, line, col));
                }
                Some(c) if c.is_ascii_digit() => {
                    tokens.push(self.read_number(line, col));
                }
                Some(c) if c == '"' || c == '\'' => {
                    tokens.push(self.read_string(c, line, col));
                }
                Some(c) if c.is_alphabetic() || c == '_' || "áéíóúüñÁÉÍÓÚÜÑ".contains(c) => {
                    tokens.push(self.read_ident(line, col));
                }
                Some(c) => {
                    let next = self.peek(1);
                    let next2 = self.peek(2);

                    // 3-char operators
                    if let (Some(n), Some(n2)) = (next, next2) {
                        let t3 = format!("{}{}{}", c, n, n2);
                        if t3 == "..=" { self.advance(); self.advance(); self.advance(); tokens.push(Token::new(TokenKind::RangeTo, line, col)); continue; }
                        if t3 == "..." { self.advance(); self.advance(); self.advance(); tokens.push(Token::new(TokenKind::Spread, line, col)); continue; }
                    }

                    // 2-char operators
                    if let Some(n) = next {
                        let t2 = format!("{}{}", c, n);
                        let kind2 = match t2.as_str() {
                            "==" => Some(TokenKind::Eq), "!=" => Some(TokenKind::NotEq),
                            "<=" => Some(TokenKind::Le), ">=" => Some(TokenKind::Ge),
                            "+=" => Some(TokenKind::PlusAssign), "-=" => Some(TokenKind::MinusAssign),
                            "*=" => Some(TokenKind::MulAssign), "/=" => Some(TokenKind::DivAssign),
                            "**" => Some(TokenKind::Power), "->" => Some(TokenKind::Arrow),
                            "=>" => Some(TokenKind::FatArrow), ".." => Some(TokenKind::Range),
                            "|>" => Some(TokenKind::Pipeline), "::" => Some(TokenKind::DoubleColon),
                            "<<" => Some(TokenKind::LShift), ">>" => Some(TokenKind::RShift),
                            _ => None,
                        };
                        if let Some(k) = kind2 {
                            self.advance(); self.advance();
                            tokens.push(Token::new(k, line, col));
                            continue;
                        }
                    }

                    // 1-char operators
                    let kind1 = match c {
                        '+' => Some(TokenKind::Plus), '-' => Some(TokenKind::Minus),
                        '*' => Some(TokenKind::Star), '/' => Some(TokenKind::Slash),
                        '%' => Some(TokenKind::Percent), '<' => Some(TokenKind::Lt),
                        '>' => Some(TokenKind::Gt), '=' => Some(TokenKind::Assign),
                        '&' => Some(TokenKind::Amp), '|' => Some(TokenKind::BitOr),
                        '^' => Some(TokenKind::BitXor), '~' => Some(TokenKind::BitNot),
                        '?' => Some(TokenKind::Question), '!' => Some(TokenKind::Bang),
                        '@' => Some(TokenKind::At), '#' => Some(TokenKind::Hash),
                        '(' => Some(TokenKind::LParen), ')' => Some(TokenKind::RParen),
                        '{' => Some(TokenKind::LBrace), '}' => Some(TokenKind::RBrace),
                        '[' => Some(TokenKind::LBracket), ']' => Some(TokenKind::RBracket),
                        ',' => Some(TokenKind::Comma), '.' => Some(TokenKind::Dot),
                        ':' => Some(TokenKind::Colon), ';' => Some(TokenKind::Semicolon),
                        '\\' => Some(TokenKind::BackSlash),
                        _ => None,
                    };
                    if let Some(k) = kind1 {
                        self.advance();
                        tokens.push(Token::new(k, line, col));
                    } else {
                        self.advance(); // skip unknown
                    }
                }
            }
        }

        tokens
    }
}

fn keyword_or_ident(s: &str) -> TokenKind {
    match s {
        "si" => TokenKind::Si,
        "sino" => TokenKind::Sino,
        "ademas" | "además" => TokenKind::Ademas,
        "mientras" => TokenKind::Mientras,
        "para" => TokenKind::Para,
        "en" => TokenKind::En,
        "funcion" | "función" => TokenKind::Funcion,
        "dar" => TokenKind::Dar,
        "forma" => TokenKind::Forma,
        "yo" => TokenKind::Yo,
        "de" => TokenKind::De,
        "y" => TokenKind::Y,
        "o" => TokenKind::O,
        "no" => TokenKind::No,
        "verdadero" => TokenKind::Verdadero,
        "falso" => TokenKind::Falso,
        "nada" => TokenKind::Nada,
        "inicio" => TokenKind::Inicio,
        "modulo" | "módulo" => TokenKind::Modulo,
        "usar" => TokenKind::Usar,
        "importar" => TokenKind::Importar,
        "como" => TokenKind::Como,
        "prueba" => TokenKind::Prueba,
        "verificar" => TokenKind::Verificar,
        "afirmar" => TokenKind::Afirmar,
        "coincidir" => TokenKind::Coincidir,
        "intentar" => TokenKind::Intentar,
        "capturar" => TokenKind::Capturar,
        "finalmente" => TokenKind::Finalmente,
        "lanzar" => TokenKind::Lanzar,
        "parar" => TokenKind::Parar,
        "continuar" => TokenKind::Continuar,
        "saltar" => TokenKind::Saltar,
        "constante" => TokenKind::Constante,
        "mutable" => TokenKind::Mutable,
        "publico" | "público" => TokenKind::Publico,
        "privado" => TokenKind::Privado,
        "bajo" => TokenKind::Bajo,
        "medio" => TokenKind::Medio,
        "super" => TokenKind::Super,
        "tarea" => TokenKind::Tarea,
        "esperar" => TokenKind::Esperar,
        "repetir" => TokenKind::Repetir,
        "bucle" => TokenKind::Bucle,
        // English
        "if" => TokenKind::If,
        "else" => TokenKind::Else,
        "elif" => TokenKind::Elif,
        "while" => TokenKind::While,
        "for" => TokenKind::For,
        "in" => TokenKind::In_,
        "function" => TokenKind::Function,
        "return" | "give" => TokenKind::Return,
        "class" | "shape" => TokenKind::Shape,
        "self" | "this" => TokenKind::Self_,
        "and" => TokenKind::And,
        "or" => TokenKind::Or,
        "not" => TokenKind::Not,
        "true" => TokenKind::True,
        "false" => TokenKind::False,
        "none" | "null" => TokenKind::None_,
        "start" => TokenKind::Start,
        "module" => TokenKind::Module,
        "use" => TokenKind::Use,
        "import" => TokenKind::Import,
        "as" => TokenKind::As,
        "test" => TokenKind::Test,
        "check" => TokenKind::Check,
        "assert" => TokenKind::Assert,
        "match" => TokenKind::Match,
        "try" => TokenKind::Try,
        "catch" => TokenKind::Catch,
        "finally" => TokenKind::Finally,
        "throw" => TokenKind::Throw,
        "break" | "stop" => TokenKind::Break,
        "continue" | "skip" => TokenKind::Continue,
        "const" => TokenKind::Const,
        "mut" => TokenKind::Mut,
        "pub" => TokenKind::Pub,
        "private" => TokenKind::Private_,
        "low" => TokenKind::Low,
        "mid" => TokenKind::Mid,
        "task" => TokenKind::Task,
        "await" => TokenKind::Await,
        "async" => TokenKind::Await,
        "repeat" => TokenKind::Repeat,
        "loop" => TokenKind::Loop_,
        _ => TokenKind::Ident(s.to_string()),
    }
}
