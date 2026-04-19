// Mesa v4.0.0 - AST Node Definitions in Rust
// All statement and expression node types for the Mesa language

#[derive(Debug, Clone)]
pub struct Param {
    pub name: String,
    pub type_ann: Option<String>,
    pub default: Option<Expr>,
    pub is_self: bool,
}

#[derive(Debug, Clone)]
pub enum Stmt {
    Expr(Expr),
    VarDecl { name: String, type_ann: Option<String>, value: Option<Expr>, is_const: bool },
    Assign { target: Expr, value: Expr },
    FuncDecl { name: String, params: Vec<Param>, body: Vec<Stmt>, return_type: Option<String> },
    ShapeDecl { name: String, fields: Vec<(String, Option<String>)>, methods: Vec<Stmt> },
    If { condition: Expr, then_body: Vec<Stmt>, elif_parts: Vec<(Expr, Vec<Stmt>)>, else_body: Option<Vec<Stmt>> },
    While { condition: Expr, body: Vec<Stmt> },
    For { item: String, index: Option<String>, iterable: Expr, body: Vec<Stmt> },
    Return(Option<Expr>),
    Break,
    Continue,
    Import { path: String, alias: Option<String> },
    Try { body: Vec<Stmt>, catch_var: Option<String>, catch_body: Vec<Stmt>, finally_body: Option<Vec<Stmt>> },
    Throw(Expr),
    Match { value: Expr, arms: Vec<(Expr, Vec<Stmt>)> },
    Test { name: String, body: Vec<Stmt> },
    Block(Vec<Stmt>),
}

#[derive(Debug, Clone)]
pub enum Expr {
    Number(f64),
    Str(String),
    Bool(bool),
    Null,
    Ident(String),
    Self_,
    List(Vec<Expr>),
    Map(Vec<(String, Expr)>),
    StructInit { name: String, fields: Vec<(String, Expr)> },
    BinaryOp { left: Box<Expr>, op: String, right: Box<Expr> },
    UnaryOp { op: String, operand: Box<Expr> },
    Call { callee: Box<Expr>, args: Vec<Expr> },
    MethodCall { object: Box<Expr>, method: String, args: Vec<Expr> },
    MemberAccess { object: Box<Expr>, member: String },
    Index { object: Box<Expr>, index: Box<Expr> },
    Lambda { params: Vec<Param>, body: Vec<Stmt> },
    Pipeline { left: Box<Expr>, right: Box<Expr> },
    Conditional { cond: Box<Expr>, then: Box<Expr>, else_: Box<Expr> },
    Range { start: Box<Expr>, end: Box<Expr>, inclusive: bool },
}
