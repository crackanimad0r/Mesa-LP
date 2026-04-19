// Mesa v4.0.0 - Native Value System

use std::collections::HashMap;
use std::fmt;
use std::sync::{Arc, Mutex};
use std::any::Any;
use crate::ast::{Stmt, Param};
use crate::env::Env;

use serde::{Serialize, Serializer};

#[derive(Clone, Debug)]
pub struct MesaFunc {
    pub name: String,
    pub params: Vec<Param>,
    pub body: Vec<Stmt>,
    pub closure: Arc<Mutex<Env>>,
}

#[derive(Clone, Debug)]
pub struct MesaShape {
    pub name: String,
    pub fields: Vec<String>,
    pub methods: HashMap<String, MesaFunc>,
}

#[derive(Clone, Debug)]
pub struct MesaInstance {
    pub shape_name: String,
    pub fields: HashMap<String, MesaValue>,
    pub methods: HashMap<String, MesaFunc>,
}

impl MesaInstance {
    pub fn get(&self, key: &str) -> Option<&MesaValue> { self.fields.get(key) }
    pub fn set(&mut self, key: &str, val: MesaValue) { self.fields.insert(key.to_string(), val); }
}

// NativeFn does NOT take &mut Interpreter to avoid borrow conflicts
pub type NativeFn = Arc<dyn Fn(Vec<MesaValue>) -> Result<MesaValue, MesaError> + Send + Sync>;

#[derive(Clone)]
pub enum MesaValue {
    Num(f64),
    Str(String),
    Bool(bool),
    List(Arc<Mutex<Vec<MesaValue>>>),
    Map(Arc<Mutex<HashMap<String, MesaValue>>>),
    Func(Arc<MesaFunc>),
    NativeFunc(String, NativeFn),
    Native(Arc<Mutex<Box<dyn Any + Send>>>),
    Shape(Arc<MesaShape>),
    Instance(Arc<Mutex<MesaInstance>>),
    Lambda(Arc<Vec<Param>>, Arc<Vec<Stmt>>),
    Range(f64, f64, bool), // start, end, inclusive
    Null,
}

impl Serialize for MesaValue {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where S: Serializer {
        match self {
            MesaValue::Num(n) => serializer.serialize_f64(*n),
            MesaValue::Str(s) => serializer.serialize_str(s),
            MesaValue::Bool(b) => serializer.serialize_bool(*b),
            MesaValue::Null => serializer.serialize_unit(),
            MesaValue::List(l) => {
                let items = l.lock().unwrap();
                items.serialize(serializer)
            }
            MesaValue::Map(m) => {
                let m = m.lock().unwrap();
                m.serialize(serializer)
            }
            _ => serializer.serialize_unit(),
        }
    }
}

impl MesaValue {
    pub fn from_json(v: serde_json::Value) -> Self {
        match v {
            serde_json::Value::Number(n) => MesaValue::Num(n.as_f64().unwrap_or(0.0)),
            serde_json::Value::String(s) => MesaValue::Str(s),
            serde_json::Value::Bool(b) => MesaValue::Bool(b),
            serde_json::Value::Null => MesaValue::Null,
            serde_json::Value::Array(a) => {
                let items = a.into_iter().map(MesaValue::from_json).collect();
                MesaValue::List(Arc::new(Mutex::new(items)))
            }
            serde_json::Value::Object(o) => {
                let mut m = HashMap::new();
                for (k, val) in o { m.insert(k, MesaValue::from_json(val)); }
                MesaValue::Map(Arc::new(Mutex::new(m)))
            }
        }
    }
}

impl fmt::Debug for MesaValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { write!(f, "{}", self) }
}

impl fmt::Display for MesaValue {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MesaValue::Num(n) => {
                if n.fract() == 0.0 && n.abs() < 1e15 { write!(f, "{}", *n as i64) }
                else { write!(f, "{}", n) }
            }
            MesaValue::Str(s) => write!(f, "{}", s),
            MesaValue::Bool(b) => write!(f, "{}", if *b { "verdadero" } else { "falso" }),
            MesaValue::List(l) => {
                let items = l.lock().unwrap();
                let parts: Vec<String> = items.iter().map(|v| format!("{}", v)).collect();
                write!(f, "[{}]", parts.join(", "))
            }
            MesaValue::Map(m) => {
                let m = m.lock().unwrap();
                let parts: Vec<String> = m.iter().map(|(k, v)| format!("{}: {}", k, v)).collect();
                write!(f, "{{{}}}", parts.join(", "))
            }
            MesaValue::Func(func) => write!(f, "<fn {}>", func.name),
            MesaValue::NativeFunc(name, _) => write!(f, "<built-in {}>", name),
            MesaValue::Native(_) => write!(f, "<native-handle>"),
            MesaValue::Lambda(_, _) => write!(f, "<lambda>"),
            MesaValue::Shape(s) => write!(f, "<forma {}>", s.name),
            MesaValue::Instance(inst) => {
                let inst = inst.lock().unwrap();
                let parts: Vec<String> = inst.fields.iter().map(|(k, v)| format!("{}: {}", k, v)).collect();
                write!(f, "{}{{{}}}", inst.shape_name, parts.join(", "))
            }
            MesaValue::Range(s, e, inc) => write!(f, "{}..{}{}", s, e, if *inc { "=" } else { "" }),
            MesaValue::Null => write!(f, "nada"),
        }
    }
}

impl MesaValue {
    pub fn is_truthy(&self) -> bool {
        match self {
            MesaValue::Bool(b) => *b,
            MesaValue::Null => false,
            MesaValue::Num(n) => *n != 0.0,
            MesaValue::Str(s) => !s.is_empty(),
            MesaValue::List(l) => !l.lock().unwrap().is_empty(),
            MesaValue::Map(m) => !m.lock().unwrap().is_empty(),
            _ => true,
        }
    }
    pub fn type_name(&self) -> &'static str {
        match self {
            MesaValue::Num(_) => "num",
            MesaValue::Str(_) => "str",
            MesaValue::Bool(_) => "bool",
            MesaValue::List(_) => "lista",
            MesaValue::Map(_) => "mapa",
            MesaValue::Func(_) | MesaValue::NativeFunc(_, _) | MesaValue::Lambda(_, _) => "funcion",
            MesaValue::Shape(_) => "forma",
            MesaValue::Instance(_) => "instancia",
            MesaValue::Native(_) => "nativo",
            MesaValue::Range(_, _, _) => "rango",
            MesaValue::Null => "nada",
        }
    }
    pub fn len(&self) -> usize {
        match self {
            MesaValue::Str(s) => s.len(),
            MesaValue::List(l) => l.lock().unwrap().len(),
            MesaValue::Map(m) => m.lock().unwrap().len(),
            _ => 1
        }
    }
}

impl PartialEq for MesaValue {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (MesaValue::Num(a), MesaValue::Num(b)) => a == b,
            (MesaValue::Str(a), MesaValue::Str(b)) => a == b,
            (MesaValue::Bool(a), MesaValue::Bool(b)) => a == b,
            (MesaValue::Null, MesaValue::Null) => true,
            (MesaValue::List(a), MesaValue::List(b)) => *a.lock().unwrap() == *b.lock().unwrap(),
            (MesaValue::Map(a), MesaValue::Map(b)) => *a.lock().unwrap() == *b.lock().unwrap(),
            (MesaValue::Range(s1, e1, inc1), MesaValue::Range(s2, e2, inc2)) => s1 == s2 && e1 == e2 && inc1 == inc2,
            _ => false,
        }
    }
}

#[derive(Debug, Clone)]
pub struct MesaError {
    pub message: String,
    pub kind: ErrorKind,
}

#[derive(Debug, Clone)]
pub enum ErrorKind {
    Runtime, Type, Name,
    Return(MesaValue),
    Break, Continue,
    Throw(MesaValue),
}

impl MesaError {
    pub fn runtime(msg: impl Into<String>) -> Self { MesaError { message: msg.into(), kind: ErrorKind::Runtime } }
    pub fn name(msg: impl Into<String>) -> Self { MesaError { message: msg.into(), kind: ErrorKind::Name } }
}
