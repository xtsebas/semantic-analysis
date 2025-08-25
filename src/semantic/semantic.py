from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional

from antlr4 import ParserRuleContext

try:
    from program.CompiscriptParser import CompiscriptParser
    from program.CompiscriptVisitor import CompiscriptVisitor
except ImportError:
    # Fallback for different import paths
    from CompiscriptParser import CompiscriptParser
    from CompiscriptVisitor import CompiscriptVisitor


# -------------------------
# Tipos del lenguaje
# -------------------------
class TypeKind(Enum):
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    STRING = auto()
    NULL = auto()
    ERROR = auto()


@dataclass
class SemanticIssue:
    line: int
    column: int
    message: str


# -------------------------
# Símbolos y ámbitos
# -------------------------
@dataclass
class Symbol:
    name: str
    ty: TypeKind
    is_const: bool
    decl_line: int
    decl_col: int
    is_function: bool = False


@dataclass
class Scope:
    name: str
    kind: str
    symbols: Dict[str, Symbol]

    def __init__(self, name: str, kind: str):
        self.name = name
        self.kind = kind
        self.symbols = {}


class SymbolTable:
    def __init__(self) -> None:
        self.scopes: List[Scope] = [Scope(name="global", kind="global")]

    def push(self, name: str, kind: str) -> None:
        self.scopes.append(Scope(name, kind))

    def pop(self) -> None:
        assert len(self.scopes) > 1, "No puedes sacar el ámbito global"
        self.scopes.pop()

    @property
    def current(self) -> Scope:
        return self.scopes[-1]

    def declare(self, sym: Symbol) -> Optional[str]:
        if sym.name in self.current.symbols:
            first = self.current.symbols[sym.name]
            return (f"Identificador '{sym.name}' redeclarado en el mismo ámbito "
                    f"(declarado antes en línea {first.decl_line}, col {first.decl_col}).")
        self.current.symbols[sym.name] = sym
        return None

    def export_as_lines(self) -> List[str]:
        """
        Devuelve una representación textual de la tabla de símbolos
        (lo que espera Driver.py para imprimirla).
        """
        out: List[str] = []
        for i, scope in enumerate(self.scopes):
            out.append(f"[{i}] {scope.kind} — {scope.name}")
            for sym in scope.symbols.values():
                kind = "func" if getattr(sym, "is_function", False) else ("const" if sym.is_const else "var")
                out.append(f"    {sym.name}: {sym.ty.name.lower()} [{kind}] @ ({sym.decl_line},{sym.decl_col})")
        return out
        
    def resolve(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self.scopes):
            if name in scope.symbols:
                return scope.symbols[name]
        return None


def is_numeric(t: TypeKind) -> bool:
    return t in (TypeKind.INTEGER, TypeKind.FLOAT)


def numeric_result(a: TypeKind, b: TypeKind) -> TypeKind:
    if a == TypeKind.ERROR or b == TypeKind.ERROR:
        return TypeKind.ERROR
    if a == TypeKind.FLOAT or b == TypeKind.FLOAT:
        return TypeKind.FLOAT
    return TypeKind.INTEGER


# -------------------------
# Visitor semántico con labels
# -------------------------
class SemanticVisitor(CompiscriptVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.issues: List[SemanticIssue] = []
        self.symtab = SymbolTable()

    def error(self, ctx: ParserRuleContext, msg: str) -> None:
        token = ctx.start
        self.issues.append(SemanticIssue(line=token.line, column=token.column, message=msg))

    def require_numeric(self, ctx: ParserRuleContext, left: TypeKind, right: TypeKind, op: str) -> TypeKind:
        if is_numeric(left) and is_numeric(right):
            return numeric_result(left, right)
        self.error(ctx, f"Operación aritmética '{op}' requiere integer/float; obtenidos {left.name.lower()} y {right.name.lower()}.")
        return TypeKind.ERROR

    def require_boolean(self, ctx: ParserRuleContext, ty: TypeKind, op: str) -> TypeKind:
        if ty == TypeKind.BOOLEAN:
            return TypeKind.BOOLEAN
        self.error(ctx, f"Operador lógico '{op}' requiere boolean; obtenido {ty.name.lower()}.")
        return TypeKind.ERROR

    def _type_from_annotation(self, ann_ctx: Optional[CompiscriptParser.TypeAnnotationContext]) -> Optional[TypeKind]:
        if not ann_ctx:
            return None
        tctx = ann_ctx.type_()
        base = tctx.baseType().getText()
        if base == "integer":
            return TypeKind.INTEGER
        if base == "boolean":
            return TypeKind.BOOLEAN
        if base == "string":
            return TypeKind.STRING
        return TypeKind.ERROR

    # ---------- LITERALES ----------
    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext) -> TypeKind:
        text = ctx.getText()
        if text == "true" or text == "false":
            return TypeKind.BOOLEAN
        if text.startswith('"') and text.endswith('"'):
            return TypeKind.STRING
        if text == "null":
            return TypeKind.NULL
        try:
            if "." in text:
                float(text)
                return TypeKind.FLOAT
            else:
                int(text)
                return TypeKind.INTEGER
        except Exception:
            return TypeKind.ERROR

    # ---------- IDENTIFICADORES ----------
    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext) -> TypeKind:
        name = ctx.Identifier().getText()
        sym = self.symtab.resolve(name)
        if not sym:
            self.error(ctx, f"Uso de variable no declarada: '{name}'.")
            return TypeKind.ERROR
        return sym.ty

    # ---------- EXPRESIONES CON LABELS ----------

    # Operadores relacionales: <, <=, >, >=
    def visitRelationalOp(self, ctx: CompiscriptParser.RelationalOpContext) -> TypeKind:
        left_ty = self.visit(ctx.relationalExpr())
        right_ty = self.visit(ctx.additiveExpr())
        op = ctx.op.text
        
        if (is_numeric(left_ty) and is_numeric(right_ty)) or \
           (left_ty == TypeKind.STRING and right_ty == TypeKind.STRING):
            return TypeKind.BOOLEAN  # ¡RESULTADO CORRECTO!
        else:
            self.error(ctx, f"Comparación '{op}' requiere operandos compatibles; "
                            f"obtenidos {left_ty.name.lower()} y {right_ty.name.lower()}.")
            return TypeKind.ERROR

    def visitRelationalPassthrough(self, ctx: CompiscriptParser.RelationalPassthroughContext) -> TypeKind:
        return self.visit(ctx.additiveExpr())

    # Operadores de igualdad: ==, !=
    def visitEqualityOp(self, ctx: CompiscriptParser.EqualityOpContext) -> TypeKind:
        left_ty = self.visit(ctx.equalityExpr())
        right_ty = self.visit(ctx.relationalExpr())
        op = ctx.op.text
        
        compatible = False
        if left_ty == right_ty:
            compatible = True
        elif is_numeric(left_ty) and is_numeric(right_ty):
            compatible = True
        elif left_ty == TypeKind.NULL or right_ty == TypeKind.NULL:
            compatible = True

        if not compatible:
            self.error(ctx, f"Comparación '{op}' entre tipos incompatibles "
                            f"{left_ty.name.lower()} y {right_ty.name.lower()}.")
            return TypeKind.ERROR
        
        return TypeKind.BOOLEAN  # ¡RESULTADO CORRECTO!

    def visitEqualityPassthrough(self, ctx: CompiscriptParser.EqualityPassthroughContext) -> TypeKind:
        return self.visit(ctx.relationalExpr())

    # Operadores lógicos: &&
    def visitLogicalAndOp(self, ctx: CompiscriptParser.LogicalAndOpContext) -> TypeKind:
        left_ty = self.visit(ctx.logicalAndExpr())
        right_ty = self.visit(ctx.equalityExpr())
        
        left_bool = self.require_boolean(ctx, left_ty, '&&')
        right_bool = self.require_boolean(ctx, right_ty, '&&')
        
        return TypeKind.BOOLEAN if left_bool != TypeKind.ERROR and right_bool != TypeKind.ERROR else TypeKind.ERROR

    def visitLogicalAndPassthrough(self, ctx: CompiscriptParser.LogicalAndPassthroughContext) -> TypeKind:
        return self.visit(ctx.equalityExpr())

    # Operadores lógicos: ||
    def visitLogicalOrOp(self, ctx: CompiscriptParser.LogicalOrOpContext) -> TypeKind:
        left_ty = self.visit(ctx.logicalOrExpr())
        right_ty = self.visit(ctx.logicalAndExpr())
        
        left_bool = self.require_boolean(ctx, left_ty, '||')
        right_bool = self.require_boolean(ctx, right_ty, '||')
        
        return TypeKind.BOOLEAN if left_bool != TypeKind.ERROR and right_bool != TypeKind.ERROR else TypeKind.ERROR

    def visitLogicalOrPassthrough(self, ctx: CompiscriptParser.LogicalOrPassthroughContext) -> TypeKind:
        return self.visit(ctx.logicalAndExpr())

    # Operadores aritméticos: +, -
    def visitAdditiveOp(self, ctx: CompiscriptParser.AdditiveOpContext) -> TypeKind:
        left_ty = self.visit(ctx.additiveExpr())
        right_ty = self.visit(ctx.multiplicativeExpr())
        op = ctx.op.text
        
        return self.require_numeric(ctx, left_ty, right_ty, op)

    def visitAdditivePassthrough(self, ctx: CompiscriptParser.AdditivePassthroughContext) -> TypeKind:
        return self.visit(ctx.multiplicativeExpr())

    # Operadores multiplicativos: *, /, %
    def visitMultiplicativeOp(self, ctx: CompiscriptParser.MultiplicativeOpContext) -> TypeKind:
        left_ty = self.visit(ctx.multiplicativeExpr())
        right_ty = self.visit(ctx.unaryExpr())
        op = ctx.op.text
        
        return self.require_numeric(ctx, left_ty, right_ty, op)

    def visitMultiplicativePassthrough(self, ctx: CompiscriptParser.MultiplicativePassthroughContext) -> TypeKind:
        return self.visit(ctx.unaryExpr())

    # Operadores unarios: -, !
    def visitUnaryOp(self, ctx: CompiscriptParser.UnaryOpContext) -> TypeKind:
        operand_ty = self.visit(ctx.unaryExpr())
        op = ctx.op.text
        
        if op == '!':
            return self.require_boolean(ctx, operand_ty, '!')
        elif op in ('+', '-'):
            if is_numeric(operand_ty):
                return operand_ty
            else:
                self.error(ctx, f"Operador unario '{op}' requiere integer/float; obtenido {operand_ty.name.lower()}.")
                return TypeKind.ERROR
        
        return TypeKind.ERROR

    def visitUnaryPassthrough(self, ctx: CompiscriptParser.UnaryPassthroughContext) -> TypeKind:
        return self.visit(ctx.primaryExpr())

    # Expresiones primarias
    def visitLiteralPrimary(self, ctx: CompiscriptParser.LiteralPrimaryContext) -> TypeKind:
        return self.visit(ctx.literalExpr())

    def visitLeftHandSidePrimary(self, ctx: CompiscriptParser.LeftHandSidePrimaryContext) -> TypeKind:
        return self.visit(ctx.leftHandSide())

    def visitParenthesizedExpr(self, ctx: CompiscriptParser.ParenthesizedExprContext) -> TypeKind:
        return self.visit(ctx.expression())

    # ---------- DECLARACIONES ----------
    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext) -> Optional[TypeKind]:
        name = ctx.Identifier().getText()
        return_type = TypeKind.INTEGER
        
        if ctx.type_():
            base = ctx.type_().baseType().getText()
            if base == "integer":
                return_type = TypeKind.INTEGER
            elif base == "boolean":
                return_type = TypeKind.BOOLEAN
            elif base == "string":
                return_type = TypeKind.STRING
            else:
                return_type = TypeKind.ERROR

        err = self.symtab.declare(Symbol(
            name=name, ty=return_type, is_const=False, is_function=True,
            decl_line=ctx.start.line, decl_col=ctx.start.column
        ))
        if err:
            self.error(ctx, err)

        self.symtab.push(name=f"function_{name}", kind="function")

        if ctx.parameters():
            for param_ctx in ctx.parameters().parameter():
                param_name = param_ctx.Identifier().getText()
                param_type = TypeKind.INTEGER
                
                if param_ctx.type_():
                    base = param_ctx.type_().baseType().getText()
                    if base == "integer":
                        param_type = TypeKind.INTEGER
                    elif base == "boolean":
                        param_type = TypeKind.BOOLEAN
                    elif base == "string":
                        param_type = TypeKind.STRING
                    else:
                        param_type = TypeKind.ERROR

                param_err = self.symtab.declare(Symbol(
                    name=param_name, ty=param_type, is_const=False,
                    decl_line=param_ctx.start.line, decl_col=param_ctx.start.column
                ))
                if param_err:
                    self.error(param_ctx, param_err)

        self.visit(ctx.block())
        self.symtab.pop()
        return None

    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext) -> Optional[TypeKind]:
        name = ctx.Identifier().getText()
        ann_ty = self._type_from_annotation(ctx.typeAnnotation() if ctx.typeAnnotation() else None)

        init_ty: Optional[TypeKind] = None
        if ctx.initializer():
            init_ty = self.visit(ctx.initializer().expression())

        ty = ann_ty if ann_ty is not None else (init_ty if init_ty is not None else TypeKind.ERROR)

        if ann_ty is not None and init_ty is not None and ann_ty != TypeKind.ERROR and init_ty != TypeKind.ERROR and ann_ty != init_ty:
            self.error(ctx, f"Tipo incompatible en inicialización de '{name}': declarado {ann_ty.name.lower()}, inicializador {init_ty.name.lower()}.")

        err = self.symtab.declare(Symbol(
            name=name, ty=ty, is_const=False,
            decl_line=ctx.start.line, decl_col=ctx.start.column
        ))
        if err:
            self.error(ctx, err)
        return None

    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext) -> Optional[TypeKind]:
        name = ctx.Identifier().getText()
        ann_ty = self._type_from_annotation(ctx.typeAnnotation() if ctx.typeAnnotation() else None)
        init_ty = self.visit(ctx.expression())

        if ann_ty is not None and init_ty is not None and ann_ty != TypeKind.ERROR and init_ty != TypeKind.ERROR and ann_ty != init_ty:
            self.error(ctx, f"Tipo incompatible en const '{name}': declarado {ann_ty.name.lower()}, inicializador {init_ty.name.lower()}.")

        ty = ann_ty if ann_ty is not None else (init_ty if init_ty is not None else TypeKind.ERROR)

        err = self.symtab.declare(Symbol(
            name=name, ty=ty, is_const=True,
            decl_line=ctx.start.line, decl_col=ctx.start.column
        ))
        if err:
            self.error(ctx, err)
        return None

    def visitBlock(self, ctx: CompiscriptParser.BlockContext) -> Optional[TypeKind]:
        self.symtab.push(name="block", kind="block")
        for st in ctx.statement():
            self.visit(st)
        self.symtab.pop()
        return None

    # ---------- FALLBACK ----------
    def visitChildren(self, node: ParserRuleContext) -> TypeKind:
        last: Optional[TypeKind] = None
        for i in range(node.getChildCount()):
            child = node.getChild(i)
            res = child.accept(self) if hasattr(child, "accept") else None
            last = res if res is not None else last
        return last if last is not None else TypeKind.ERROR