from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Union


class ASTNode:
    pass


@dataclass
class Program(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class Block(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)


@dataclass
class LevelBlock(ASTNode):
    level: str = ''
    statements: List[ASTNode] = field(default_factory=list)


# === LITERALES ===

@dataclass
class NumberLiteral(ASTNode):
    value: float = 0


@dataclass
class StringLiteral(ASTNode):
    value: str = ''


@dataclass
class BoolLiteral(ASTNode):
    value: bool = False


@dataclass
class NoneLiteral(ASTNode):
    pass


# === IDENTIFICADORES ===

@dataclass
class Identifier(ASTNode):
    name: str = ''


@dataclass
class SelfExpr(ASTNode):
    pass


# === OPERACIONES ===

@dataclass
class BinaryOp(ASTNode):
    left: ASTNode = None
    operator: str = ''
    right: ASTNode = None


@dataclass
class UnaryOp(ASTNode):
    operator: str = ''
    operand: ASTNode = None


# === ASIGNACION Y VARIABLES ===

@dataclass
class Assignment(ASTNode):
    target: Any = None
    value: ASTNode = None


@dataclass
class VariableDecl(ASTNode):
    name: str = ''
    type_annotation: Any = None
    value: ASTNode = None
    is_const: bool = False
    is_mutable: bool = True


# === FUNCIONES ===

@dataclass
class Parameter(ASTNode):
    name: str = ''
    type_annotation: Any = None
    default_value: ASTNode = None
    is_self: bool = False
    is_mutable: bool = False


@dataclass
class FunctionDef(ASTNode):
    name: str = ''
    params: List[Any] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)
    return_type: Any = None
    is_public: bool = False
    is_async: bool = False
    is_static: bool = False


@dataclass
class Lambda(ASTNode):
    params: List[Any] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class Return(ASTNode):
    value: ASTNode = None


# === LLAMADAS ===

@dataclass
class CallExpr(ASTNode):
    callee: ASTNode = None
    args: List[ASTNode] = field(default_factory=list)
    kwargs: Dict[str, ASTNode] = field(default_factory=dict)


@dataclass
class MethodCall(ASTNode):
    object: ASTNode = None
    method: str = ''
    args: List[ASTNode] = field(default_factory=list)


@dataclass
class MemberAccess(ASTNode):
    object: ASTNode = None
    member: str = ''


@dataclass
class IndexAccess(ASTNode):
    object: ASTNode = None
    index: ASTNode = None


# === COLECCIONES ===

@dataclass
class ListLiteral(ASTNode):
    elements: List[ASTNode] = field(default_factory=list)


@dataclass
class MapLiteral(ASTNode):
    pairs: List[Tuple] = field(default_factory=list)


@dataclass
class SetLiteral(ASTNode):
    elements: List[ASTNode] = field(default_factory=list)


@dataclass
class TupleLiteral(ASTNode):
    elements: List[ASTNode] = field(default_factory=list)


@dataclass
class ListComprehension(ASTNode):
    expr: ASTNode = None
    variable: str = ''
    iterable: ASTNode = None
    condition: ASTNode = None


# === SHAPES (CLASES) ===

@dataclass
class Field(ASTNode):
    name: str = ''
    type_annotation: Any = None
    default_value: ASTNode = None
    is_public: bool = False
    is_static: bool = False
    is_const: bool = False


@dataclass
class ShapeDef(ASTNode):
    name: str = ''
    fields: List[Any] = field(default_factory=list)
    methods: List[Any] = field(default_factory=list)
    parent: Any = None
    type_params: List[str] = field(default_factory=list)
    is_public: bool = False


@dataclass
class StructInstantiation(ASTNode):
    type_name: str = ''
    fields: Dict[str, ASTNode] = field(default_factory=dict)


# === ENUMS ===

@dataclass
class EnumVariant(ASTNode):
    name: str = ''
    fields: List[Tuple] = field(default_factory=list)
    value: ASTNode = None


@dataclass
class EnumDef(ASTNode):
    name: str = ''
    variants: List[Any] = field(default_factory=list)
    is_public: bool = False


# === TRAITS ===

@dataclass
class TraitDef(ASTNode):
    name: str = ''
    methods: List[Any] = field(default_factory=list)
    parents: List[Any] = field(default_factory=list)
    is_public: bool = False


@dataclass
class ImplBlock(ASTNode):
    trait_name: Any = None
    type_name: Any = None
    methods: List[Any] = field(default_factory=list)


# === TIPOS ===

@dataclass
class TypeAnnotation(ASTNode):
    name: str = ''
    type_args: List[Any] = field(default_factory=list)
    is_nullable: bool = False
    is_pointer: bool = False


# === CONDICIONALES ===

@dataclass
class IfStatement(ASTNode):
    condition: ASTNode = None
    then_body: List[ASTNode] = field(default_factory=list)
    elif_parts: List[Tuple] = field(default_factory=list)
    else_body: List[ASTNode] = None


# === BUCLES ===

@dataclass
class WhileLoop(ASTNode):
    condition: ASTNode = None
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class ForLoop(ASTNode):
    variable: str = ''
    index_var: str = None
    iterable: ASTNode = None
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class RepeatLoop(ASTNode):
    times: ASTNode = None
    index_var: str = None
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class InfiniteLoop(ASTNode):
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class Break(ASTNode):
    pass


@dataclass
class Continue(ASTNode):
    pass


# === MATCH ===

@dataclass
class MatchStatement(ASTNode):
    value: ASTNode = None
    cases: List[Any] = field(default_factory=list)


@dataclass
class MatchCase(ASTNode):
    pattern: ASTNode = None
    guard: ASTNode = None
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class WildcardPattern(ASTNode):
    pass


@dataclass
class RangePattern(ASTNode):
    start: ASTNode = None
    end: ASTNode = None
    inclusive: bool = False


@dataclass
class EnumPattern(ASTNode):
    enum_name: str = ''
    variant: str = ''
    bindings: List[str] = field(default_factory=list)


# === ERRORES ===

@dataclass
class TryStatement(ASTNode):
    try_body: List[ASTNode] = field(default_factory=list)
    catch_var: str = None
    catch_body: List[ASTNode] = None
    finally_body: List[ASTNode] = None


@dataclass
class Throw(ASTNode):
    value: ASTNode = None


# === ASYNC ===

@dataclass
class TaskExpr(ASTNode):
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class AwaitExpr(ASTNode):
    value: ASTNode = None


# === MODULOS ===

@dataclass
class ModuleDef(ASTNode):
    name: str = ''


@dataclass
class ImportStmt(ASTNode):
    module: str = ''
    items: List[str] = None
    alias: str = None


# === TESTING ===

@dataclass
class TestDef(ASTNode):
    name: str = ''
    body: List[ASTNode] = field(default_factory=list)


# === EXPRESIONES ESPECIALES ===

@dataclass
class IfExpr(ASTNode):
    condition: ASTNode = None
    then_value: ASTNode = None
    else_value: ASTNode = None


@dataclass
class TernaryExpr(ASTNode):
    condition: ASTNode = None
    true_value: ASTNode = None
    false_value: ASTNode = None


@dataclass
class PipelineExpr(ASTNode):
    value: ASTNode = None
    function: ASTNode = None


# === MEMORIA / BAJO NIVEL ===

@dataclass
class RefExpr(ASTNode):
    operand: ASTNode = None
    is_mutable: bool = False


@dataclass
class DerefExpr(ASTNode):
    operand: ASTNode = None


@dataclass
class UnwrapExpr(ASTNode):
    operand: ASTNode = None


@dataclass
class PropagateExpr(ASTNode):
    operand: ASTNode = None


@dataclass
class SliceExpr(ASTNode):
    obj: ASTNode = None
    start: ASTNode = None
    end: ASTNode = None
    step: ASTNode = None


@dataclass
class NamespaceAccess(ASTNode):
    namespace: ASTNode = None
    member: str = ''


@dataclass
class MatchExpr(ASTNode):
    value: ASTNode = None
    cases: List[Any] = field(default_factory=list)


# === BAJO NIVEL: Nodos estilo C ===

@dataclass
class LowVarDecl(ASTNode):
    """Declaracion de variable de bajo nivel: int x = 5;"""
    var_type: str = ''
    name: str = ''
    value: ASTNode = None
    is_pointer: bool = False
    is_array: bool = False
    array_size: ASTNode = None


@dataclass
class LowArrayAccess(ASTNode):
    """Acceso a array de bajo nivel: arr[i]"""
    array: ASTNode = None
    index: ASTNode = None


@dataclass
class LowPointerOp(ASTNode):
    """Operacion de puntero: &x o *p"""
    operator: str = ''
    operand: ASTNode = None


@dataclass
class LowCast(ASTNode):
    """Cast de tipo: (float)x"""
    target_type: str = ''
    expr: ASTNode = None


@dataclass
class LowSizeof(ASTNode):
    """sizeof(tipo)"""
    target: str = ''


@dataclass
class LowMalloc(ASTNode):
    """reservar(tamaño) / malloc"""
    size: ASTNode = None
    element_type: str = ''


@dataclass
class LowFree(ASTNode):
    """liberar(ptr) / free"""
    pointer: ASTNode = None


@dataclass
class LowMemset(ASTNode):
    """llenar(ptr, valor, tamaño)"""
    pointer: ASTNode = None
    value: ASTNode = None
    size: ASTNode = None


@dataclass
class LowMemcpy(ASTNode):
    """copiar_mem(dest, src, tamaño)"""
    dest: ASTNode = None
    src: ASTNode = None
    size: ASTNode = None


@dataclass
class LowPrintAddr(ASTNode):
    """dir(x) - imprimir direccion de memoria"""
    operand: ASTNode = None


@dataclass
class LowBlock(ASTNode):
    """Bloque bajo { ... } con su propio contexto"""
    statements: List[ASTNode] = field(default_factory=list)


def print_ast(node, indent=0):
    result = "  " * indent + type(node).__name__ + "\n"
    return result


def count_nodes(node):
    return 1