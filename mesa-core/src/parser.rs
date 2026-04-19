// Mesa v4.0.0 - Recursive Descent Parser in Rust
// Parses token streams into Mesa AST

use crate::lexer::{Token, TokenKind};
use crate::ast::{Stmt, Expr, Param};
use crate::value::MesaError;

pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Parser { tokens, pos: 0 }
    }

    fn cur(&self) -> &TokenKind {
        &self.tokens[self.pos.min(self.tokens.len() - 1)].kind
    }

    fn cur_tok(&self) -> &Token {
        &self.tokens[self.pos.min(self.tokens.len() - 1)]
    }

    fn peek(&self, offset: usize) -> Option<&TokenKind> {
        let n = self.pos + offset;
        if n < self.tokens.len() {
            Some(&self.tokens[n].kind)
        } else {
            None
        }
    }

    fn advance(&mut self) -> &TokenKind {
        let k = &self.tokens[self.pos.min(self.tokens.len() - 1)].kind;
        if self.pos < self.tokens.len() - 1 { self.pos += 1; }
        k
    }

    fn expect(&mut self, expected: &TokenKind) -> Result<(), MesaError> {
        if std::mem::discriminant(self.cur()) == std::mem::discriminant(expected) {
            self.advance();
            Ok(())
        } else {
            Err(MesaError::runtime(format!(
                "Error de sintaxis en línea {}: Se esperaba {:?}, se encontró {:?}",
                self.cur_tok().line, expected, self.cur()
            )))
        }
    }

    fn expect_ident(&mut self) -> Result<String, MesaError> {
        match self.cur().clone() {
            TokenKind::Ident(n) => { self.advance(); Ok(n) }
            // Allow common short keywords as identifiers in positions where it is safe
            TokenKind::Y | TokenKind::O | TokenKind::En | TokenKind::In_ | TokenKind::De | TokenKind::Como | TokenKind::As => {
                let s = format!("{:?}", self.cur()).to_lowercase();
                self.advance();
                Ok(s)
            }
            other => Err(MesaError::runtime(format!(
                "Error de sintaxis en línea {}: Se esperaba identificador, se encontró {:?}",
                self.cur_tok().line, other
            )))
        }
    }

    fn skip_nl(&mut self) {
        while matches!(self.cur(), TokenKind::Newline | TokenKind::Semicolon) {
            self.advance();
        }
    }

    fn check_nl_or_eof(&self) -> bool {
        matches!(self.cur(), TokenKind::Newline | TokenKind::Semicolon | TokenKind::Eof | TokenKind::RBrace)
    }

    fn is_stmt_keyword(&self) -> bool {
        matches!(self.cur(),
            TokenKind::Si | TokenKind::If |
            TokenKind::Mientras | TokenKind::While |
            TokenKind::Para | TokenKind::For |
            TokenKind::Funcion | TokenKind::Function |
            TokenKind::Forma | TokenKind::Shape | TokenKind::Class |
            TokenKind::Dar | TokenKind::Return |
            TokenKind::Parar | TokenKind::Break |
            TokenKind::Continuar | TokenKind::Continue |
            TokenKind::Importar | TokenKind::Import |
            TokenKind::Usar | TokenKind::Use |
            TokenKind::Intentar | TokenKind::Try |
            TokenKind::Lanzar | TokenKind::Throw |
            TokenKind::Prueba | TokenKind::Test |
            TokenKind::Coincidir | TokenKind::Match |
            TokenKind::Repetir | TokenKind::Repeat |
            TokenKind::Inicio | TokenKind::Start
        )
    }

    pub fn parse_program(&mut self) -> Result<Vec<Stmt>, MesaError> {
        let mut stmts = Vec::new();
        self.skip_nl();
        while !matches!(self.cur(), TokenKind::Eof) {
            stmts.push(self.parse_stmt()?);
            self.skip_nl();
        }
        Ok(stmts)
    }

    fn parse_block(&mut self) -> Result<Vec<Stmt>, MesaError> {
        self.expect(&TokenKind::LBrace)?;
        let mut stmts = Vec::new();
        self.skip_nl();
        while !matches!(self.cur(), TokenKind::RBrace | TokenKind::Eof) {
            stmts.push(self.parse_stmt()?);
            self.skip_nl();
        }
        self.expect(&TokenKind::RBrace)?;
        Ok(stmts)
    }

    fn parse_stmt(&mut self) -> Result<Stmt, MesaError> {
        self.skip_nl();
        match self.cur().clone() {
            TokenKind::Si | TokenKind::If => self.parse_if(),
            TokenKind::Mientras | TokenKind::While => self.parse_while(),
            TokenKind::Para | TokenKind::For => self.parse_for(),
            TokenKind::Funcion | TokenKind::Function => self.parse_func(),
            TokenKind::Forma | TokenKind::Shape | TokenKind::Class => self.parse_shape(),
            TokenKind::Dar | TokenKind::Return => self.parse_return(),
            TokenKind::Parar | TokenKind::Break => { self.advance(); Ok(Stmt::Break) }
            TokenKind::Continuar | TokenKind::Continue | TokenKind::Saltar | TokenKind::Skip => { self.advance(); Ok(Stmt::Continue) }
            TokenKind::Importar | TokenKind::Import | TokenKind::Usar | TokenKind::Use => self.parse_import(),
            TokenKind::Intentar | TokenKind::Try => self.parse_try(),
            TokenKind::Lanzar | TokenKind::Throw => { self.advance(); let e = self.parse_expr()?; Ok(Stmt::Throw(e)) }
            TokenKind::Coincidir | TokenKind::Match => self.parse_match(),
            TokenKind::Prueba | TokenKind::Test => self.parse_test(),
            TokenKind::Repetir | TokenKind::Repeat => self.parse_repeat(),
            TokenKind::Inicio | TokenKind::Start => {
                self.advance();
                let body = self.parse_block()?;
                Ok(Stmt::Block(body))
            }
            _ => self.parse_expr_stmt(),
        }
    }

    fn parse_if(&mut self) -> Result<Stmt, MesaError> {
        self.advance(); // si / if
        let condition = self.parse_expr()?;
        self.skip_nl();
        let then_body = self.parse_block()?;
        let mut elif_parts = Vec::new();
        let mut else_body = None;

        loop {
            self.skip_nl();
            if matches!(self.cur(), TokenKind::Ademas | TokenKind::Elif | TokenKind::Else) {
                // Check if it is genuine 'else if' / 'ademas'/ 'elif'
                if matches!(self.cur(), TokenKind::Ademas | TokenKind::Elif) {
                    self.advance();
                    let ec = self.parse_expr()?;
                    self.skip_nl();
                    let eb = self.parse_block()?;
                    elif_parts.push((ec, eb));
                } else {
                    // Plain else
                    self.advance();
                    self.skip_nl();
                    else_body = Some(self.parse_block()?);
                    break;
                }
            } else if matches!(self.cur(), TokenKind::Sino) {
                // 'sino' can be plain else
                self.advance();
                self.skip_nl();
                else_body = Some(self.parse_block()?);
                break;
            } else {
                break;
            }
        }

        Ok(Stmt::If { condition, then_body, elif_parts, else_body })
    }

    fn parse_while(&mut self) -> Result<Stmt, MesaError> {
        self.advance();
        let condition = self.parse_expr()?;
        self.skip_nl();
        let body = self.parse_block()?;
        Ok(Stmt::While { condition, body })
    }

    fn parse_for(&mut self) -> Result<Stmt, MesaError> {
        self.advance();
        let item = self.expect_ident()?;
        let mut index = None;
        if self.cur() == &TokenKind::Comma {
            self.advance();
            index = Some(self.expect_ident()?);
        }
        // expect 'en' / 'in'
        if matches!(self.cur(), TokenKind::En | TokenKind::In_) { self.advance(); }
        let iterable = self.parse_expr()?;
        self.skip_nl();
        let body = self.parse_block()?;
        Ok(Stmt::For { item, index, iterable, body })
    }

    fn parse_func(&mut self) -> Result<Stmt, MesaError> {
        self.advance();
        let name = self.expect_ident()?;
        self.expect(&TokenKind::LParen)?;
        let params = self.parse_params()?;
        self.expect(&TokenKind::RParen)?;
        let mut return_type = None;
        let mut body = None;

        if matches!(self.cur(), TokenKind::Arrow | TokenKind::Colon) {
            let tok_kind = self.advance().clone(); // -> or :
            if matches!(self.cur(), TokenKind::LBrace) {
                // Return type omitted, starting block
                body = Some(self.parse_block()?);
            } else {
                // Could be a type or an arrow expression
                if tok_kind == TokenKind::Arrow && !matches!(self.peek(1), Some(TokenKind::LBrace)) {
                    // Arrow function shorthand (implicit return body)
                    let expr = self.parse_expr()?;
                    body = Some(vec![Stmt::Return(Some(expr))]);
                } else {
                    // Type annotation
                    if let TokenKind::Ident(t) = self.cur().clone() {
                        self.advance();
                        return_type = Some(t);
                    }
                }
            }
        }

        if body.is_none() {
            self.skip_nl();
            body = Some(self.parse_block()?);
        }

        Ok(Stmt::FuncDecl { name, params, body: body.unwrap(), return_type })
    }

    fn parse_params(&mut self) -> Result<Vec<Param>, MesaError> {
        let mut params = Vec::new();
        while !matches!(self.cur(), TokenKind::RParen | TokenKind::Eof) {
            let is_self = matches!(self.cur(), TokenKind::Yo | TokenKind::Self_);
            let name = if is_self {
                self.advance();
                "yo".to_string()
            } else {
                self.expect_ident()?
            };
            let type_ann = if matches!(self.cur(), TokenKind::Colon) {
                self.advance();
                if let TokenKind::Ident(t) = self.cur().clone() { self.advance(); Some(t) } else { None }
            } else { None };
            let default = if matches!(self.cur(), TokenKind::Assign) {
                self.advance();
                Some(self.parse_expr()?)
            } else { None };
            params.push(Param { name, type_ann, default, is_self });
            if !matches!(self.cur(), TokenKind::Comma) { break; }
            self.advance();
        }
        Ok(params)
    }

    fn parse_shape(&mut self) -> Result<Stmt, MesaError> {
        self.advance();
        let name = self.expect_ident()?;
        self.skip_nl();
        self.expect(&TokenKind::LBrace)?;
        let mut fields = Vec::new();
        let mut methods = Vec::new();
        self.skip_nl();
        while !matches!(self.cur(), TokenKind::RBrace | TokenKind::Eof) {
            if matches!(self.cur(), TokenKind::Funcion | TokenKind::Function) {
                methods.push(self.parse_func()?);
            } else if let TokenKind::Ident(fname) = self.cur().clone() {
                self.advance();
                let type_ann = if matches!(self.cur(), TokenKind::Colon) {
                    self.advance();
                    if let TokenKind::Ident(t) = self.cur().clone() { self.advance(); Some(t) } else { None }
                } else { None };
                fields.push((fname, type_ann));
            } else {
                self.advance();
            }
            self.skip_nl();
        }
        self.expect(&TokenKind::RBrace)?;
        Ok(Stmt::ShapeDecl { name, fields, methods })
    }

    fn parse_return(&mut self) -> Result<Stmt, MesaError> {
        self.advance();
        if self.check_nl_or_eof() {
            Ok(Stmt::Return(None))
        } else {
            Ok(Stmt::Return(Some(self.parse_expr()?)))
        }
    }

    fn parse_import(&mut self) -> Result<Stmt, MesaError> {
        self.advance();
        let path = if let TokenKind::Ident(n) = self.cur().clone() {
            self.advance();
            n
        } else if let TokenKind::Str(s) = self.cur().clone() {
            self.advance();
            s
        } else {
            return Err(MesaError::runtime("Se esperaba módulo a importar"));
        };
        let alias = if matches!(self.cur(), TokenKind::Como | TokenKind::As) {
            self.advance();
            if let TokenKind::Ident(a) = self.cur().clone() { self.advance(); Some(a) } else { None }
        } else { None };
        Ok(Stmt::Import { path, alias })
    }

    fn parse_try(&mut self) -> Result<Stmt, MesaError> {
        self.advance();
        let body = self.parse_block()?;
        let mut catch_var = None;
        let mut catch_body = Vec::new();
        let mut finally_body = None;
        self.skip_nl();
        if matches!(self.cur(), TokenKind::Capturar | TokenKind::Catch) {
            self.advance();
            if let TokenKind::Ident(v) = self.cur().clone() {
                catch_var = Some(v);
                self.advance();
            }
            catch_body = self.parse_block()?;
        }
        self.skip_nl();
        if matches!(self.cur(), TokenKind::Finalmente | TokenKind::Finally) {
            self.advance();
            finally_body = Some(self.parse_block()?);
        }
        Ok(Stmt::Try { body, catch_var, catch_body, finally_body })
    }

    fn parse_match(&mut self) -> Result<Stmt, MesaError> {
        self.advance();
        let value = self.parse_expr()?;
        self.skip_nl();
        self.expect(&TokenKind::LBrace)?;
        let mut arms = Vec::new();
        self.skip_nl();
        while !matches!(self.cur(), TokenKind::RBrace | TokenKind::Eof) {
            let pattern = self.parse_expr()?;
            if matches!(self.cur(), TokenKind::Arrow | TokenKind::FatArrow) { self.advance(); }
            self.skip_nl();
            let body = self.parse_block()?;
            arms.push((pattern, body));
            self.skip_nl();
        }
        self.expect(&TokenKind::RBrace)?;
        Ok(Stmt::Match { value, arms })
    }

    fn parse_test(&mut self) -> Result<Stmt, MesaError> {
        self.advance();
        let name = if let TokenKind::Str(s) = self.cur().clone() {
            self.advance();
            s
        } else {
            "test".to_string()
        };
        self.skip_nl();
        let body = self.parse_block()?;
        Ok(Stmt::Test { name, body })
    }

    fn parse_repeat(&mut self) -> Result<Stmt, MesaError> {
        self.advance(); // repetir / repeat
        let n = self.parse_expr()?;
        
        let mut var_name = "_".to_string();
        if matches!(self.cur(), TokenKind::Como | TokenKind::As) {
            self.advance();
            var_name = self.expect_ident()?;
        }

        let body = self.parse_block()?;
        // Implement as a for loop over 0..n
        Ok(Stmt::For { 
            item: var_name, 
            index: None,
            iterable: Expr::Range { 
                start: Box::new(Expr::Number(0.0)), 
                end: Box::new(n), 
                inclusive: false 
            }, 
            body 
        })
    }

    fn parse_expr_stmt(&mut self) -> Result<Stmt, MesaError> {
        let expr = self.parse_expr()?;

        // Check for assignment
        if matches!(self.cur(), TokenKind::Assign | TokenKind::PlusAssign | TokenKind::MinusAssign | TokenKind::MulAssign | TokenKind::DivAssign) {
            let kind = self.cur().clone();
            self.advance();
            let value = self.parse_expr()?;
            
            let op = match kind {
                TokenKind::PlusAssign => Some("+"),
                TokenKind::MinusAssign => Some("-"),
                TokenKind::MulAssign => Some("*"),
                TokenKind::DivAssign => Some("/"),
                _ => None,
            };

            if let Some(o) = op {
                return Ok(Stmt::Assign { target: expr.clone(), value: Expr::BinaryOp {
                    left: Box::new(expr),
                    op: o.to_string(),
                    right: Box::new(value)
                }});
            }
            return Ok(Stmt::Assign { target: expr, value });
        }

        // Typed variable declaration: ident: type (= value)?
        if matches!(self.cur(), TokenKind::Colon) {
            if let Expr::Ident(name) = &expr {
                let name = name.clone();
                self.advance(); // colon
                let type_ann = if let TokenKind::Ident(t) = self.cur().clone() { self.advance(); Some(t) } else { None };
                let value = if matches!(self.cur(), TokenKind::Assign) {
                    self.advance();
                    Some(self.parse_expr()?)
                } else { None };
                return Ok(Stmt::VarDecl { name, type_ann, value, is_const: false });
            }
        }

        Ok(Stmt::Expr(expr))
    }

    // === EXPRESSION PARSERS (recursive descent with precedence) ===

    pub fn parse_expr(&mut self) -> Result<Expr, MesaError> {
        self.parse_pipeline()
    }

    fn parse_pipeline(&mut self) -> Result<Expr, MesaError> {
        let mut left = self.parse_range()?;
        while matches!(self.cur(), TokenKind::Pipeline) {
            self.advance();
            let right = self.parse_range()?;
            left = Expr::Pipeline { left: Box::new(left), right: Box::new(right) };
        }
        Ok(left)
    }

    fn parse_range(&mut self) -> Result<Expr, MesaError> {
        let left = self.parse_or()?;
        if matches!(self.cur(), TokenKind::Range | TokenKind::RangeTo) {
            let inclusive = matches!(self.cur(), TokenKind::RangeTo);
            self.advance();
            // Open range support
            if self.check_nl_or_eof() || matches!(self.cur(), TokenKind::RBracket | TokenKind::RParen | TokenKind::Comma) {
                return Ok(Expr::Range { start: Box::new(left), end: Box::new(Expr::Null), inclusive });
            }
            let right = self.parse_or()?;
            return Ok(Expr::Range { start: Box::new(left), end: Box::new(right), inclusive });
        }
        Ok(left)
    }

    fn parse_or(&mut self) -> Result<Expr, MesaError> {
        let mut left = self.parse_and()?;
        while matches!(self.cur(), TokenKind::O | TokenKind::Or) {
            self.advance();
            let right = self.parse_and()?;
            left = Expr::BinaryOp { left: Box::new(left), op: "or".to_string(), right: Box::new(right) };
        }
        Ok(left)
    }

    fn parse_and(&mut self) -> Result<Expr, MesaError> {
        let mut left = self.parse_not()?;
        while matches!(self.cur(), TokenKind::Y | TokenKind::And) {
            self.advance();
            let right = self.parse_not()?;
            left = Expr::BinaryOp { left: Box::new(left), op: "and".to_string(), right: Box::new(right) };
        }
        Ok(left)
    }

    fn parse_not(&mut self) -> Result<Expr, MesaError> {
        if matches!(self.cur(), TokenKind::No | TokenKind::Not | TokenKind::Bang) {
            self.advance();
            let operand = self.parse_not()?;
            return Ok(Expr::UnaryOp { op: "not".to_string(), operand: Box::new(operand) });
        }
        self.parse_compare()
    }

    fn parse_compare(&mut self) -> Result<Expr, MesaError> {
        let mut left = self.parse_add()?;
        loop {
            let op = match self.cur() {
                TokenKind::Eq => "==",
                TokenKind::NotEq => "!=",
                TokenKind::Lt => "<",
                TokenKind::Le => "<=",
                TokenKind::Gt => ">",
                TokenKind::Ge => ">=",
                _ => break,
            }.to_string();
            self.advance();
            let right = self.parse_add()?;
            left = Expr::BinaryOp { left: Box::new(left), op, right: Box::new(right) };
        }
        Ok(left)
    }

    fn parse_add(&mut self) -> Result<Expr, MesaError> {
        let mut left = self.parse_mul()?;
        loop {
            let op = match self.cur() {
                TokenKind::Plus => "+",
                TokenKind::Minus => "-",
                _ => break,
            }.to_string();
            self.advance();
            let right = self.parse_mul()?;
            left = Expr::BinaryOp { left: Box::new(left), op, right: Box::new(right) };
        }
        Ok(left)
    }

    fn parse_mul(&mut self) -> Result<Expr, MesaError> {
        let mut left = self.parse_power()?;
        loop {
            let op = match self.cur() {
                TokenKind::Star => "*",
                TokenKind::Slash => "/",
                TokenKind::Percent => "%",
                _ => break,
            }.to_string();
            self.advance();
            let right = self.parse_power()?;
            left = Expr::BinaryOp { left: Box::new(left), op, right: Box::new(right) };
        }
        Ok(left)
    }

    fn parse_power(&mut self) -> Result<Expr, MesaError> {
        let base = self.parse_unary()?;
        if matches!(self.cur(), TokenKind::Power) {
            self.advance();
            let exp = self.parse_unary()?;
            return Ok(Expr::BinaryOp { left: Box::new(base), op: "**".to_string(), right: Box::new(exp) });
        }
        Ok(base)
    }

    fn parse_unary(&mut self) -> Result<Expr, MesaError> {
        if matches!(self.cur(), TokenKind::Minus) {
            self.advance();
            let operand = self.parse_unary()?;
            return Ok(Expr::UnaryOp { op: "-".to_string(), operand: Box::new(operand) });
        }
        self.parse_postfix()
    }

    fn parse_postfix(&mut self) -> Result<Expr, MesaError> {
        let mut expr = self.parse_primary()?;
        loop {
            match self.cur().clone() {
                TokenKind::LParen => {
                    self.advance();
                    let args = self.parse_args()?;
                    self.expect(&TokenKind::RParen)?;
                    expr = Expr::Call { callee: Box::new(expr), args };
                }
                TokenKind::Dot => {
                    self.advance();
                    let member = if let TokenKind::Ident(m) = self.cur().clone() {
                        self.advance();
                        m
                    } else {
                        return Err(MesaError::runtime("Se esperaba miembro después de '.'"));
                    };
                    if matches!(self.cur(), TokenKind::LParen) {
                        self.advance();
                        let args = self.parse_args()?;
                        self.expect(&TokenKind::RParen)?;
                        expr = Expr::MethodCall { object: Box::new(expr), method: member, args };
                    } else {
                        expr = Expr::MemberAccess { object: Box::new(expr), member };
                    }
                }
                TokenKind::LBracket => {
                    self.advance();
                    let idx = self.parse_expr()?;
                    self.expect(&TokenKind::RBracket)?;
                    expr = Expr::Index { object: Box::new(expr), index: Box::new(idx) };
                }
                _ => break,
            }
        }
        Ok(expr)
    }

    fn parse_args(&mut self) -> Result<Vec<Expr>, MesaError> {
        let mut args = Vec::new();
        self.skip_nl();
        while !matches!(self.cur(), TokenKind::RParen | TokenKind::Eof) {
            args.push(self.parse_expr()?);
            self.skip_nl();
            if !matches!(self.cur(), TokenKind::Comma) { break; }
            self.advance();
            self.skip_nl();
        }
        Ok(args)
    }

    fn parse_primary(&mut self) -> Result<Expr, MesaError> {
        match self.cur().clone() {
            TokenKind::Number(n) => { self.advance(); Ok(Expr::Number(n)) }
            TokenKind::Str(s) => { self.advance(); Ok(Expr::Str(s)) }
            TokenKind::Verdadero | TokenKind::True => { self.advance(); Ok(Expr::Bool(true)) }
            TokenKind::Falso | TokenKind::False => { self.advance(); Ok(Expr::Bool(false)) }
            TokenKind::Nada | TokenKind::None_ | TokenKind::Null => { self.advance(); Ok(Expr::Null) }
            TokenKind::Yo | TokenKind::Self_ => { self.advance(); Ok(Expr::Self_) }
            TokenKind::LParen => {
                self.advance();
                self.skip_nl();
                let e = self.parse_expr()?;
                self.skip_nl();
                self.expect(&TokenKind::RParen)?;
                Ok(e)
            }
            TokenKind::LBracket => {
                self.advance();
                let mut items = Vec::new();
                self.skip_nl();
                while !matches!(self.cur(), TokenKind::RBracket | TokenKind::Eof) {
                    items.push(self.parse_expr()?);
                    self.skip_nl();
                    if !matches!(self.cur(), TokenKind::Comma) { break; }
                    self.advance();
                    self.skip_nl();
                }
                self.expect(&TokenKind::RBracket)?;
                Ok(Expr::List(items))
            }
            TokenKind::LBrace => {
                // Map literal
                self.advance();
                let mut pairs = Vec::new();
                self.skip_nl();
                while !matches!(self.cur(), TokenKind::RBrace | TokenKind::Eof) {
                    let key = if let TokenKind::Ident(k) = self.cur().clone() {
                        self.advance(); k
                    } else if let TokenKind::Str(k) = self.cur().clone() {
                        self.advance(); k
                    } else {
                        break;
                    };
                    self.expect(&TokenKind::Colon)?;
                    let val = self.parse_expr()?;
                    pairs.push((key, val));
                    self.skip_nl();
                    if !matches!(self.cur(), TokenKind::Comma) { break; }
                    self.advance();
                    self.skip_nl();
                }
                self.expect(&TokenKind::RBrace)?;
                Ok(Expr::Map(pairs))
            }
            TokenKind::Funcion | TokenKind::Function => {
                // Lambda
                self.advance();
                self.expect(&TokenKind::LParen)?;
                let params = self.parse_params()?;
                self.expect(&TokenKind::RParen)?;
                self.skip_nl();
                if matches!(self.cur(), TokenKind::Arrow | TokenKind::FatArrow) {
                    self.advance();
                    let e = self.parse_expr()?;
                    Ok(Expr::Lambda { params, body: vec![Stmt::Return(Some(e))] })
                } else {
                    let body = self.parse_block()?;
                    Ok(Expr::Lambda { params, body })
                }
            }
            TokenKind::Ident(_) | TokenKind::Y | TokenKind::O | TokenKind::En | TokenKind::In_ | TokenKind::De | TokenKind::Como | TokenKind::As => {
                let name = self.expect_ident()?;
                // Struct instantiation: TypeName { field: val }
                if name.chars().next().map_or(false, |c| c.is_uppercase())
                    && matches!(self.cur(), TokenKind::LBrace) {
                    self.advance();
                    let mut fields = Vec::new();
                    self.skip_nl();
                    while !matches!(self.cur(), TokenKind::RBrace | TokenKind::Eof) {
                        let fname = self.expect_ident()?;
                        self.expect(&TokenKind::Colon)?;
                        let fval = self.parse_expr()?;
                        fields.push((fname, fval));
                        self.skip_nl();
                        if !matches!(self.cur(), TokenKind::Comma) { break; }
                        self.advance();
                        self.skip_nl();
                    }
                    self.expect(&TokenKind::RBrace)?;
                    return Ok(Expr::StructInit { name, fields });
                }
                Ok(Expr::Ident(name))
            }
            _ => {
                let tok = self.cur_tok().clone();
                Err(MesaError::runtime(format!(
                    "Error de sintaxis en línea {}: token inesperado {:?}",
                    tok.line, tok.kind
                )))
            }
        }
    }
}


