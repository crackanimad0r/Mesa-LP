// Mesa v4.0.0 - Native C Codegen / Transpiler
// Converts Mesa AST to C and compiles with Clang/GCC

use crate::ast::{Stmt, Expr};

pub struct CodegenC {
    output: String,
}

impl CodegenC {
    pub fn new() -> Self {
        CodegenC { output: String::new() }
    }

    pub fn compile(&mut self, stmts: &[Stmt]) -> String {
        self.output.push_str("#include <stdio.h>\n#include <math.h>\n#include <stdbool.h>\n\n");
        
        // Functions first
        for stmt in stmts {
            if let Stmt::FuncDecl { .. } = stmt {
                self.visit_stmt(stmt);
            }
        }

        self.output.push_str("int main() {\n");
        for stmt in stmts {
            if !matches!(stmt, Stmt::FuncDecl { .. }) {
                self.visit_stmt(stmt);
            }
        }
        self.output.push_str("  return 0;\n}\n");
        self.output.clone()
    }

    fn visit_stmt(&mut self, stmt: &Stmt) {
        match stmt {
            Stmt::Expr(e) => {
                self.output.push_str("  ");
                self.visit_expr(e);
                self.output.push_str(";\n");
            }
            Stmt::VarDecl { name, value, .. } => {
                self.output.push_str(&format!("  double {} = ", name));
                if let Some(v) = value {
                    self.visit_expr(v);
                } else {
                    self.output.push_str("0.0");
                }
                self.output.push_str(";\n");
            }
            Stmt::Assign { target, value } => {
                self.output.push_str("  ");
                self.visit_expr(target);
                self.output.push_str(" = ");
                self.visit_expr(value);
                self.output.push_str(";\n");
            }
            Stmt::FuncDecl { name, params, body, .. } => {
                self.output.push_str(&format!("double {}(", name));
                for (i, p) in params.iter().enumerate() {
                    self.output.push_str(&format!("double {}", p.name));
                    if i < params.len() - 1 { self.output.push_str(", "); }
                }
                self.output.push_str(") {\n");
                for s in body {
                    self.visit_stmt(s);
                }
                self.output.push_str("  return 0.0;\n}\n\n");
            }
            Stmt::Return(val) => {
                self.output.push_str("  return ");
                if let Some(v) = val {
                    self.visit_expr(v);
                } else {
                    self.output.push_str("0.0");
                }
                self.output.push_str(";\n");
            }
            Stmt::If { condition, then_body, else_body, .. } => {
                self.output.push_str("  if (");
                self.visit_expr(condition);
                self.output.push_str(") {\n");
                for s in then_body { self.visit_stmt(s); }
                self.output.push_str("  }");
                if let Some(eb) = else_body {
                    self.output.push_str(" else {\n");
                    for s in eb { self.visit_stmt(s); }
                    self.output.push_str("  }\n");
                } else {
                    self.output.push_str("\n");
                }
            }
            _ => { /* todo: handle other stmts */ }
        }
    }

    fn visit_expr(&mut self, expr: &Expr) {
        match expr {
            Expr::Number(n) => self.output.push_str(&format!("{}", n)),
            Expr::Str(s) => self.output.push_str(&format!("\"{}\"", s)),
            Expr::Bool(b) => self.output.push_str(if *b { "1" } else { "0" }),
            Expr::Ident(n) => self.output.push_str(n),
            Expr::BinaryOp { left, op, right } => {
                self.output.push_str("(");
                self.visit_expr(left);
                self.output.push_str(&format!(" {} ", op));
                self.visit_expr(right);
                self.output.push_str(")");
            }
            Expr::Call { callee, args } => {
                let name = match &**callee {
                    Expr::Ident(n) => n.as_str(),
                    _ => "unknown",
                };
                if name == "decir" || name == "mostrar" {
                    self.output.push_str("printf(\"%g\\n\", ");
                    self.visit_expr(&args[0]);
                    self.output.push_str(")");
                } else {
                    self.output.push_str(&format!("{}(", name));
                    for (i, a) in args.iter().enumerate() {
                        self.visit_expr(a);
                        if i < args.len() - 1 { self.output.push_str(", "); }
                    }
                    self.output.push_str(")");
                }
            }
            _ => self.output.push_str("0.0"),
        }
    }
}
