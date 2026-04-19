// Mesa v4.0.0 — Tree-Walking Interpreter (Pure Rust, No Python)

use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use crate::ast::{Stmt, Expr, Param};
use crate::env::Env;
use crate::value::{MesaValue, MesaError, ErrorKind, MesaFunc, MesaShape, MesaInstance, NativeFn};
use regex::Regex;
use sha2::{Sha256, Digest};
use md5;
use base64::{Engine as _, engine::general_purpose};
use uuid::Uuid;
use bcrypt::{hash, verify, DEFAULT_COST};
use rusqlite::Connection;
use chrono::TimeZone;
use std::process::Command;

#[derive(Clone)]
pub struct Interpreter {
    pub env: Arc<Mutex<Env>>,
    pub web_html: Arc<Mutex<String>>,
    pub x86_code: Arc<Mutex<Vec<u8>>>,
    pub x86_labels: Arc<Mutex<HashMap<String, usize>>>,
    pub x86_fixups: Arc<Mutex<Vec<(String, usize, u8, u32)>>>, // (label, offset, type, base_addr)
}

impl Interpreter {
    pub fn new() -> Self {
        let env = Arc::new(Mutex::new(Env::new()));
        let web_html = Arc::new(Mutex::new(String::new()));
        let x86_code = Arc::new(Mutex::new(Vec::new()));
        let x86_labels = Arc::new(Mutex::new(HashMap::new()));
        let x86_fixups = Arc::new(Mutex::new(Vec::new()));
        let interp = Interpreter { env, web_html, x86_code, x86_labels, x86_fixups };
        interp.register_builtins();
        interp
    }

    fn def(&self, name: &str, val: MesaValue) {
        self.env.lock().unwrap().define(name.to_string(), val);
    }

    fn native(&self, name: &str, f: impl Fn(Vec<MesaValue>) -> Result<MesaValue, MesaError> + Send + Sync + 'static) {
        let af: NativeFn = Arc::new(f);
        self.def(name, MesaValue::NativeFunc(name.to_string(), af));
    }

    pub fn define_env(&mut self, key: &str, val: String) {
        self.env.lock().unwrap().define(key.to_string(), MesaValue::Str(val));
    }

    pub fn run(&mut self, stmts: &[Stmt]) -> Result<MesaValue, MesaError> {
        let mut last = MesaValue::Null;
        for stmt in stmts { last = self.exec(stmt)?; }
        Ok(last)
    }

    fn run_block_in_env(&mut self, stmts: &[Stmt], child: Arc<Mutex<Env>>) -> Result<MesaValue, MesaError> {
        let old = std::mem::replace(&mut self.env, child);
        let mut r = Ok(MesaValue::Null);
        for s in stmts { r = self.exec(s); if r.is_err() { break; } }
        self.env = old;
        r
    }

    fn run_block(&mut self, stmts: &[Stmt]) -> Result<MesaValue, MesaError> {
        let child = Arc::new(Mutex::new(Env::new_child(self.env.clone())));
        self.run_block_in_env(stmts, child)
    }

    pub fn exec(&mut self, stmt: &Stmt) -> Result<MesaValue, MesaError> {
        match stmt {
            Stmt::Expr(e) => self.eval(e),
            Stmt::VarDecl { name, value, .. } => {
                let v = value.as_ref().map(|e| self.eval(e)).transpose()?.unwrap_or(MesaValue::Null);
                self.env.lock().unwrap().define(name.clone(), v);
                Ok(MesaValue::Null)
            }
            Stmt::Assign { target, value } => {
                let v = self.eval(value)?;
                self.assign(target, v)
            }
            Stmt::FuncDecl { name, params, body, .. } => {
                let f = MesaFunc { name: name.clone(), params: params.clone(), body: body.clone(), closure: self.env.clone() };
                self.env.lock().unwrap().define(name.clone(), MesaValue::Func(Arc::new(f)));
                Ok(MesaValue::Null)
            }
            Stmt::ShapeDecl { name, fields, methods } => {
                let mut mmap = HashMap::new();
                for m in methods {
                    if let Stmt::FuncDecl { name: mn, params, body, .. } = m {
                        mmap.insert(mn.clone(), MesaFunc { name: mn.clone(), params: params.clone(), body: body.clone(), closure: self.env.clone() });
                    }
                }
                let flds: Vec<String> = fields.iter().map(|(f,_)| f.clone()).collect();
                let shape = MesaShape { name: name.clone(), fields: flds, methods: mmap };
                self.env.lock().unwrap().define(name.clone(), MesaValue::Shape(Arc::new(shape)));
                Ok(MesaValue::Null)
            }
            Stmt::If { condition, then_body, elif_parts, else_body } => {
                if self.eval(condition)?.is_truthy() {
                    return self.run_block(then_body);
                }
                for (ec, eb) in elif_parts {
                    if self.eval(ec)?.is_truthy() { return self.run_block(eb); }
                }
                if let Some(eb) = else_body { return self.run_block(eb); }
                Ok(MesaValue::Null)
            }
            Stmt::While { condition, body } => {
                loop {
                    if !self.eval(condition)?.is_truthy() { break; }
                    match self.run_block(body) {
                        Err(MesaError { kind: ErrorKind::Break, .. }) => break,
                        Err(MesaError { kind: ErrorKind::Continue, .. }) => continue,
                        Err(e) => return Err(e),
                        Ok(_) => {}
                    }
                }
                Ok(MesaValue::Null)
            }
            Stmt::For { item: var, index, iterable, body } => {
                let items = match self.eval(iterable)? {
                    MesaValue::List(l) => l.lock().unwrap().clone(),
                    MesaValue::Range(s, e, inc) => {
                        let step = if s <= e { 1.0 } else { -1.0 };
                        let mut res = Vec::new();
                        let mut curr = s;
                        let end_val = if e == -1.0 { 0.0 } else { e }; // Placeholder if open, but For usually has end
                        // Note: For open ranges in For loop, it might need better handling
                        // But usually Ranges in For have end.
                        let real_end = if e == -1.0 { 1000000.0 } else { e }; // Safety cap
                        let limit = if inc { real_end + (step as f64).signum() * 0.1 } else { real_end };
                        while (step > 0.0 && curr < limit) || (step < 0.0 && curr > limit) {
                            res.push(MesaValue::Num(curr));
                            curr += step;
                        }
                        res
                    }
                    MesaValue::Str(s) => s.chars().map(|c| MesaValue::Str(c.to_string())).collect(),
                    _ => return Err(MesaError::runtime("Solo se puede iterar listas, textos o rangos")),
                };
                for (i, item) in items.into_iter().enumerate() {
                    self.env.lock().unwrap().define(var.clone(), item);
                    if let Some(idx_var) = index {
                        self.env.lock().unwrap().define(idx_var.clone(), MesaValue::Num(i as f64));
                    }
                    match self.run_block(body) {
                        Err(MesaError { kind: ErrorKind::Break, .. }) => break,
                        Err(MesaError { kind: ErrorKind::Continue, .. }) => continue,
                        Err(e) => return Err(e),
                        Ok(_) => {}
                    }
                }
                Ok(MesaValue::Null)
            }
        
            Stmt::Return(e) => {
                let v = e.as_ref().map(|ex| self.eval(ex)).transpose()?.unwrap_or(MesaValue::Null);
                Err(MesaError { message: "return".into(), kind: ErrorKind::Return(v) })
            }
            Stmt::Break => Err(MesaError { message: "break".into(), kind: ErrorKind::Break }),
            Stmt::Continue => Err(MesaError { message: "continue".into(), kind: ErrorKind::Continue }),
            Stmt::Throw(e) => {
                let v = self.eval(e)?;
                Err(MesaError { message: format!("{}", v), kind: ErrorKind::Throw(v) })
            }
            Stmt::Try { body, catch_var, catch_body, finally_body } => {
                let res = self.run_block(body);
                let out = match res {
                    Err(MesaError { kind: ErrorKind::Return(_) | ErrorKind::Break | ErrorKind::Continue, .. }) => return res,
                    Err(e) => {
                        if let Some(v) = catch_var { self.env.lock().unwrap().define(v.clone(), MesaValue::Str(e.message.clone())); }
                        self.run_block(catch_body)
                    }
                    ok => ok,
                };
                if let Some(fin) = finally_body { let _ = self.run_block(fin); }
                out
            }
            Stmt::Import { path, alias } => { self.load_module(path, alias.as_deref()) }
            Stmt::Match { value, arms } => {
                let v = self.eval(value)?;
                for (pat, body) in arms {
                    let pv = self.eval(pat)?;
                    if v == pv || matches!(&pv, MesaValue::Str(s) if s == "_") {
                        return self.run_block(body);
                    }
                }
                Ok(MesaValue::Null)
            }
            Stmt::Test { name, body } => {
                match self.run_block(body) {
                    Ok(_) => println!("  ✅ {}", name),
                    Err(e) => println!("  ❌ {} — {}", name, e.message),
                }
                Ok(MesaValue::Null)
            }
            Stmt::Block(stmts) => self.run_block(stmts),
        }
    }

    pub fn eval(&mut self, expr: &Expr) -> Result<MesaValue, MesaError> {
        match expr {
            Expr::Number(n) => Ok(MesaValue::Num(*n)),
            Expr::Str(s) => {
                let mut result = s.clone();
                if s.contains('{') && s.contains('}') {
                    let mut replacements = Vec::new();
                    let mut start = 0;
                    while let Some(open) = result[start..].find('{') {
                        let actual_open = start + open;
                        if let Some(close) = result[actual_open..].find('}') {
                            let actual_close = actual_open + close;
                            let inner = &result[actual_open + 1..actual_close];
                            // Attempt to parse and eval inner as expression
                            use crate::lexer::Lexer;
                            use crate::parser::Parser;
                            let mut lexer = Lexer::new(inner);
                            let tokens = lexer.tokenize();
                            let mut parser = Parser::new(tokens);
                            if let Ok(expr) = parser.parse_expr() {
                                if let Ok(val) = self.eval(&expr) {
                                    replacements.push((actual_open, actual_close + 1, val.to_string()));
                                }
                            }
                            start = actual_close + 1;
                        } else { break; }
                    }
                    for (s, e, val) in replacements.into_iter().rev() {
                        result.replace_range(s..e, &val);
                    }
                }
                Ok(MesaValue::Str(result))
            }
            Expr::Bool(b) => Ok(MesaValue::Bool(*b)),
            Expr::Null => Ok(MesaValue::Null),
            Expr::Self_ => self.env.lock().unwrap().get("yo"),
            Expr::Ident(n) => self.env.lock().unwrap().get(n),
            Expr::List(items) => {
                let mut v = Vec::new();
                for i in items { v.push(self.eval(i)?); }
                Ok(MesaValue::List(Arc::new(Mutex::new(v))))
            }
            Expr::Map(pairs) => {
                let mut m = HashMap::new();
                for (k, v) in pairs { m.insert(k.clone(), self.eval(v)?); }
                Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
            }
            Expr::BinaryOp { left, op, right } => self.eval_binary(left, op, right),
            Expr::UnaryOp { op, operand } => {
                let v = self.eval(operand)?;
                match op.as_str() {
                    "-" => if let MesaValue::Num(n) = v { Ok(MesaValue::Num(-n)) } else { Err(MesaError::runtime("'-' requiere número")) },
                    "not" => Ok(MesaValue::Bool(!v.is_truthy())),
                    _ => Err(MesaError::runtime(format!("Operador '{}' desconocido", op))),
                }
            }
            Expr::Call { callee, args } => {
                let f = self.eval(callee)?;
                let av: Result<Vec<_>, _> = args.iter().map(|a| self.eval(a)).collect();
                self.call_value(f, av?)
            }
            Expr::MethodCall { object, method, args } => {
                let obj = self.eval(object)?;
                let av: Result<Vec<_>, _> = args.iter().map(|a| self.eval(a)).collect();
                self.call_method(obj, object, method, av?)
            }
            Expr::MemberAccess { object, member } => {
                let obj = self.eval(object)?;
                self.get_member(obj, member)
            }
            Expr::Index { object, index } => {
                let obj = self.eval(object)?;
                let idx = self.eval(index)?;
                match (obj, idx) {
                    (MesaValue::List(l), MesaValue::Num(n)) => {
                        let l = l.lock().unwrap();
                        let i = if n < 0.0 { (l.len() as f64 + n) as usize } else { n as usize };
                        l.get(i).cloned().ok_or_else(|| MesaError::runtime("Índice fuera de rango"))
                    }
                    (MesaValue::List(l), MesaValue::Range(s, e, inc)) => {
                        let items = l.lock().unwrap();
                        let start = s as usize;
                        let end = if e == -1.0 { items.len() } else { if inc { e as usize + 1 } else { e as usize } };
                        let start = start.min(items.len());
                        let end = end.min(items.len());
                        let res: Vec<MesaValue> = items.iter().skip(start).take(end - start).cloned().collect();
                        Ok(MesaValue::List(Arc::new(Mutex::new(res))))
                    }
                    (MesaValue::Map(m), MesaValue::Str(k)) => Ok(m.lock().unwrap().get(&k).cloned().unwrap_or(MesaValue::Null)),
                    (MesaValue::Str(s), MesaValue::Num(n)) => {
                        s.chars().nth(n as usize).map(|c| MesaValue::Str(c.to_string())).ok_or_else(|| MesaError::runtime("Índice fuera de rango"))
                    }
                    (MesaValue::Str(s), MesaValue::Range(s_idx, e_idx, inc)) => {
                        let start = s_idx as usize;
                        let end = if e_idx == -1.0 { s.len() } else { if inc { e_idx as usize + 1 } else { e_idx as usize } };
                        let start = start.min(s.len());
                        let end = end.min(s.len());
                        let res: String = s.chars().skip(start).take(end - start).collect();
                        Ok(MesaValue::Str(res))
                    }
                    _ => Err(MesaError::runtime("No se puede indexar este tipo")),
                }
            }
            Expr::StructInit { name, fields } => {
                let shape_v = self.env.lock().unwrap().get(name)?;
                if let MesaValue::Shape(shape) = shape_v {
                    let mut fm = HashMap::new();
                    for (k, v) in fields { fm.insert(k.clone(), self.eval(v)?); }
                    let inst = MesaInstance { shape_name: shape.name.clone(), fields: fm, methods: shape.methods.clone() };
                    Ok(MesaValue::Instance(Arc::new(Mutex::new(inst))))
                } else { Err(MesaError::runtime(format!("'{}' no es una forma", name))) }
            }
            Expr::Lambda { params, body } => {
                let f = MesaFunc { name: "<lambda>".into(), params: params.clone(), body: body.clone(), closure: self.env.clone() };
                Ok(MesaValue::Func(Arc::new(f)))
            }
            Expr::Pipeline { left, right } => {
                let lv = self.eval(left)?;
                let rf = self.eval(right)?;
                self.call_value(rf, vec![lv])
            }
            Expr::Range { start, end, inclusive } => {
                let s = self.eval(start)?;
                let e = self.eval(end)?;
                match (s, e) {
                    (MesaValue::Num(si), MesaValue::Num(ei)) => Ok(MesaValue::Range(si, ei, *inclusive)),
                    (MesaValue::Num(si), MesaValue::Null) => Ok(MesaValue::Range(si, -1.0, *inclusive)), // -1.0 as sentinel for auto-end
                    _ => Err(MesaError::runtime("Rango requiere números")),
                }
            }
            Expr::Conditional { cond, then, else_ } => {
                if self.eval(cond)?.is_truthy() { self.eval(then) } else { self.eval(else_) }
            }
        }
    }

    fn assign(&mut self, target: &Expr, val: MesaValue) -> Result<MesaValue, MesaError> {
        match target {
            Expr::Ident(n) => { self.env.lock().unwrap().set(n, val); Ok(MesaValue::Null) }
            Expr::MemberAccess { object, member } => {
                let obj = self.eval(object)?;
                if let MesaValue::Instance(inst) = obj {
                    inst.lock().unwrap().set(member, val);
                    Ok(MesaValue::Null)
                } else { Err(MesaError::runtime("No se puede asignar miembro")) }
            }
            Expr::Index { object, index } => {
                let idx = self.eval(index)?;
                if let Expr::Ident(name) = object.as_ref() {
                    if let Ok(MesaValue::List(l)) = self.env.lock().unwrap().get(name) {
                        if let MesaValue::Num(n) = idx { 
                            l.lock().unwrap()[n as usize] = val; 
                            return Ok(MesaValue::Null); 
                        }
                    }
                }
                Err(MesaError::runtime("Asignación de índice no soportada"))
            }
            _ => Err(MesaError::runtime("Objetivo de asignación inválido")),
        }
    }

    fn eval_binary(&mut self, left: &Expr, op: &str, right: &Expr) -> Result<MesaValue, MesaError> {
        if op == "and" { let l = self.eval(left)?; if !l.is_truthy() { return Ok(MesaValue::Bool(false)); } return Ok(MesaValue::Bool(self.eval(right)?.is_truthy())); }
        if op == "or" { let l = self.eval(left)?; if l.is_truthy() { return Ok(MesaValue::Bool(true)); } return Ok(MesaValue::Bool(self.eval(right)?.is_truthy())); }
        let lv = self.eval(left)?;
        let rv = self.eval(right)?;
        match (op, &lv, &rv) {
            ("+", MesaValue::Num(a), MesaValue::Num(b)) => Ok(MesaValue::Num(a + b)),
            ("+", MesaValue::Str(a), _) => Ok(MesaValue::Str(format!("{}{}", a, rv))),
            ("+", MesaValue::List(a), MesaValue::List(b)) => { 
                let mut c = a.lock().unwrap().clone(); 
                c.extend(b.lock().unwrap().clone()); 
                Ok(MesaValue::List(Arc::new(Mutex::new(c)))) 
            }
            ("-", MesaValue::Num(a), MesaValue::Num(b)) => Ok(MesaValue::Num(a - b)),
            ("*", MesaValue::Num(a), MesaValue::Num(b)) => Ok(MesaValue::Num(a * b)),
            ("*", MesaValue::Str(s), MesaValue::Num(n)) => Ok(MesaValue::Str(s.repeat(*n as usize))),
            ("/", MesaValue::Num(a), MesaValue::Num(b)) => { if *b == 0.0 { Err(MesaError::runtime("División por cero")) } else { Ok(MesaValue::Num(a / b)) } }
            ("%", MesaValue::Num(a), MesaValue::Num(b)) => Ok(MesaValue::Num(a % b)),
            ("**", MesaValue::Num(a), MesaValue::Num(b)) => Ok(MesaValue::Num(a.powf(*b))),
            ("==", a, b) => Ok(MesaValue::Bool(a == b)),
            ("!=", a, b) => Ok(MesaValue::Bool(a != b)),
            ("<", MesaValue::Num(a), MesaValue::Num(b)) => Ok(MesaValue::Bool(a < b)),
            ("<=", MesaValue::Num(a), MesaValue::Num(b)) => Ok(MesaValue::Bool(a <= b)),
            (">", MesaValue::Num(a), MesaValue::Num(b)) => Ok(MesaValue::Bool(a > b)),
            (">=", MesaValue::Num(a), MesaValue::Num(b)) => Ok(MesaValue::Bool(a >= b)),
            ("in", _, MesaValue::List(l)) => Ok(MesaValue::Bool(l.lock().unwrap().contains(&lv))),
            ("in", MesaValue::Str(sub), MesaValue::Str(s)) => Ok(MesaValue::Bool(s.contains(sub.as_str()))),
            _ => Err(MesaError::runtime(format!("Operación '{}' no soportada entre {} y {}", op, lv.type_name(), rv.type_name()))),
        }
    }

    pub fn call_value(&mut self, func: MesaValue, args: Vec<MesaValue>) -> Result<MesaValue, MesaError> {
        match func {
            MesaValue::Func(f) => self.call_func(&f.clone(), args),
            MesaValue::NativeFunc(_, nf) => nf(args),
            MesaValue::Lambda(params, body) => {
                let f = MesaFunc {
                    name: "anonymous".to_string(),
                    params: (*params).clone(),
                    body: (*body).clone(),
                    closure: self.env.clone(), // Should probably be closure from Lambda if we had one
                };
                self.call_func(&f, args)
            }
            MesaValue::Shape(shape) => {
                let mut fields = HashMap::new();
                for (i, fname) in shape.fields.iter().enumerate() {
                    fields.insert(fname.clone(), args.get(i).cloned().unwrap_or(MesaValue::Null));
                }
                Ok(MesaValue::Instance(Arc::new(Mutex::new(MesaInstance { shape_name: shape.name.clone(), fields, methods: shape.methods.clone() }))))
            }
            other => Err(MesaError::runtime(format!("'{}' no es invocable", other))),
        }
    }

    pub fn call_func(&mut self, func: &MesaFunc, args: Vec<MesaValue>) -> Result<MesaValue, MesaError> {
        let call_env = Arc::new(Mutex::new(Env::new_child(func.closure.clone())));
        {
            let mut env = call_env.lock().unwrap();
            for (i, param) in func.params.iter().enumerate() {
                if param.is_self { continue; }
                let v = args.get(i).cloned().unwrap_or(MesaValue::Null);
                env.define(param.name.clone(), v);
            }
        }
        let body = func.body.clone();
        let res = self.run_block_in_env(&body, call_env);
        match res {
            Err(MesaError { kind: ErrorKind::Return(v), .. }) => Ok(v),
            other => other,
        }
    }

    fn call_method(&mut self, obj: MesaValue, _obj_expr: &Expr, method: &str, args: Vec<MesaValue>) -> Result<MesaValue, MesaError> {
        match obj.clone() {
            MesaValue::Instance(inst_arc) => {
                let mfunc = inst_arc.lock().unwrap().methods.get(method).cloned();
                if let Some(mf) = mfunc {
                    let call_env = Arc::new(Mutex::new(Env::new_child(mf.closure.clone())));
                    call_env.lock().unwrap().define("yo".to_string(), MesaValue::Instance(inst_arc.clone()));
                    call_env.lock().unwrap().define("self".to_string(), MesaValue::Instance(inst_arc.clone()));
                    let non_self: Vec<&Param> = mf.params.iter().filter(|p| !p.is_self).collect();
                    for (i, param) in non_self.iter().enumerate() {
                        let v = args.get(i).cloned().unwrap_or(MesaValue::Null);
                        call_env.lock().unwrap().define(param.name.clone(), v);
                    }
                    let body = mf.body.clone();
                    let res = self.run_block_in_env(&body, call_env.clone());
                    // sync mutated instance fields back
                    if let Ok(MesaValue::Instance(new_inst)) = call_env.lock().unwrap().get("yo") {
                        *inst_arc.lock().unwrap() = new_inst.lock().unwrap().clone();
                    }
                    return match res { Err(MesaError { kind: ErrorKind::Return(v), .. }) => Ok(v), other => other };
                }
                Err(MesaError::runtime(format!("Método '{}' no encontrado en instancia", method)))
            }
            MesaValue::List(l) => self.list_method(l, method, args),
            MesaValue::Str(s) => self.str_method(s, method, args),
            MesaValue::Map(m) => self.map_method(m, method, args),
            _ => Err(MesaError::runtime(format!("Tipo {} no tiene métodos", obj.type_name()))),
        }
    }

    fn list_method(&mut self, l_arc: Arc<Mutex<Vec<MesaValue>>>, method: &str, args: Vec<MesaValue>) -> Result<MesaValue, MesaError> {
        let mut l = l_arc.lock().unwrap();
        match method {
            "agregar" | "add" | "push" | "append" | "adjuntar" | "insertar" => {
                let v = args.into_iter().next().unwrap_or(MesaValue::Null);
                if let MesaValue::List(other_l) = v { 
                    l.extend(other_l.lock().unwrap().clone()); 
                } else { 
                    l.push(v); 
                }
                Ok(MesaValue::Null)
            }
            "remover" | "remove" | "pop" => {
                let v = if let Some(MesaValue::Num(i)) = args.first() { l.remove(*i as usize) } else { l.pop().unwrap_or(MesaValue::Null) };
                Ok(v)
            }
            "tamaño" | "len" | "longitud" | "length" | "size" => Ok(MesaValue::Num(l.len() as f64)),
            "vacío" | "vacio" | "empty" | "is_empty" => Ok(MesaValue::Bool(l.is_empty())),
            "contiene" | "contains" => Ok(MesaValue::Bool(l.contains(args.first().unwrap_or(&MesaValue::Null)))),
            "invertir" | "reverse" => { l.reverse(); Ok(MesaValue::List(l_arc.clone())) }
            "ordenar" | "sort" => { l.sort_by(|a,b| match (a,b) { (MesaValue::Num(x),MesaValue::Num(y)) => x.partial_cmp(y).unwrap_or(std::cmp::Ordering::Equal), (MesaValue::Str(x),MesaValue::Str(y)) => x.cmp(y), _ => std::cmp::Ordering::Equal }); Ok(MesaValue::List(l_arc.clone())) }
            "unir" | "join" => { let sep = args.first().map(|v| v.to_string()).unwrap_or_default(); Ok(MesaValue::Str(l.iter().map(|v| v.to_string()).collect::<Vec<_>>().join(&sep))) }
            "primero" | "first" => Ok(l.first().cloned().unwrap_or(MesaValue::Null)),
            "último" | "ultimo" | "last" => Ok(l.last().cloned().unwrap_or(MesaValue::Null)),
            "copiar" | "copy" | "clone" => Ok(MesaValue::List(Arc::new(Mutex::new(l.clone())))),
            "indice" | "index" | "find" => { let t = args.first().unwrap_or(&MesaValue::Null); Ok(MesaValue::Num(l.iter().position(|x| x == t).map(|i| i as f64).unwrap_or(-1.0))) }
            "mapear" | "map" => {
                if let Some(f) = args.into_iter().next() {
                    let mut res = Vec::new();
                    for item in l.iter() { res.push(self.call_value(f.clone(), vec![item.clone()])?); }
                    Ok(MesaValue::List(Arc::new(Mutex::new(res))))
                } else { Ok(MesaValue::List(l_arc.clone())) }
            }
            "filtrar" | "filter" => {
                if let Some(f) = args.into_iter().next() {
                    let mut res = Vec::new();
                    for item in l.iter() { if self.call_value(f.clone(), vec![item.clone()])?.is_truthy() { res.push(item.clone()); } }
                    Ok(MesaValue::List(Arc::new(Mutex::new(res))))
                } else { Ok(MesaValue::List(l_arc.clone())) }
            }
            "reducir" | "reduce" => {
                if args.len() >= 2 { let f = args[0].clone(); let mut acc = args[1].clone(); for item in l.iter() { acc = self.call_value(f.clone(), vec![acc, item.clone()])?; } Ok(acc) }
                else { Err(MesaError::runtime("reducir requiere función e inicial")) }
            }
            _ => Err(MesaError::runtime(format!("Método de lista '{}' no existe", method))),
        }
    }

    fn str_method(&self, s: String, method: &str, args: Vec<MesaValue>) -> Result<MesaValue, MesaError> {
        let arg0 = args.first().map(|v| v.to_string()).unwrap_or_default();
        match method {
            "mayusculas" | "upper" => Ok(MesaValue::Str(s.to_uppercase())),
            "minusculas" | "lower" => Ok(MesaValue::Str(s.to_lowercase())),
            "tamaño" | "len" | "longitud" | "length" => Ok(MesaValue::Num(s.chars().count() as f64)),
            "recortar" | "trim" => Ok(MesaValue::Str(s.trim().to_string())),
            "separar" | "split" | "dividir" => {
                let arg0 = args.first().map(|v| v.to_string()).unwrap_or_default();
                Ok(MesaValue::List(Arc::new(Mutex::new(s.split(&*arg0).map(|p| MesaValue::Str(p.to_string())).collect()))))
            }
            "reemplazar" | "replace" => { let to = args.get(1).map(|v| v.to_string()).unwrap_or_default(); Ok(MesaValue::Str(s.replace(&*arg0, &*to))) }
            "contiene" | "contains" => Ok(MesaValue::Bool(s.contains(&*arg0))),
            "empieza_con" | "starts_with" => Ok(MesaValue::Bool(s.starts_with(&*arg0))),
            "termina_con" | "ends_with" => Ok(MesaValue::Bool(s.ends_with(&*arg0))),
            _ => Err(MesaError::runtime(format!("Método de texto '{}' no existe", method))),
        }
    }

    fn map_method(&self, m_arc: Arc<Mutex<HashMap<String, MesaValue>>>, method: &str, args: Vec<MesaValue>) -> Result<MesaValue, MesaError> {
        let m = m_arc.lock().unwrap();
        let arg0 = args.first().map(|v| v.to_string()).unwrap_or_default();
        match method {
            "obtener" | "get" => Ok(m.get(&arg0).cloned().unwrap_or(MesaValue::Null)),
            "claves" | "keys" => Ok(MesaValue::List(Arc::new(Mutex::new(m.keys().map(|k| MesaValue::Str(k.clone())).collect())))),
            "valores" | "values" => Ok(MesaValue::List(Arc::new(Mutex::new(m.values().cloned().collect())))),
            "contiene" | "contains" | "tiene" | "has" => Ok(MesaValue::Bool(m.contains_key(&arg0))),
            "tamaño" | "len" => Ok(MesaValue::Num(m.len() as f64)),
            _ => Err(MesaError::runtime(format!("Método de mapa '{}' no existe", method))),
        }
    }

    fn get_member(&self, obj: MesaValue, member: &str) -> Result<MesaValue, MesaError> {
        match obj {
            MesaValue::Instance(inst) => inst.lock().unwrap().get(member).cloned().ok_or_else(|| MesaError::runtime(format!("Campo '{}' no existe", member))),
            MesaValue::Map(m) => Ok(m.lock().unwrap().get(member).cloned().unwrap_or(MesaValue::Null)),
            _ => Err(MesaError::runtime(format!("No se puede acceder a '{}' en {}", member, obj.type_name()))),
        }
    }

    fn load_module(&mut self, path: &str, _alias: Option<&str>) -> Result<MesaValue, MesaError> {
        let mut curr = std::env::current_dir().unwrap_or_else(|_| std::path::PathBuf::from("."));
        let mut searches = vec![
            format!("{}.mesa", path),
            format!("{}/{}.mesa", path, path),
            format!("mesa_pkgs/{}/{}.mesa", path, path),
            format!("mesa_pkgs/{}.mesa", path),
        ];
        
        // Search upwards for packages and mesa_pkgs
        let mut temp_curr = curr.clone();
        for _ in 0..4 {
            searches.push(temp_curr.join(path).join(format!("{}.mesa", path)).to_string_lossy().to_string());
            searches.push(temp_curr.join(format!("{}.mesa", path)).to_string_lossy().to_string());
            searches.push(temp_curr.join("mesa_pkgs").join(path).join(format!("{}.mesa", path)).to_string_lossy().to_string());
            searches.push(temp_curr.join("mesa_pkgs").join(format!("{}.mesa", path)).to_string_lossy().to_string());
            if let Some(p) = temp_curr.parent() { temp_curr = p.to_path_buf(); } else { break; }
        }

        for search in &searches {
            if std::path::Path::new(search).exists() {
                let src = std::fs::read_to_string(search).map_err(|e| MesaError::runtime(e.to_string()))?;
                let tokens = crate::lexer::Lexer::new(&src).tokenize();
                let stmts = crate::parser::Parser::new(tokens).parse_program()?;
                let mod_env = Arc::new(Mutex::new(Env::new_child(self.env.clone())));
                let _ = self.run_block_in_env(&stmts, mod_env.clone());
                for (k, v) in mod_env.lock().unwrap().export_all() {
                    self.env.lock().unwrap().define(k, v);
                }
                return Ok(MesaValue::Null);
            }
        }
        Err(MesaError::runtime(format!("Módulo '{}' no encontrado", path)))
    }

    fn register_builtins(&self) {
        // Standard Library
        self.native("decir", |args| {
            for arg in args { print!("{} ", arg.to_string()); }
            println!();
            Ok(MesaValue::Null)
        });
        self.native("say", |args| {
            for arg in args { print!("{} ", arg.to_string()); }
            println!();
            Ok(MesaValue::Null)
        });
        self.native("imprimir", |args| {
            for arg in args { print!("{}", arg.to_string()); }
            println!();
            Ok(MesaValue::Null)
        });
        self.native("print", |args| {
            for arg in args { print!("{}", arg.to_string()); }
            println!();
            Ok(MesaValue::Null)
        });
        self.native("crear_mapa", |args| {
            let mut m = HashMap::new();
            for i in (0..args.len()).step_by(2) {
                if let (Some(MesaValue::Str(k)), Some(v)) = (args.get(i), args.get(i+1)) {
                    m.insert(k.clone(), v.clone());
                }
            }
            Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
        });
        self.native("crear_lista", |args| {
            Ok(MesaValue::List(Arc::new(Mutex::new(args))))
        });
        self.native("json_bonito", |args| {
            if let Some(v) = args.first() {
                Ok(MesaValue::Str(serde_json::to_string_pretty(&v).unwrap_or_else(|_| format!("{:#?}", v))))
            } else { Ok(MesaValue::Null) }
        });
        self.native("json_parsear", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                let v: serde_json::Value = serde_json::from_str(s).unwrap_or(serde_json::Value::Null);
                Ok(MesaValue::from_json(v))
            } else { Err(MesaError::runtime("json_parsear(json)")) }
        });
        self.native("json_obtener", |args| {
            if let (Some(obj), Some(MesaValue::Str(key))) = (args.get(0), args.get(1)) {
                match obj {
                    MesaValue::Map(m) => Ok(m.lock().unwrap().get(key).cloned().unwrap_or(MesaValue::Null)),
                    MesaValue::Str(s) => {
                        let v: serde_json::Value = serde_json::from_str(s).unwrap_or(serde_json::Value::Null);
                        Ok(MesaValue::from_json(v[key].clone()))
                    }
                    MesaValue::Instance(inst) => Ok(inst.lock().unwrap().fields.get(key).cloned().unwrap_or(MesaValue::Null)),
                    _ => Ok(MesaValue::Null)
                }
            } else { Err(MesaError::runtime("json_obtener(obj, llave)")) }
        });
        self.native("unico", |args| {
            if let Some(MesaValue::List(l_arc)) = args.first() {
                let l = l_arc.lock().unwrap();
                let mut res = Vec::new();
                for item in l.iter() { if !res.contains(item) { res.push(item.clone()); } }
                Ok(MesaValue::List(Arc::new(Mutex::new(res))))
            } else { Err(MesaError::runtime("unico(lista)")) }
        });
        self.native("partir", |args| {
            if let (Some(MesaValue::List(l_arc)), Some(MesaValue::Num(n))) = (args.get(0), args.get(1)) {
                let l = l_arc.lock().unwrap();
                let chunks: Vec<MesaValue> = l.chunks(*n as usize).map(|c| MesaValue::List(Arc::new(Mutex::new(c.to_vec())))).collect();
                Ok(MesaValue::List(Arc::new(Mutex::new(chunks))))
            } else { Err(MesaError::runtime("partir(lista, n)")) }
        });
        self.native("tomar", |args| {
            if let (Some(MesaValue::List(l_arc)), Some(MesaValue::Num(n))) = (args.get(0), args.get(1)) {
                let l = l_arc.lock().unwrap();
                let res: Vec<MesaValue> = l.iter().take(*n as usize).cloned().collect();
                Ok(MesaValue::List(Arc::new(Mutex::new(res))))
            } else { Err(MesaError::runtime("tomar(lista, n)")) }
        });
        
        // Regex
        self.native("regex_buscar", |args| {
            if let (Some(MesaValue::Str(pat)), Some(MesaValue::Str(text))) = (args.get(0), args.get(1)) {
                let re = Regex::new(pat).map_err(|e| MesaError::runtime(format!("Regex error: {}", e)))?;
                if let Some(caps) = re.captures(text) {
                    let mut m = HashMap::new();
                    m.insert("valor".to_string(), MesaValue::Str(caps[0].to_string()));
                    Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
                } else { Ok(MesaValue::Null) }
            } else { Err(MesaError::runtime("regex_buscar(pat, texto)")) }
        });
        self.native("regex_todos", |args| {
            if let (Some(MesaValue::Str(pat)), Some(MesaValue::Str(text))) = (args.get(0), args.get(1)) {
                let re = Regex::new(pat).map_err(|e| MesaError::runtime(format!("Regex error: {}", e)))?;
                let matches: Vec<MesaValue> = re.find_iter(text).map(|m| MesaValue::Str(m.as_str().to_string())).collect();
                Ok(MesaValue::List(Arc::new(Mutex::new(matches))))
            } else { Err(MesaError::runtime("regex_todos(pat, texto)")) }
        });
        self.native("es_email", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                let re = Regex::new(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$").unwrap();
                Ok(MesaValue::Bool(re.is_match(s)))
            } else { Ok(MesaValue::Bool(false)) }
        });
        self.native("es_url", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                Ok(MesaValue::Bool(s.starts_with("http://") || s.starts_with("https://")))
            } else { Ok(MesaValue::Bool(false)) }
        });

        // Crypto
        self.native("md5", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                Ok(MesaValue::Str(format!("{:x}", md5::compute(s))))
            } else { Ok(MesaValue::Null) }
        });
        self.native("sha256", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                let mut hasher = Sha256::new();
                hasher.update(s);
                Ok(MesaValue::Str(format!("{:x}", hasher.finalize())))
            } else { Ok(MesaValue::Null) }
        });
        self.native("generar_uuid", |_| Ok(MesaValue::Str(Uuid::new_v4().to_string())));
        self.native("generar_token", |args| {
            let len = args.first().and_then(|v| if let MesaValue::Num(n) = v { Some(*n as usize) } else { None }).unwrap_or(16);
            use rand::{Rng, thread_rng};
            let s: String = thread_rng().sample_iter(&rand::distributions::Alphanumeric).take(len).map(char::from).collect();
            Ok(MesaValue::Str(s))
        });
        self.native("base64_codificar", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                Ok(MesaValue::Str(general_purpose::STANDARD.encode(s)))
            } else { Ok(MesaValue::Null) }
        });
        self.native("base64_decodificar", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                let d = general_purpose::STANDARD.decode(s).map_err(|_| MesaError::runtime("Base64 error"))?;
                Ok(MesaValue::Str(String::from_utf8_lossy(&d).to_string()))
            } else { Ok(MesaValue::Null) }
        });
        self.native("hash_password", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                let hashed = hash(s, DEFAULT_COST).map_err(|_| MesaError::runtime("Bcrypt error"))?;
                let mut m = HashMap::new();
                m.insert("hash".to_string(), MesaValue::Str(hashed));
                m.insert("salt".to_string(), MesaValue::Str("".to_string())); // bcrypt handles salt internally
                Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
            } else { Ok(MesaValue::Null) }
        });
        self.native("verificar_password", |args| {
            if let (Some(MesaValue::Str(p)), Some(MesaValue::Str(h))) = (args.get(0), args.get(1)) {
                Ok(MesaValue::Bool(verify(p, h).unwrap_or(false)))
            } else { Ok(MesaValue::Bool(false)) }
        });

        // Database
        self.native("db_conectar", |args| {
            let path = args.first().map(|v| v.to_string()).unwrap_or(":memory:".to_string());
            let conn = Connection::open(&path).map_err(|e| MesaError::runtime(format!("DB error: {}", e)))?;
            // Store as Native (we assume it's thread-safe enough inside Mutex)
            Ok(MesaValue::Native(Arc::new(Mutex::new(Box::new(conn)))))
        });
        self.native("db_ejecutar", |args| {
            if let (Some(MesaValue::Native(conn_arc)), Some(MesaValue::Str(sql))) = (args.get(0), args.get(1)) {
                let conn_any = conn_arc.lock().unwrap();
                let conn = conn_any.as_ref().downcast_ref::<Connection>().ok_or_else(|| MesaError::runtime("No es una conexión válida"))?;
                conn.execute(sql, []).map_err(|e| MesaError::runtime(format!("DB exec error: {}", e)))?;
                Ok(MesaValue::Null)
            } else { Err(MesaError::runtime("db_ejecutar(conn, sql)")) }
        });
        self.native("db_insertar", |args| {
            if let (Some(MesaValue::Native(conn_arc)), Some(MesaValue::Str(table)), Some(MesaValue::Map(m_arc))) = (args.get(0), args.get(1), args.get(2)) {
                let conn_any = conn_arc.lock().unwrap();
                let conn = conn_any.as_ref().downcast_ref::<Connection>().ok_or_else(|| MesaError::runtime("No es una conexión válida"))?;
                let m = m_arc.lock().unwrap();
                let keys: Vec<String> = m.keys().cloned().collect();
                let placeholders: Vec<String> = (0..keys.len()).map(|_| "?".to_string()).collect();
                let sql = format!("INSERT INTO {} ({}) VALUES ({})", table, keys.join(", "), placeholders.join(", "));
                let mut stmt = conn.prepare(&sql).map_err(|e| MesaError::runtime(format!("DB prepare error: {}", e)))?;
                let vals: Vec<String> = keys.iter().map(|k| m.get(k).unwrap().to_string()).collect();
                stmt.execute(rusqlite::params_from_iter(vals.iter())).map_err(|e| MesaError::runtime(format!("DB insert error: {}", e)))?;
                Ok(MesaValue::Null)
            } else { Err(MesaError::runtime("db_insertar(conn, tabla, mapa)")) }
        });
        self.native("db_consultar", |args| {
            if let (Some(MesaValue::Native(conn_arc)), Some(MesaValue::Str(sql))) = (args.get(0), args.get(1)) {
                let conn_any = conn_arc.lock().unwrap();
                let conn = conn_any.as_ref().downcast_ref::<Connection>().ok_or_else(|| MesaError::runtime("No es una conexión válida"))?;
                let mut stmt = conn.prepare(sql).map_err(|e| MesaError::runtime(format!("DB prepare error: {}", e)))?;
                let column_count = stmt.column_count();
                let column_names: Vec<String> = (0..column_count).map(|i| stmt.column_name(i).unwrap().to_string()).collect();
                let rows = stmt.query_map([], |row| {
                    let mut m = HashMap::new();
                    for i in 0..column_count {
                        let name = column_names[i].clone();
                        let val = match row.get_ref(i).unwrap() {
                            rusqlite::types::ValueRef::Integer(n) => MesaValue::Num(n as f64),
                            rusqlite::types::ValueRef::Real(n) => MesaValue::Num(n),
                            rusqlite::types::ValueRef::Text(s) => MesaValue::Str(String::from_utf8_lossy(s).into_owned()),
                            rusqlite::types::ValueRef::Blob(b) => MesaValue::Str(general_purpose::STANDARD.encode(b)),
                            rusqlite::types::ValueRef::Null => MesaValue::Null,
                        };
                        m.insert(name, val);
                    }
                    Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
                }).map_err(|e| MesaError::runtime(format!("DB query error: {}", e)))?;
                let mut res = Vec::new();
                for r in rows { res.push(r.map_err(|e| MesaError::runtime(format!("DB row error: {}", e)))?); }
                Ok(MesaValue::List(Arc::new(Mutex::new(res))))
            } else { Err(MesaError::runtime("db_consultar(conn, sql)")) }
        });
        self.native("db_contar", |args| {
            if let (Some(MesaValue::Native(conn_arc)), Some(MesaValue::Str(table))) = (args.get(0), args.get(1)) {
                let conn_any = conn_arc.lock().unwrap();
                let conn = conn_any.as_ref().downcast_ref::<Connection>().ok_or_else(|| MesaError::runtime("No es una conexión válida"))?;
                let count: i64 = conn.query_row(&format!("SELECT COUNT(*) FROM {}", table), [], |row| row.get(0)).map_err(|e| MesaError::runtime(format!("DB count error: {}", e)))?;
                Ok(MesaValue::Num(count as f64))
            } else { Err(MesaError::runtime("db_contar(conn, tabla)")) }
        });
        self.native("db_tablas", |args| {
            if let Some(MesaValue::Native(conn_arc)) = args.first() {
                let conn_any = conn_arc.lock().unwrap();
                let conn = conn_any.as_ref().downcast_ref::<Connection>().ok_or_else(|| MesaError::runtime("No es una conexión válida"))?;
                let mut stmt = conn.prepare("SELECT name FROM sqlite_master WHERE type='table'").unwrap();
                let names: Vec<MesaValue> = stmt.query_map([], |row| Ok(MesaValue::Str(row.get(0)?))).unwrap().map(|r| r.unwrap()).collect();
                Ok(MesaValue::List(Arc::new(Mutex::new(names))))
            } else { Err(MesaError::runtime("db_tablas(conn)")) }
        });
        self.native("db_cerrar", |args| { Ok(MesaValue::Null) }); // SQLite connection closes on drop

        // Concurrency
        self.native("canal_crear", |_| {
            let (tx, rx) = std::sync::mpsc::channel::<MesaValue>();
            let m = HashMap::from([
                ("sender".to_string(), MesaValue::Native(Arc::new(Mutex::new(Box::new(tx))))),
                ("receiver".to_string(), MesaValue::Native(Arc::new(Mutex::new(Box::new(rx))))),
            ]);
            Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
        });
        self.native("enviar", |args| {
            if let (Some(MesaValue::Native(tx_arc)), Some(val)) = (args.get(0), args.get(1)) {
                let tx = tx_arc.lock().unwrap();
                let tx = tx.as_ref().downcast_ref::<std::sync::mpsc::Sender<MesaValue>>().ok_or_else(|| MesaError::runtime("No es un canal válido"))?;
                tx.send(val.clone()).map_err(|_| MesaError::runtime("Error al enviar mensaje"))?;
                Ok(MesaValue::Bool(true))
            } else { Err(MesaError::runtime("enviar(canal, valor)")) }
        });
        self.native("recibir", |args| {
            if let Some(MesaValue::Native(rx_arc)) = args.get(0) {
                let rx = rx_arc.lock().unwrap();
                let rx = rx.as_ref().downcast_ref::<std::sync::mpsc::Receiver<MesaValue>>().ok_or_else(|| MesaError::runtime("No es un canal válido"))?;
                let val = rx.recv().map_err(|_| MesaError::runtime("Error al recibir mensaje"))?;
                Ok(val)
            } else { Err(MesaError::runtime("recibir(canal)")) }
        });

        // CSV
        self.native("csv_escribir", |args| {
            if let (Some(MesaValue::Str(path)), Some(MesaValue::List(l_arc))) = (args.get(0), args.get(1)) {
                let l = l_arc.lock().unwrap();
                let mut content = String::new();
                for item in l.iter() {
                    if let MesaValue::Map(m_arc) = item {
                        let m = m_arc.lock().unwrap();
                        let line: Vec<String> = m.values().map(|v| v.to_string()).collect();
                        content.push_str(&line.join(","));
                        content.push('\n');
                    }
                }
                std::fs::write(path, content).map_err(|e| MesaError::runtime(format!("CSV write error: {}", e)))?;
                Ok(MesaValue::Bool(true))
            } else { Err(MesaError::runtime("csv_escribir(ruta, lista)")) }
        });
        self.native("csv_leer", |args| {
            if let Some(MesaValue::Str(path)) = args.first() {
                let content = std::fs::read_to_string(path).map_err(|e| MesaError::runtime(format!("CSV read error: {}", e)))?;
                let mut res = Vec::new();
                for line in content.lines() {
                    let cols: Vec<MesaValue> = line.split(',').map(|s| MesaValue::Str(s.to_string())).collect();
                    res.push(MesaValue::List(Arc::new(Mutex::new(cols))));
                }
                Ok(MesaValue::List(Arc::new(Mutex::new(res))))
            } else { Err(MesaError::runtime("csv_leer(ruta)")) }
        });

        // Datetime
        self.native("ahora", |_| Ok(MesaValue::Str(chrono::Local::now().to_rfc3339())));
        self.native("timestamp", |_| Ok(MesaValue::Num(chrono::Utc::now().timestamp() as f64)));
        self.native("dia_semana", |_| Ok(MesaValue::Str(chrono::Local::now().format("%A").to_string())));
        self.native("fecha_formato", |args| {
            if let Some(MesaValue::Str(f)) = args.first() { Ok(MesaValue::Str(chrono::Local::now().format(f).to_string())) }
            else { Err(MesaError::runtime("fecha_formato(formato)")) }
        });
        self.native("fecha_sumar", |args| {
            if let (Some(MesaValue::Str(dt_str)), Some(MesaValue::Num(days))) = (args.get(0), args.get(1)) {
                let dt = match chrono::DateTime::parse_from_rfc3339(dt_str) {
                    Ok(d) => Ok(d),
                    Err(_) => {
                        let nd = chrono::NaiveDateTime::parse_from_str(dt_str, "%Y-%m-%d %H:%M:%S")
                            .or_else(|_| chrono::NaiveDateTime::parse_from_str(dt_str, "%Y-%m-%dT%H:%M:%S"));
                        match nd {
                            Ok(n) => Ok(chrono::Local.from_local_datetime(&n).unwrap().fixed_offset()),
                            Err(_) => Err(MesaError::runtime(format!("Fecha inválida: {}", dt_str))),
                        }
                    }
                }?;
                let new_dt = dt + chrono::Duration::days(*days as i64);
                Ok(MesaValue::Str(new_dt.to_rfc3339()))
            } else { Err(MesaError::runtime("fecha_sumar(fecha, dias)")) }
        });

        // Filesystem
        self.native("crear_directorio", |args| {
            if let Some(MesaValue::Str(p)) = args.first() { std::fs::create_dir_all(p).ok(); Ok(MesaValue::Bool(true)) }
            else { Err(MesaError::runtime("crear_directorio(ruta)")) }
        });
        self.native("archivo_escribir", |args| {
            if let (Some(MesaValue::Str(p)), Some(MesaValue::Str(c))) = (args.get(0), args.get(1)) {
                std::fs::write(p, c).map_err(|e| MesaError::runtime(format!("Write error: {}", e)))?;
                Ok(MesaValue::Bool(true))
            } else { Err(MesaError::runtime("archivo_escribir(ruta, contenido)")) }
        });
        self.native("archivo_leer", |args| {
            if let Some(MesaValue::Str(p)) = args.first() {
                let c = std::fs::read_to_string(p).map_err(|e| MesaError::runtime(format!("Read error: {}", e)))?;
                Ok(MesaValue::Str(c))
            } else { Err(MesaError::runtime("archivo_leer(ruta)")) }
        });
        self.native("hash_archivo", |args| {
            if let Some(MesaValue::Str(p)) = args.first() {
                let data = std::fs::read(p).map_err(|e| MesaError::runtime(format!("Hash error: {}", e)))?;
                Ok(MesaValue::Str(format!("{:x}", sha2::Sha256::digest(&data))))
            } else { Err(MesaError::runtime("hash_archivo(ruta)")) }
        });
        self.native("listar_directorio", |args| {
            if let Some(MesaValue::Str(p)) = args.first() {
                let mut res = Vec::new();
                for entry in std::fs::read_dir(p).unwrap() { res.push(MesaValue::Str(entry.unwrap().file_name().into_string().unwrap())); }
                Ok(MesaValue::List(Arc::new(Mutex::new(res))))
            } else { Err(MesaError::runtime("listar_directorio(ruta)")) }
        });

        // HTTP
        self.native("http_get", |args| {
            if let Some(MesaValue::Str(url)) = args.first() {
                let client = reqwest::blocking::Client::new();
                let resp = client.get(url).send().map_err(|e| MesaError::runtime(format!("HTTP GET error: {}", e)))?;
                let mut m = HashMap::new();
                m.insert("status".to_string(), MesaValue::Num(resp.status().as_u16() as f64));
                m.insert("ok".to_string(), MesaValue::Bool(resp.status().is_success()));
                let body = resp.text().unwrap_or_default();
                m.insert("body".to_string(), MesaValue::Str(body));
                Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
            } else { Err(MesaError::runtime("http_get(url)")) }
        });
        self.native("db_cerrar", |_| Ok(MesaValue::Null));

        // X86 Assembler Toolkit
        self.native("x86_nuevo", |args| {
            // We'll append to a global 'asm' list
            Ok(MesaValue::Null)
        });

        // Instruction emitters (these append to 'asm' list in global env)
        let _instr = |name: &'static str, opcode: u8| {
            move |args: &[MesaValue]| -> Result<MesaValue, MesaError> {
                let mut m = HashMap::new();
                m.insert("op".to_string(), MesaValue::Str(name.to_string()));
                m.insert("hex".to_string(), MesaValue::Num(opcode as f64));
                if let Some(arg) = args.first() { m.insert("arg".to_string(), arg.clone()); }
                Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
            }
        };

        self.native("etiqueta", |args| {
            let mut m = HashMap::new();
            m.insert("tipo".to_string(), MesaValue::Str("etiqueta".to_string()));
            m.insert("nombre".to_string(), args.first().cloned().unwrap_or(MesaValue::Null));
            Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
        });

        // Basic instructions
        self.native("modo_video", |args| {
            let mut m = HashMap::new();
            m.insert("op".to_string(), MesaValue::Str("modo_video".to_string()));
            m.insert("val".to_string(), args.first().cloned().unwrap_or(MesaValue::Num(0x13 as f64)));
            Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
        });

        self.native("vram_escribir", |args| {
            let mut m = HashMap::new();
            m.insert("op".to_string(), MesaValue::Str("vram_escribir".to_string()));
            m.insert("off".to_string(), args.get(0).cloned().unwrap_or(MesaValue::Num(0.0)));
            m.insert("val".to_string(), args.get(1).cloned().unwrap_or(MesaValue::Num(0.0)));
            Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
        });

        self.native("leer_puerto", |args| {
            let mut m = HashMap::new();
            m.insert("op".to_string(), MesaValue::Str("in".to_string()));
            m.insert("port".to_string(), args.first().cloned().unwrap_or(MesaValue::Num(0x60 as f64)));
            Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
        });

        self.native("cmp_al", |args| {
            let mut m = HashMap::new();
            m.insert("op".to_string(), MesaValue::Str("cmp_al".to_string()));
            m.insert("val".to_string(), args.first().cloned().unwrap_or(MesaValue::Num(0.0)));
            Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
        });

        self.native("si_igual", |args| {
            let mut m = HashMap::new();
            m.insert("op".to_string(), MesaValue::Str("je".to_string()));
            m.insert("dest".to_string(), args.first().cloned().unwrap_or(MesaValue::Null));
            Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
        });

        self.native("jmp_a", |args| {
            let mut m = HashMap::new();
            m.insert("op".to_string(), MesaValue::Str("jmp".to_string()));
            m.insert("dest".to_string(), args.first().cloned().unwrap_or(MesaValue::Null));
            Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
        });

        self.native("hlt", |_| {
            let mut m = HashMap::new();
            m.insert("op".to_string(), MesaValue::Str("hlt".to_string()));
            Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
        });

        self.native("compilar", |args| {
            if let Some(MesaValue::List(l_arc)) = args.first() {
                let l = l_arc.lock().unwrap();
                let mut bytes = Vec::new();
                // A very simplified x86 "compiler" for demo purposes
                // Real implementation would resolve labels and emit real opcodes
                for _ in l.iter() {
                    bytes.extend_from_slice(&[0x90]); // NOPs for everything for now
                }
                // Let's add at least the video mode 0x13 (MOV AX, 0013h; INT 10h)
                let mut real_bytes = vec![0xB8, 0x13, 0x00, 0xCD, 0x10];
                // And a loop with keyboard read (IN AL, 60h; CMP AL, 01h; JE loop)
                real_bytes.extend_from_slice(&[0xE4, 0x60, 0x3C, 0x01, 0x74, 0xFA, 0xF4]);
                
                Ok(MesaValue::Str(general_purpose::STANDARD.encode(real_bytes)))
            } else { Err(MesaError::runtime("compilar(asm)")) }
        });

        self.native("bootsector", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                let mut code = general_purpose::STANDARD.decode(s).unwrap();
                let mut boot = vec![0; 512];
                for (i, &b) in code.iter().enumerate().take(510) { boot[i] = b; }
                boot[510] = 0x55;
                boot[511] = 0xAA;
                Ok(MesaValue::Str(general_purpose::STANDARD.encode(boot)))
            } else { Err(MesaError::runtime("bootsector(codigo)")) }
        });

        self.native("archivo_escribir_bytes", |args| {
            if let (Some(MesaValue::Str(path)), Some(MesaValue::Str(b64))) = (args.get(0), args.get(1)) {
                let bytes = general_purpose::STANDARD.decode(b64).map_err(|_| MesaError::runtime("Base64 error"))?;
                std::fs::write(path, bytes).map_err(|e| MesaError::runtime(format!("Write error: {}", e)))?;
                Ok(MesaValue::Bool(true))
            } else { Err(MesaError::runtime("archivo_escribir_bytes(ruta, b64)")) }
        });

        self.native("lanzar_qemu", |args| {
            if let Some(MesaValue::Str(path)) = args.first() {
                let status = Command::new("qemu-system-x86_64")
                    .arg("-drive")
                    .arg(format!("format=raw,file={}", path))
                    .spawn();
                match status {
                    Ok(_) => Ok(MesaValue::Bool(true)),
                    Err(e) => Err(MesaError::runtime(format!("QEMU failed: {}", e)))
                }
            } else { Err(MesaError::runtime("lanzar_qemu(ruta)")) }
        });

        // Compression
        self.native("comprimir", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                use std::io::Write;
                let mut encoder = zip::write::ZipWriter::new(std::io::Cursor::new(Vec::new()));
                encoder.start_file("data", zip::write::FileOptions::default()).unwrap();
                encoder.write_all(s.as_bytes()).unwrap();
                let result = encoder.finish().unwrap().into_inner();
                Ok(MesaValue::Str(general_purpose::STANDARD.encode(result)))
            } else { Ok(MesaValue::Null) }
        });
        self.native("descomprimir", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                let data = general_purpose::STANDARD.decode(s).map_err(|_| MesaError::runtime("Zip deco error"))?;
                let mut decoder = zip::read::ZipArchive::new(std::io::Cursor::new(data)).map_err(|_| MesaError::runtime("Zip error"))?;
                let mut file = decoder.by_index(0).unwrap();
                let mut res = String::new();
                use std::io::Read;
                file.read_to_string(&mut res).unwrap();
                Ok(MesaValue::Str(res))
            } else { Ok(MesaValue::Null) }
        });

        // System
        self.native("plataforma", |_| Ok(MesaValue::Str(std::env::consts::OS.to_string())));
        self.native("info_sistema", |_| {
            let mut m = HashMap::new();
            m.insert("pid".to_string(), MesaValue::Num(std::process::id() as f64));
            m.insert("usuario".to_string(), MesaValue::Str(std::env::var("USER").unwrap_or_default()));
            Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
        });
        self.native("ejecutar_comando", |args| {
            if let Some(MesaValue::Str(cmd)) = args.first() {
                let out = std::process::Command::new("sh").arg("-c").arg(cmd).output().map_err(|e| MesaError::runtime(format!("Exec error: {}", e)))?;
                let mut m = HashMap::new();
                m.insert("salida".to_string(), MesaValue::Str(String::from_utf8_lossy(&out.stdout).to_string()));
                Ok(MesaValue::Map(Arc::new(Mutex::new(m))))
            } else { Err(MesaError::runtime("ejecutar_comando(cmd)")) }
        });
        
        // JSON Helper
        self.native("json_parsear", |args| {
            if let Some(MesaValue::Str(s)) = args.first() {
                let v: serde_json::Value = serde_json::from_str(s).map_err(|e| MesaError::runtime(format!("JSON error: {}", e)))?;
                Ok(MesaValue::from_json(v))
            } else { Err(MesaError::runtime("json_parsear(texto)")) }
        });
        self.native("json_obtener", |args| {
            if let (Some(MesaValue::Map(m_arc)), Some(MesaValue::Str(k))) = (args.get(0), args.get(1)) {
                let m = m_arc.lock().unwrap();
                Ok(m.get(k).cloned().unwrap_or(MesaValue::Null))
            } else { Ok(MesaValue::Null) }
        });
        self.native("partir", |args| {
            if let (Some(MesaValue::List(l_arc)), Some(MesaValue::Num(n))) = (args.get(0), args.get(1)) {
                let l = l_arc.lock().unwrap();
                let size = *n as usize;
                let chunks: Vec<MesaValue> = l.chunks(size).map(|c| MesaValue::List(Arc::new(Mutex::new(c.to_vec())))).collect();
                Ok(MesaValue::List(Arc::new(Mutex::new(chunks))))
            } else { Err(MesaError::runtime("partir(lista, n)")) }
        });
        self.native("unico", |args| {
            if let Some(MesaValue::List(l_arc)) = args.first() {
                let l = l_arc.lock().unwrap();
                let mut seen = Vec::new();
                for item in l.iter() {
                    if !seen.contains(item) { seen.push(item.clone()); }
                }
                Ok(MesaValue::List(Arc::new(Mutex::new(seen))))
            } else { Err(MesaError::runtime("unico(lista)")) }
        });
        
        // Functional
        self.native("mapear", { let s_orig = self.clone(); move |args| {
            if let (Some(f), Some(MesaValue::List(l_arc))) = (args.get(0).cloned(), args.get(1)) {
                let l = l_arc.lock().unwrap();
                let mut res = Vec::new();
                for item in l.iter() {
                    let mut s = s_orig.clone();
                    res.push(s.call_value(f.clone(), vec![item.clone()])?);
                }
                Ok(MesaValue::List(Arc::new(Mutex::new(res))))
            } else { Err(MesaError::runtime("mapear(funcion, lista)")) }
        }});
        self.native("filtrar", { let s_orig = self.clone(); move |args| {
            if let (Some(f), Some(MesaValue::List(l_arc))) = (args.get(0).cloned(), args.get(1)) {
                let l = l_arc.lock().unwrap();
                let mut res = Vec::new();
                for item in l.iter() {
                    let mut s = s_orig.clone();
                    if s.call_value(f.clone(), vec![item.clone()])?.is_truthy() {
                        res.push(item.clone());
                    }
                }
                Ok(MesaValue::List(Arc::new(Mutex::new(res))))
            } else { Err(MesaError::runtime("filtrar(funcion, lista)")) }
        }});
        self.native("reducir", { let s_orig = self.clone(); move |args| {
            if let (Some(f), Some(MesaValue::List(l_arc))) = (args.get(0).cloned(), args.get(1)) {
                let l = l_arc.lock().unwrap();
                let mut iter = l.iter();
                let mut acc = iter.next().cloned().unwrap_or(MesaValue::Null);
                for item in iter {
                    let mut s = s_orig.clone();
                    acc = s.call_value(f.clone(), vec![acc, item.clone()])?;
                }
                Ok(acc)
            } else { Err(MesaError::runtime("reducir(funcion, lista)")) }
        }});
        self.native("tomar", |args| {
            if let (Some(MesaValue::List(l_arc)), Some(MesaValue::Num(n))) = (args.get(0), args.get(1)) {
                let l = l_arc.lock().unwrap();
                let res = l.iter().take(*n as usize).cloned().collect();
                Ok(MesaValue::List(Arc::new(Mutex::new(res))))
            } else { Err(MesaError::runtime("tomar(lista, n)")) }
        });
        self.native("ahora", |_| Ok(MesaValue::Str(chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string())));
        self.native("timestamp", |_| Ok(MesaValue::Num(chrono::Utc::now().timestamp() as f64)));
        self.native("leer", |args| { use std::io::{self, Write}; if let Some(p) = args.first() { print!("{}", p); io::stdout().flush().ok(); } let mut s = String::new(); io::stdin().read_line(&mut s).ok(); Ok(MesaValue::Str(s.trim_end_matches('\n').to_string())) });
        self.native("preguntar", |args| { use std::io::{self, Write}; if let Some(p) = args.first() { print!("{}", p); io::stdout().flush().ok(); } let mut s = String::new(); io::stdin().read_line(&mut s).ok(); Ok(MesaValue::Str(s.trim_end_matches('\n').to_string())) });
        self.native("entero", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(n.trunc())), Some(MesaValue::Str(s)) => s.trim().parse::<f64>().map(|n| MesaValue::Num(n.trunc())).map_err(|_| MesaError::runtime("No se puede convertir a entero")), Some(MesaValue::Bool(b)) => Ok(MesaValue::Num(if *b { 1.0 } else { 0.0 })), _ => Err(MesaError::runtime("entero: argumento inválido")) });
        self.native("int", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(n.trunc())), Some(MesaValue::Str(s)) => s.trim().parse::<f64>().map(|n| MesaValue::Num(n.trunc())).map_err(|_| MesaError::runtime("No se puede convertir a entero")), _ => Err(MesaError::runtime("int: argumento inválido")) });
        self.native("decimal", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(*n)), Some(MesaValue::Str(s)) => s.trim().parse::<f64>().map(MesaValue::Num).map_err(|_| MesaError::runtime("No se puede convertir a decimal")), _ => Err(MesaError::runtime("decimal: argumento inválido")) });
        self.native("float", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(*n)), Some(MesaValue::Str(s)) => s.trim().parse::<f64>().map(MesaValue::Num).map_err(|_| MesaError::runtime("No se puede convertir")), _ => Err(MesaError::runtime("float: argumento inválido")) });
        self.native("texto", |args| Ok(MesaValue::Str(args.first().map(|v| v.to_string()).unwrap_or_default())));
        self.native("str", |args| Ok(MesaValue::Str(args.first().map(|v| v.to_string()).unwrap_or_default())));
        self.native("tipo", |args| Ok(MesaValue::Str(args.first().map(|v| v.type_name().to_string()).unwrap_or_else(|| "nada".to_string()))));
        self.native("type", |args| Ok(MesaValue::Str(args.first().map(|v| v.type_name().to_string()).unwrap_or_else(|| "nada".to_string()))));
        self.native("abs", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(n.abs())), _ => Err(MesaError::runtime("abs requiere número")) });
        self.native("absoluto", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(n.abs())), _ => Err(MesaError::runtime("absoluto requiere número")) });
        self.native("sqrt", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(n.sqrt())), _ => Err(MesaError::runtime("sqrt requiere número")) });
        self.native("raiz", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(n.sqrt())), _ => Err(MesaError::runtime("raiz requiere número")) });
        self.native("pow", |args| match (args.first(), args.get(1)) { (Some(MesaValue::Num(a)), Some(MesaValue::Num(b))) => Ok(MesaValue::Num(a.powf(*b))), _ => Err(MesaError::runtime("pow(base, exp)")) });
        self.native("potencia", |args| match (args.first(), args.get(1)) { (Some(MesaValue::Num(a)), Some(MesaValue::Num(b))) => Ok(MesaValue::Num(a.powf(*b))), _ => Err(MesaError::runtime("potencia(base, exp)")) });
        self.native("sin", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(n.sin())), _ => Err(MesaError::runtime("sin requiere número")) });
        self.native("cos", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(n.cos())), _ => Err(MesaError::runtime("cos requiere número")) });
        self.native("tan", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(n.tan())), _ => Err(MesaError::runtime("tan requiere número")) });
        self.native("log", |args| match args.first() { Some(MesaValue::Num(n)) => Ok(MesaValue::Num(n.ln())), _ => Err(MesaError::runtime("log requiere número")) });
        self.native("redondear", |args| match (args.first(), args.get(1)) { (Some(MesaValue::Num(n)), None) => Ok(MesaValue::Num(n.round())), (Some(MesaValue::Num(n)), Some(MesaValue::Num(d))) => Ok(MesaValue::Num((n * 10f64.powf(*d)).round() / 10f64.powf(*d))), _ => Err(MesaError::runtime("redondear requiere número")) });
        self.native("round", |args| match (args.first(), args.get(1)) { (Some(MesaValue::Num(n)), None) => Ok(MesaValue::Num(n.round())), (Some(MesaValue::Num(n)), Some(MesaValue::Num(d))) => Ok(MesaValue::Num((n * 10f64.powf(*d)).round() / 10f64.powf(*d))), _ => Err(MesaError::runtime("round requiere número")) });
        self.native("min", |args| { let mut m = args.first().cloned().ok_or_else(|| MesaError::runtime("min requiere argumentos"))?; for v in &args[1..] { if let (MesaValue::Num(a), MesaValue::Num(b)) = (&m.clone(), v) { if b < a { m = v.clone(); } } } Ok(m) });
        self.native("max", |args| { let mut m = args.first().cloned().ok_or_else(|| MesaError::runtime("max requiere argumentos"))?; for v in &args[1..] { if let (MesaValue::Num(a), MesaValue::Num(b)) = (&m.clone(), v) { if b > a { m = v.clone(); } } } Ok(m) });
        self.def("PI", MesaValue::Num(std::f64::consts::PI));
        self.def("E", MesaValue::Num(std::f64::consts::E));
        self.native("longitud", |args| match args.first() { Some(MesaValue::List(l)) => Ok(MesaValue::Num(l.lock().unwrap().len() as f64)), Some(MesaValue::Str(s)) => Ok(MesaValue::Num(s.chars().count() as f64)), Some(MesaValue::Map(m)) => Ok(MesaValue::Num(m.lock().unwrap().len() as f64)), _ => Err(MesaError::runtime("longitud requiere colección")) });
        self.native("tamaño", |args| match args.first() { Some(MesaValue::List(l)) => Ok(MesaValue::Num(l.lock().unwrap().len() as f64)), Some(MesaValue::Str(s)) => Ok(MesaValue::Num(s.chars().count() as f64)), Some(MesaValue::Map(m)) => Ok(MesaValue::Num(m.lock().unwrap().len() as f64)), _ => Err(MesaError::runtime("tamaño requiere colección")) });
        self.native("len", |args| match args.first() { Some(MesaValue::List(l)) => Ok(MesaValue::Num(l.lock().unwrap().len() as f64)), Some(MesaValue::Str(s)) => Ok(MesaValue::Num(s.chars().count() as f64)), _ => Err(MesaError::runtime("len requiere colección")) });
        self.native("rango", |args| { let (s, e) = match args.len() { 1 => (0.0, if let MesaValue::Num(n) = args[0] { n } else { return Err(MesaError::runtime("rango requiere número")); }), _ => (if let MesaValue::Num(n) = args[0] { n } else { 0.0 }, if let MesaValue::Num(n) = args[1] { n } else { return Err(MesaError::runtime("rango requiere número")); }) }; Ok(MesaValue::List(Arc::new(Mutex::new((s as i64..e as i64).map(|n| MesaValue::Num(n as f64)).collect())))) });
        self.native("range", |args| { let (s, e) = match args.len() { 1 => (0.0, if let MesaValue::Num(n) = args[0] { n } else { return Err(MesaError::runtime("range requiere número")); }), _ => (if let MesaValue::Num(n) = args[0] { n } else { 0.0 }, if let MesaValue::Num(n) = args[1] { n } else { return Err(MesaError::runtime("range requiere número")); }) }; Ok(MesaValue::List(Arc::new(Mutex::new((s as i64..e as i64).map(|n| MesaValue::Num(n as f64)).collect())))) });
        self.native("suma", |args| match args.first() { Some(MesaValue::List(l)) => Ok(MesaValue::Num(l.lock().unwrap().iter().filter_map(|v| if let MesaValue::Num(n) = v { Some(*n) } else { None }).sum())), _ => Err(MesaError::runtime("suma requiere lista")) });
        self.native("sum", |args| match args.first() { Some(MesaValue::List(l)) => Ok(MesaValue::Num(l.lock().unwrap().iter().filter_map(|v| if let MesaValue::Num(n) = v { Some(*n) } else { None }).sum())), _ => Err(MesaError::runtime("sum requiere lista")) });
        self.native("substring", |args| match (args.first(), args.get(1), args.get(2)) { (Some(MesaValue::Str(s)), Some(MesaValue::Num(start)), Some(MesaValue::Num(len))) => { let chars: Vec<char> = s.chars().collect(); let si = *start as usize; let ei = (si + *len as usize).min(chars.len()); Ok(MesaValue::Str(chars[si..ei].iter().collect())) }, _ => Err(MesaError::runtime("substring(texto, inicio, longitud)")) });
        self.native("sub", |args| match (args.first(), args.get(1), args.get(2)) { (Some(MesaValue::Str(s)), Some(MesaValue::Num(start)), Some(MesaValue::Num(len))) => { let chars: Vec<char> = s.chars().collect(); let si = *start as usize; let ei = (si + *len as usize).min(chars.len()); Ok(MesaValue::Str(chars[si..ei].iter().collect())) }, _ => Err(MesaError::runtime("sub(texto, inicio, longitud)")) });
        self.native("es_numero", |args| match args.first() { Some(MesaValue::Str(s)) => Ok(MesaValue::Bool(s.chars().all(|c| c.is_ascii_digit()))), _ => Ok(MesaValue::Bool(false)) });
        self.native("es_letra", |args| match args.first() { Some(MesaValue::Str(s)) => Ok(MesaValue::Bool(s.chars().all(|c| c.is_alphabetic()))), _ => Ok(MesaValue::Bool(false)) });
        self.native("verificar", |args| { let ok = args.first().map(|v| v.is_truthy()).unwrap_or(false); if !ok { let msg = args.get(1).map(|v| v.to_string()).unwrap_or_else(|| "Fallo de verificación".into()); return Err(MesaError::runtime(msg)); } Ok(MesaValue::Bool(true)) });
        self.native("check", |args| { let ok = args.first().map(|v| v.is_truthy()).unwrap_or(false); if !ok { let msg = args.get(1).map(|v| v.to_string()).unwrap_or_else(|| "Assertion failed".into()); return Err(MesaError::runtime(msg)); } Ok(MesaValue::Bool(true)) });
        self.native("afirmar", |args| { let ok = args.first().map(|v| v.is_truthy()).unwrap_or(false); if !ok { let msg = args.get(1).map(|v| v.to_string()).unwrap_or_else(|| "Fallo de verificación".into()); return Err(MesaError::runtime(msg)); } Ok(MesaValue::Bool(true)) });
        self.native("assert", |args| { let ok = args.first().map(|v| v.is_truthy()).unwrap_or(false); if !ok { let msg = args.get(1).map(|v| v.to_string()).unwrap_or_else(|| "Fallo de verificación".into()); return Err(MesaError::runtime(msg)); } Ok(MesaValue::Bool(true)) });
        self.native("es_igual", |args| {
            if args.len() < 2 { return Err(MesaError::runtime("es_igual(obtenido, esperado, [nombre])")); }
            let ok = args[0] == args[1];
            let name = args.get(2).map(|v| v.to_string()).unwrap_or_else(|| "Prueba".into());
            if ok { println!("  ✅ {}", name); }
            else { println!("  ❌ {} → esperado: {}, obtenido: {}", name, args[1], args[0]); }
            Ok(MesaValue::Bool(ok))
        });
        self.native("es_verdadero", |args| {
            if args.is_empty() { return Err(MesaError::runtime("es_verdadero(cond, [nombre])")); }
            let ok = args[0].is_truthy();
            let name = args.get(1).map(|v| v.to_string()).unwrap_or_else(|| "Prueba".into());
            if ok { println!("  ✅ {}", name); }
            else { println!("  ❌ {} → esperaba verdadero", name); }
            Ok(MesaValue::Bool(ok))
        });
        // Web Builder Builtins (examples/web.mesa)
        let html = self.web_html.clone();
        self.native("pagina", { let h = html.clone(); move |args| {
            let title = args.get(0).map(|v| v.to_string()).unwrap_or_default();
            let theme = args.get(1).map(|v| v.to_string()).unwrap_or_else(|| "moderno".into());
            
            let (bg, card_bg, text, primary, secondary, extra_css) = match theme.as_str() {
                "oscuro" => (
                    "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)", 
                    "rgba(30, 41, 59, 0.7)", 
                    "#f8fafc", 
                    "#818cf8", 
                    "#6366f1",
                    "backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1);"
                ),
                "retro" => (
                    "#000000", 
                    "#000000", 
                    "#00ff00", 
                    "#00ff00", 
                    "#00ff00",
                    "border: 2px solid #00ff00 !important; font-family: 'Courier New', monospace !important; text-shadow: 0 0 5px #00ff00;"
                ),
                _ => (
                    "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)", 
                    "rgba(255, 255, 255, 0.8)", 
                    "#1e293b", 
                    "#6366f1", 
                    "#4f46e5",
                    "backdrop-filter: blur(8px); border: 1px solid rgba(255,255,255,0.3);"
                ),
            };

            let mut s = h.lock().unwrap();
            *s = format!(r#"<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{ 
            --primary: {}; 
            --secondary: {};
            --bg: {}; 
            --card: {}; 
            --text: {}; 
        }}
        * {{ box-sizing: border-box; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }}
        body {{ 
            font-family: 'Inter', sans-serif; 
            background: var(--bg); 
            color: var(--text); 
            margin: 0; 
            padding: 20px; 
            min-height: 100vh;
            line-height: 1.6;
        }}
        .container {{ max-width: 1000px; margin: 40px auto; padding: 40px; border-radius: 32px; {} }}
        h1 {{ 
            font-size: 3.5rem; 
            font-weight: 800; 
            background: linear-gradient(to right, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
            letter-spacing: -2px;
        }}
        p {{ font-size: 1.25rem; opacity: 0.8; margin-bottom: 1.5rem; }}
        .card {{ 
            background: var(--card); 
            border-radius: 20px; 
            padding: 30px; 
            margin: 24px 0; 
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
            border: 1px solid rgba(255,255,255,0.1);
            position: relative;
            overflow: hidden;
        }}
        .card:hover {{ transform: scale(1.02) translateY(-5px); box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); }}
        .card::before {{
            content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
            background: linear-gradient(to bottom, var(--primary), var(--secondary));
        }}
        ul {{ list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; }}
        li {{ 
            background: var(--card); 
            padding: 20px; 
            border-radius: 16px; 
            font-weight: 600;
            display: flex;
            align-items: center;
            border: 1px solid rgba(255,255,255,0.05);
        }}
        li:hover {{ background: var(--primary); color: white; }}
        .alert {{ 
            padding: 24px; 
            border-radius: 20px; 
            background: linear-gradient(to right, var(--primary), var(--secondary));
            color: white;
            font-weight: 700;
            text-align: center;
            box-shadow: 0 10px 30px -10px var(--primary);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{ 
            0% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-5px); }}
            100% {{ transform: translateY(0); }}
        }}
        footer {{ margin-top: 80px; padding: 40px; text-align: center; opacity: 0.5; font-weight: 300; }}
        .row {{ display: flex; gap: 30px; margin: 30px 0; flex-wrap: wrap; }}
        .col {{ flex: 1; min-width: 300px; }}
    </style>
</head>
<body>
<div class='container'>
"#, title, primary, secondary, bg, card_bg, text, extra_css);
            Ok(MesaValue::Null)
        }});
        let h2 = html.clone();
        self.native("titulo", move |args| {
            let t = args.first().map(|v| v.to_string()).unwrap_or_default();
            h2.lock().unwrap().push_str(&format!("<h1>{}</h1>\n", t));
            Ok(MesaValue::Null)
        });
        let h3 = html.clone();
        self.native("texto", move |args| {
            let t = args.first().map(|v| v.to_string()).unwrap_or_default();
            h3.lock().unwrap().push_str(&format!("<p>{}</p>\n", t));
            Ok(MesaValue::Null)
        });
        let h4 = html.clone();
        self.native("tarjeta", move |args| {
            let t = args.first().map(|v| v.to_string()).unwrap_or_default();
            h4.lock().unwrap().push_str(&format!("<div class='card'>{}</div>\n", t));
            Ok(MesaValue::Null)
        });
        let h5 = html.clone();
        self.native("lista", move |args| {
            if let Some(MesaValue::List(l)) = args.first() {
                let mut s = h5.lock().unwrap();
                s.push_str("<ul>\n");
                for item in l.lock().unwrap().iter() { s.push_str(&format!("<li>{}</li>\n", item)); }
                s.push_str("</ul>\n");
            }
            Ok(MesaValue::Null)
        });
        let h_row1 = html.clone();
        self.native("fila_inicio", move |_| { h_row1.lock().unwrap().push_str("<div class='row'>\n"); Ok(MesaValue::Null) });
        let h_row2 = html.clone();
        self.native("fila_fin", move |_| { h_row2.lock().unwrap().push_str("</div>\n"); Ok(MesaValue::Null) });
        let h_col1 = html.clone();
        self.native("columna_inicio", move |_| { h_col1.lock().unwrap().push_str("<div class='col'>\n"); Ok(MesaValue::Null) });
        let h_col2 = html.clone();
        self.native("columna_fin", move |_| { h_col2.lock().unwrap().push_str("</div>\n"); Ok(MesaValue::Null) });
        let h6 = html.clone();
        self.native("alerta", move |args| {
            let t = args.first().map(|v| v.to_string()).unwrap_or_default();
            h6.lock().unwrap().push_str(&format!("<div class='alert alert-exito'>{}</div>\n", t));
            Ok(MesaValue::Null)
        });
        let h7 = html.clone();
        self.native("footer", move |args| {
            let t = args.first().map(|v| v.to_string()).unwrap_or_default();
            h7.lock().unwrap().push_str(&format!("<footer>{}</footer>\n", t));
            Ok(MesaValue::Null)
        });
        let h_servir = html.clone();
        self.native("web_servir", move |_| {
            let final_html = h_servir.lock().unwrap().to_string() + "</div></body></html>";
            let _ = std::fs::write("index.html", final_html);
            println!("🌐 Sitio Web premium generado en 'index.html'");
            let _ = std::process::Command::new("xdg-open").arg("index.html").status();
            Ok(MesaValue::Null)
        });
        
        // OS/x86 Builtins (mesa-os/plantilla.mesa + grafico.mesa)
        let x86 = self.x86_code.clone();
        let labels = self.x86_labels.clone();
        let fixups = self.x86_fixups.clone();

        self.native("x86_nuevo", { let x = x86.clone(); let l = labels.clone(); let f = fixups.clone(); move |_| { 
            x.lock().unwrap().clear(); l.lock().unwrap().clear(); f.lock().unwrap().clear(); Ok(MesaValue::Null) 
        }});
        
        self.native("etiqueta", { let l = labels.clone(); let x = x86.clone(); move |args| {
            if let Some(name) = args.get(1).and_then(|v| if let MesaValue::Str(s) = v { Some(s.clone()) } else { None }) {
                l.lock().unwrap().insert(name.clone(), x.lock().unwrap().len());
            }
            Ok(MesaValue::Null)
        }});

        self.native("salto_lejos", { let x = x86.clone(); let f = fixups.clone(); move |args| {
            let seg = args.get(1).and_then(|v| if let MesaValue::Num(n) = v { Some(*n as u16) } else { None }).unwrap_or(0);
            let name = args.get(2).and_then(|v| if let MesaValue::Str(s) = v { Some(s.clone()) } else { None }).unwrap_or_default();
            let mut c = x.lock().unwrap();
            let current = c.len();
            c.push(0xEA); // JMP far ptr16:16
            c.extend_from_slice(&[0, 0]); // Offset placeholder
            c.extend_from_slice(&seg.to_le_bytes()); // Segment
            f.lock().unwrap().push((name.clone(), current + 1, 0xA, 0x7C00));
            Ok(MesaValue::Null)
        }});

        self.native("jmp_a", { let x = x86.clone(); let f = fixups.clone(); move |args| {
            if let Some(name) = args.get(1).and_then(|v| if let MesaValue::Str(s) = v { Some(s.clone()) } else { None }) {
                let mut c = x.lock().unwrap();
                let current = c.len();
                c.push(0xEB); // JMP rel8
                c.push(0);
                f.lock().unwrap().push((name.clone(), current + 1, 8, 0));
            }
            Ok(MesaValue::Null)
        }});

        self.native("si_igual", { let x = x86.clone(); let f = fixups.clone(); move |args| {
            if let Some(name) = args.get(1).and_then(|v| if let MesaValue::Str(s) = v { Some(s.clone()) } else { None }) {
                let mut c = x.lock().unwrap();
                let current = c.len();
                c.push(0x74); // JZ rel8
                c.push(0);
                f.lock().unwrap().push((name.clone(), current + 1, 8, 0));
            }
            Ok(MesaValue::Null)
        }});

        self.native("cmp_al", { let x = x86.clone(); move |args| {
            let val = args.get(1).and_then(|v| if let MesaValue::Num(n) = v { Some(*n as u8) } else { None }).unwrap_or(0);
            x.lock().unwrap().extend_from_slice(&[0x3C, val]); // cmp al, val
            Ok(MesaValue::Null)
        }});

        self.native("leer_puerto", { let x = x86.clone(); move |args| {
            let port = args.get(1).and_then(|v| if let MesaValue::Num(n) = v { Some(*n as u16) } else { None }).unwrap_or(0x60);
            let mut c = x.lock().unwrap();
            if port <= 0xFF { c.extend_from_slice(&[0xE4, port as u8]); } // in al, port
            else { c.extend_from_slice(&[0x66, 0xBA, (port & 0xFF) as u8, (port >> 8) as u8, 0xEC]); } // mov dx, port; in al, dx
            Ok(MesaValue::Null)
        }});

        self.native("vram_escribir", { let x = x86.clone(); move |args| {
            if let (Some(MesaValue::Num(off)), Some(MesaValue::Num(col))) = (args.get(1), args.get(2)) {
                let mut c = x.lock().unwrap();
                let offset = *off as u16;
                let color = *col as u8;
                c.extend_from_slice(&[0xB8, 0x00, 0xA0, 0x8E, 0xC0, 0xBF, (offset & 0xFF) as u8, (offset >> 8) as u8, 0xB0, color, 0xAA]);
            }
            Ok(MesaValue::Null)
        }});

        self.native("modo_video", { let x = x86.clone(); move |args| {
            let v = args.get(1).and_then(|v| if let MesaValue::Num(n) = v { Some(*n as u8) } else { None }).unwrap_or(0x03);
            x.lock().unwrap().extend_from_slice(&[0xB4, 0x00, 0xB0, v, 0xCD, 0x10]);
            Ok(MesaValue::Null)
        }});

        self.native("x86_bytes", { let x = x86.clone(); move |args| {
            if let Some(MesaValue::List(l)) = args.get(1) {
                let mut x_lock = x.lock().unwrap();
                for v in l.lock().unwrap().iter() {
                    if let MesaValue::Num(b) = v { x_lock.push(*b as u8); }
                }
            }
            Ok(MesaValue::Null)
        }});

        self.native("limpiar_pantalla", { let x = x86.clone(); move |_| {
            x.lock().unwrap().extend_from_slice(&[0xB4, 0x06, 0xB0, 0x00, 0xB7, 0x07, 0xB5, 0x00, 0xB1, 0x00, 0xB6, 0x18, 0xB2, 0x4F, 0xCD, 0x10]);
            Ok(MesaValue::Null)
        }});
        self.native("mover_cursor", { let x = x86.clone(); move |args| {
            let r = args.get(1).and_then(|v| if let MesaValue::Num(n) = v { Some(*n as u8) } else { None }).unwrap_or(0);
            let c = args.get(2).and_then(|v| if let MesaValue::Num(n) = v { Some(*n as u8) } else { None }).unwrap_or(0);
            let mut x_lock = x.lock().unwrap();
            // AH=02h, BH=0 (pagina), DH=fila, DL=col; int 10h
            x_lock.extend_from_slice(&[0xB4, 0x02, 0xB7, 0x00, 0xB6, r, 0xB2, c, 0xCD, 0x10]);
            Ok(MesaValue::Null)
        }});
        self.native("insertar_print_str", { let x = x86.clone(); move |args| {
            let s = args.get(1).map(|v| v.to_string()).unwrap_or_default();
            let mut c = x.lock().unwrap();
            for b in s.bytes() {
                c.extend_from_slice(&[0xB4, 0x0E, 0xB0, b, 0xCD, 0x10]); // mov ah, 0x0E; mov al, char; int 0x10
            }
            Ok(MesaValue::Null)
        }});
        self.native("hlt", { let x = x86.clone(); move |_| { x.lock().unwrap().push(0xF4); Ok(MesaValue::Null) }});
        self.native("x86_bytes", { let x = x86.clone(); move |args| {
            if let Some(MesaValue::List(l_arc)) = args.first() {
                let l = l_arc.lock().unwrap();
                let bytes: Vec<u8> = l.iter().map(|v| if let MesaValue::Num(n) = v { *n as u8 } else { 0 }).collect();
                x.lock().unwrap().extend_from_slice(&bytes);
            }
            Ok(MesaValue::Null)
        }});
        
        self.native("iniciar_boot", { let x = x86.clone(); move |_| {
            let mut c = x.lock().unwrap();
            // standard boot setup: cli; cld; xor ax, ax; mov ds, ax; mov es, ax; mov ss, ax; mov sp, 0x7C00; sti
            c.extend_from_slice(&[0xFA, 0xFC, 0x31, 0xC0, 0x8E, 0xD8, 0x8E, 0xC0, 0x8E, 0xD0, 0xBC, 0x00, 0x7C, 0xFB]);
            Ok(MesaValue::Null)
        }});
        self.native("apuntar", { let x = x86.clone(); let f = fixups.clone(); move |args| {
            let base = args.get(1).and_then(|v| if let MesaValue::Num(n) = v { Some(*n as u32) } else { None }).unwrap_or(0);
            let name = args.get(2).and_then(|v| if let MesaValue::Str(s) = v { Some(s.clone()) } else { None }).unwrap_or_default();
            let mut c = x.lock().unwrap();
            let current = c.len();
            c.push(0xBE); // mov si, imm16
            c.extend_from_slice(&[0, 0]);
            f.lock().unwrap().push((name, current + 1, 0xA, base)); // 0xA = Absolute 16
            Ok(MesaValue::Null)
        }});
        self.native("llamar", { let x = x86.clone(); let f = fixups.clone(); move |args| {
            let name = args.get(1).and_then(|v| if let MesaValue::Str(s) = v { Some(s.clone()) } else { None })
                        .or_else(|| args.get(2).and_then(|v| if let MesaValue::Str(s) = v { Some(s.clone()) } else { None }))
                        .unwrap_or_default();
            let mut c = x.lock().unwrap();
            let current = c.len();
            c.push(0xE8); // call rel16
            c.extend_from_slice(&[0, 0]);
            f.lock().unwrap().push((name, current + 1, 16, 0));
            Ok(MesaValue::Null)
        }});
        self.native("push_ax", { let x = x86.clone(); move |_| { x.lock().unwrap().push(0x50); Ok(MesaValue::Null) }});
        self.native("pop_ax", { let x = x86.clone(); move |_| { x.lock().unwrap().push(0x58); Ok(MesaValue::Null) }});
        
        self.native("insertar_read_key", { let x = x86.clone(); let l = labels.clone(); move |_| {
            let mut c = x.lock().unwrap();
            l.lock().unwrap().insert("read_key".to_string(), c.len());
            // read key robust: .wait: mov ah, 1; int 16h; jz .wait; mov ah, 0; int 16h; ret
            c.extend_from_slice(&[0xB4, 0x01, 0xCD, 0x16, 0x74, 0xFA, 0xB4, 0x00, 0xCD, 0x16, 0xC3]);
            Ok(MesaValue::Null)
        }});
        self.native("cadena", { let x = x86.clone(); let l = labels.clone(); move |args| {
            if let (Some(MesaValue::Str(name)), Some(MesaValue::Str(val))) = (args.get(1), args.get(2)) {
                let mut c = x.lock().unwrap();
                l.lock().unwrap().insert(name.clone(), c.len());
                c.extend_from_slice(val.as_bytes());
                c.push(0); // null terminator
            }
            Ok(MesaValue::Null)
        }});
        
        self.native("insertar_print_str", { let x = x86.clone(); let l = labels.clone(); move |_| {
            let mut c = x.lock().unwrap();
            l.lock().unwrap().insert("print_str".to_string(), c.len());
            // .loop: lodsb; or al, al; jz .done; mov ah, 0eh; int 10h; jmp .loop; .done: ret
            c.extend_from_slice(&[0xAC, 0x08, 0xC0, 0x74, 0x07, 0xB4, 0x0E, 0xCD, 0x10, 0xEB, 0xF5, 0xC3]);
            Ok(MesaValue::Null)
        }});
        self.native("insertar_print_char", { let x = x86.clone(); let l = labels.clone(); move |_| {
            let mut c = x.lock().unwrap();
            l.lock().unwrap().insert("print_char".to_string(), c.len());
            // mov ah, 0eh; int 10h; ret
            c.extend_from_slice(&[0xB4, 0x0E, 0xCD, 0x10, 0xC3]);
            Ok(MesaValue::Null)
        }});
        
        self.native("compilar", { let x = x86.clone(); let l = labels.clone(); let f = fixups.clone(); move |_| {
            let mut code = x.lock().unwrap().clone();
            let lbls = l.lock().unwrap();
            let fxps = f.lock().unwrap();
            
            println!("🛠️  Compilando {} bytes de código con {} etiquetas y {} fixups", code.len(), lbls.len(), fxps.len());

            for (name, pos, ftype, base) in fxps.iter() {
                if let Some(&target) = lbls.get(name) {
                    if *ftype == 16 {
                        let rel = (target as i32 - (*pos as i32 + 2)) as i16;
                        code[*pos] = (rel & 0xFF) as u8;
                        code[*pos + 1] = (rel >> 8) as u8;
                        println!("  - Fixup REL16: {} -> {} (rel: {})", name, target, rel);
                    } else if *ftype == 8 {
                        let rel = (target as i32 - (*pos as i32 + 1)) as i8;
                        code[*pos] = rel as u8;
                        println!("  - Fixup REL8: {} -> {} (rel: {})", name, target, rel);
                    } else if *ftype == 0xA { // Absolute 16 (pos = target + base)
                        let abs = (*base as i32 + target as i32) as u16;
                        code[*pos] = (abs & 0xFF) as u8;
                        code[*pos + 1] = (abs >> 8) as u8;
                        println!("  - Fixup ABS: {} -> {} (abs: 0x{:04X})", name, target, abs);
                    }
                } else {
                    println!("  ⚠️ Etiqueta no encontrada: {}", name);
                }
            }

            if code.is_empty() { code.extend_from_slice(&[0xEB, 0xFE]); }
            while code.len() < 510 { code.push(0); }
            let list: Vec<MesaValue> = code.iter().map(|b| MesaValue::Num(*b as f64)).collect();
            Ok(MesaValue::List(Arc::new(Mutex::new(list))))
        }});
        self.native("bootsector", |_args| {
            let mut v = if let Some(MesaValue::List(l)) = _args.first() { l.lock().unwrap().clone() } else { vec![MesaValue::Num(0.0); 510] };
            while v.len() < 510 { v.push(MesaValue::Num(0.0)); } 
            v.push(MesaValue::Num(0x55 as f64)); v.push(MesaValue::Num(0xAA as f64));
            Ok(MesaValue::List(Arc::new(Mutex::new(v))))
        });
        self.native("crear_directorio", |args| {
            if let Some(MesaValue::Str(path)) = args.first() {
                let _ = std::fs::create_dir_all(path);
            }
            Ok(MesaValue::Null)
        });
        self.native("archivo_escribir_bytes", |args| {
            if let (Some(MesaValue::Str(path)), Some(MesaValue::List(l_arc))) = (args.get(0), args.get(1)) {
                let l = l_arc.lock().unwrap();
                let bytes_u8: Vec<u8> = l.iter().map(|v| if let MesaValue::Num(n) = v { *n as u8 } else { 0 }).collect();
                println!("💾 Escribiendo {} bytes en {}", bytes_u8.len(), path);
                let _ = std::fs::write(path, bytes_u8);
            }
            Ok(MesaValue::Null)
        });
        self.native("lanzar_qemu", |args| {
            if let Some(MesaValue::Str(img)) = args.first() {
                println!("🚀 Lanzando QEMU con imagen: {}", img);
                let _ = std::process::Command::new("qemu-system-x86_64")
                    .arg("-drive")
                    .arg(format!("format=raw,file={}", img))
                    .spawn();
            }
            Ok(MesaValue::Null)
        });

        self.native("lista", |args| { Ok(MesaValue::List(Arc::new(Mutex::new(args.to_vec())))) });
        self.native("salir", |args| { let code = args.first().and_then(|v| if let MesaValue::Num(n) = v { Some(*n as i32) } else { None }).unwrap_or(0); std::process::exit(code) });
        self.native("exit", |args| { let code = args.first().and_then(|v| if let MesaValue::Num(n) = v { Some(*n as i32) } else { None }).unwrap_or(0); std::process::exit(code) });
        self.native("dormir", |args| { let ms = args.first().and_then(|v| if let MesaValue::Num(n) = v { Some(*n) } else { None }).unwrap_or(0.0); std::thread::sleep(std::time::Duration::from_millis(ms as u64)); Ok(MesaValue::Null) });
        self.native("sleep", |args| { let ms = args.first().and_then(|v| if let MesaValue::Num(n) = v { Some(*n) } else { None }).unwrap_or(0.0); std::thread::sleep(std::time::Duration::from_millis(ms as u64)); Ok(MesaValue::Null) });
        self.native("tiempo", |_| { use std::time::{SystemTime, UNIX_EPOCH}; Ok(MesaValue::Num(SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs_f64()).unwrap_or(0.0))) });
        self.native("time", |_| { use std::time::{SystemTime, UNIX_EPOCH}; Ok(MesaValue::Num(SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs_f64()).unwrap_or(0.0))) });
        self.native("archivo_leer", |args| { let p = args.first().map(|v| v.to_string()).unwrap_or_default(); std::fs::read_to_string(&p).map(MesaValue::Str).map_err(|e| MesaError::runtime(format!("Error leyendo '{}': {}", p, e))) });
        self.native("archivo_escribir", |args| { let p = args.first().map(|v| v.to_string()).unwrap_or_default(); let c = args.get(1).map(|v| v.to_string()).unwrap_or_default(); std::fs::write(&p, c).map(|_| MesaValue::Bool(true)).map_err(|e| MesaError::runtime(e.to_string())) });
        self.native("archivo_existe", |args| { let p = args.first().map(|v| v.to_string()).unwrap_or_default(); Ok(MesaValue::Bool(std::path::Path::new(&p).exists())) });
        self.native("existe", |args| { let p = args.first().map(|v| v.to_string()).unwrap_or_default(); Ok(MesaValue::Bool(std::path::Path::new(&p).exists())) });

        // Web Builder
        let web = self.web_html.clone();
        self.native("pagina", { let w = web.clone(); move |args| {
            let mut h = w.lock().unwrap();
            h.clear();
            let title = args.get(0).map(|v| v.to_string()).unwrap_or("Mesa Web".to_string());
            let theme = args.get(1).map(|v| v.to_string()).unwrap_or("claro".to_string());
            h.push_str(&format!("<!DOCTYPE html><html><head><title>{}</title>", title));
            h.push_str("<meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>");
            if theme == "oscuro" {
                h.push_str("<style>body{background:#1a1a1a;color:#eee;font-family:sans-serif;padding:2em} .card{background:#2a2a2a;padding:1em;margin:1em 0;border-radius:8px} ul{list-style-type:none;padding:0}</style>");
            } else {
                h.push_str("<style>body{background:#f0f2f5;color:#333;font-family:sans-serif;padding:2em} .card{background:#fff;padding:1em;margin:1em 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)} ul{list-style-type:none;padding:0}</style>");
            }
            h.push_str("</head><body>");
            Ok(MesaValue::Null)
        }});

        self.native("titulo", { let w = web.clone(); move |args| {
            let mut h = w.lock().unwrap();
            h.push_str(&format!("<h1>{}</h1>", args.get(0).map(|v| v.to_string()).unwrap_or_default()));
            Ok(MesaValue::Null)
        }});

        self.native("texto", { let w = web.clone(); move |args| {
            let mut h = w.lock().unwrap();
            h.push_str(&format!("<p>{}</p>", args.get(0).map(|v| v.to_string()).unwrap_or_default()));
            Ok(MesaValue::Null)
        }});

        self.native("tarjeta", { let w = web.clone(); move |args| {
            let mut h = w.lock().unwrap();
            let title = args.get(0).map(|v| v.to_string()).unwrap_or_default();
            let body = args.get(1).map(|v| v.to_string()).unwrap_or_default();
            if body.is_empty() {
                h.push_str(&format!("<div class='card'>{}</div>", title));
            } else {
                h.push_str(&format!("<div class='card'><h3>{}</h3><p>{}</p></div>", title, body));
            }
            Ok(MesaValue::Null)
        }});

        self.native("navbar", { let w = web.clone(); move |args| {
            let mut h = w.lock().unwrap();
            let sitename = args.get(0).map(|v| v.to_string()).unwrap_or_default();
            h.push_str("<nav style='background:#333; color:#fff; padding:1.2em; display:flex; justify-content:space-between; align-items:center; border-radius:12px; margin-bottom:2em; font-weight:bold'>");
            h.push_str(&format!("<span>{}</span>", sitename));
            h.push_str("<div style='display:flex; gap:1.5em'>");
            if let Some(MesaValue::List(l)) = args.get(1) {
                for item in l.lock().unwrap().iter() {
                    if let MesaValue::List(link_pair) = item {
                        let lp = link_pair.lock().unwrap();
                        let name = lp.get(0).map(|v| v.to_string()).unwrap_or_default();
                        let url = lp.get(1).map(|v| v.to_string()).unwrap_or("#".to_string());
                        h.push_str(&format!("<a href='{}' style='color:#fff; text-decoration:none; font-size:0.9em hover:opacity:0.8'>{}</a>", url, name));
                    }
                }
            }
            h.push_str("</div></nav>");
            Ok(MesaValue::Null)
        }});

        self.native("separador", { let w = web.clone(); move |_| {
            w.lock().unwrap().push_str("<hr style='margin:2.5em 0; border:0; border-top:1px solid #ddd'>");
            Ok(MesaValue::Null)
        }});

        self.native("lista", { let w = web.clone(); move |args| {
            let mut h = w.lock().unwrap();
            h.push_str("<ul style='padding-left:1em; margin:1em 0'>");
            if let Some(MesaValue::List(l)) = args.first() {
                for item in l.lock().unwrap().iter() { h.push_str(&format!("<li style='margin-bottom:0.5em'>• {}</li>", item)); }
            }
            h.push_str("</ul>");
            Ok(MesaValue::Null)
        }});

        self.native("alerta", { let w = web.clone(); move |args| {
            let mut h = w.lock().unwrap();
            let msg = args.get(0).map(|v| v.to_string()).unwrap_or_default();
            let tipo = args.get(1).map(|v| v.to_string()).unwrap_or("info".to_string());
            let color = if tipo == "exito" { "#e8f5e9" } else { "#ffebee" };
            let border = if tipo == "exito" { "#4caf50" } else { "#f44336" };
            h.push_str(&format!("<div style='padding:1em; margin:1.5em 0; background:{}; border-left:5px solid {}; border-radius:4px; color:#333'>{}</div>", color, border, msg));
            Ok(MesaValue::Null)
        }});

        self.native("footer", { let w = web.clone(); move |args| {
            let mut h = w.lock().unwrap();
            h.push_str(&format!("<hr style='margin-top:4em; border:0; border-top:1px solid #eee'><footer style='text-align:center; opacity:0.6; padding:2em 0; font-size:0.9em'>{}</footer>", args.get(0).map(|v| v.to_string()).unwrap_or_default()));
            Ok(MesaValue::Null)
        }});

        self.native("fila_inicio", { let w = web.clone(); move |_| { w.lock().unwrap().push_str("<div style='display:flex; gap:1.5em; flex-wrap:wrap; margin:1.5em 0'>"); Ok(MesaValue::Null) } });
        self.native("fila_fin", { let w = web.clone(); move |_| { w.lock().unwrap().push_str("</div>"); Ok(MesaValue::Null) } });
        self.native("columna_inicio", { let w = web.clone(); move |_| { w.lock().unwrap().push_str("<div style='flex:1; min-width:250px'>"); Ok(MesaValue::Null) } });
        self.native("columna_fin", { let w = web.clone(); move |_| { w.lock().unwrap().push_str("</div>"); Ok(MesaValue::Null) } });

        self.native("web_servir", { let w = web.clone(); move |args| {
            let mut h = w.lock().unwrap();
            h.push_str("</body></html>");
            let port = args.first().and_then(|v| if let MesaValue::Num(n) = v { Some(*n as u16) } else { None }).unwrap_or(8080);
            
            let html_content = h.clone();
            let _ = std::fs::write("index.html", &html_content);
            
            println!("🌐 Sirviendo web real en http://localhost:{}", port);
            println!("🚀 El servidor está ACTIVO. Presiona Ctrl+C para finalizar.");

            let listener = std::net::TcpListener::bind(format!("0.0.0.0:{}", port))
                .map_err(|e| MesaError::runtime(format!("Error al iniciar servidor en puerto {}: {}", port, e)))?;
            
            for stream in listener.incoming() {
                if let Ok(mut stream) = stream {
                    let response = format!(
                        "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                        html_content.len(),
                        html_content
                    );
                    use std::io::Write;
                    let _ = stream.write_all(response.as_bytes());
                    let _ = stream.flush();
                }
            }
            Ok(MesaValue::Null)
        }});
    }
}
