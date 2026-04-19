// Mesa v4.0.0 - Scoped Environment
// Manages variable bindings with lexical scoping via parent chain

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use crate::value::{MesaValue, MesaError};

#[derive(Debug, Clone)]
pub struct Env {
    vars: HashMap<String, MesaValue>,
    parent: Option<Arc<Mutex<Env>>>,
}

impl Env {
    pub fn new() -> Self {
        Env { vars: HashMap::new(), parent: None }
    }

    pub fn new_child(parent: Arc<Mutex<Env>>) -> Self {
        Env { vars: HashMap::new(), parent: Some(parent) }
    }

    pub fn define(&mut self, name: impl Into<String>, val: MesaValue) {
        self.vars.insert(name.into(), val);
    }

    pub fn get(&self, name: &str) -> Result<MesaValue, MesaError> {
        if let Some(val) = self.vars.get(name) {
            return Ok(val.clone());
        }
        if let Some(parent) = &self.parent {
            return parent.lock().unwrap().get(name);
        }
        Err(MesaError::name(format!("Variable '{}' no definida", name)))
    }

    pub fn set(&mut self, name: &str, val: MesaValue) -> bool {
        if self.vars.contains_key(name) {
            self.vars.insert(name.to_string(), val);
            return true;
        }
        if let Some(parent) = &self.parent {
            return parent.lock().unwrap().set(name, val);
        }
        // auto-assign at current scope (untyped)
        self.vars.insert(name.to_string(), val);
        true
    }

    pub fn define_type(&mut self, name: impl Into<String>, val: MesaValue) {
        self.define(name, val);
    }

    pub fn export_all(&self) -> HashMap<String, MesaValue> {
        self.vars.clone()
    }
}
