from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional

from antlr4 import ParserRuleContext

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
    ERROR = auto()  # tipo fantasma para propagar errores


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


@dataclass
class Scope:
    name: str
    kind: str  # "global" | "block" | "function" | "class" (futuro)
    symbols: Dict[str, Symbol]

    def __init__(self, name: str, kind: str):
        self.name = name
        self.kind = kind
        self.symbols = {}


class SymbolTable:
    def __init__(self) -> None:
        self.scopes: List[Scope] = [Scope(name="global", kind="global")]

    # ----- operaciones de ámbito -----
    def push(self, name: str, kind: str) -> None:
        self.scopes.append(Scope(name, kind))

    def pop(self) -> None:
        assert len(self.scopes) > 1, "No puedes sacar el ámbito global"
        self.scopes.pop()

    @property
    def current(self) -> Scope:
        return self.scopes[-1]

    # ----- operaciones de símbolo -----
    def declare(self, sym: Symbol) -> Optional[str]:
        """
        Declara en el ámbito ACTUAL. Devuelve string de error si redeclaración,
        si no, None.
        """
        if sym.name in self.current.symbols:
            first = self.current.symbols[sym.name]
            return (f"Identificador '{sym.name}' redeclarado en el mismo ámbito "
                    f"(declarado antes en línea {first.decl_line}, col {first.decl_col}).")
        self.current.symbols[sym.name] = sym
        return None

    def resolve(self, name: str) -> Optional[Symbol]:
        """
        Busca de adentro hacia afuera (entornos anidados).
        """
        for scope in reversed(self.scopes):
            if name in scope.symbols:
                return scope.symbols[name]
        return None

    # ----- export visual opcional -----
    def export_as_lines(self) -> List[str]:
        """
        Devuelve una representación de texto (útil para logging).
        """
        out: List[str] = []
        for i, s in enumerate(self.scopes):
            out.append(f"[{i}] {s.kind} — {s.name}")
            for sym in s.symbols.values():
                kind = "const" if sym.is_const else "var"
                out.append(f"    {sym.name}: {sym.ty.name.lower()} [{kind}] @ ({sym.decl_line},{sym.decl_col})")
        return out
# (Fin SymbolTable)


def is_numeric(t: TypeKind) -> bool:
    return t in (TypeKind.INTEGER, TypeKind.FLOAT)


def numeric_result(a: TypeKind, b: TypeKind) -> TypeKind:
    """
    Promoción numérica:
    - int op int -> int
    - int op float | float op int | float op float -> float
    """
    if a == TypeKind.ERROR or b == TypeKind.ERROR:
        return TypeKind.ERROR
    if a == TypeKind.FLOAT or b == TypeKind.FLOAT:
        return TypeKind.FLOAT
    return TypeKind.INTEGER


# -------------------------
# Visitor semántico
# -------------------------
class SemanticVisitor(CompiscriptVisitor):
    """
    Parte 1 (existente): aritmética + lógica.
    Añadido ahora:
      - Tabla de símbolos con entornos anidados (block).
      - Declaración/uso de variables (let/var/const).
      - Error si se usa variable no declarada.
      - Error si se redeclara en el mismo ámbito.
      - const requiere inicializador y no permite reasignación.
    """
    def __init__(self) -> None:
        super().__init__()
        self.issues: List[SemanticIssue] = []
        self.symtab = SymbolTable()

    # ---------- utilidades ----------
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

    # ---------- helpers de tipos ----------
    def _type_from_annotation(
        self,
        ann_ctx: Optional[CompiscriptParser.TypeAnnotationContext]
    ) -> Optional[TypeKind]:
        """
        Devuelve TypeKind a partir de una anotación `: tipo`.
        OJO: en Python, la regla 'type' se accede como type_().
        """
        if not ann_ctx:
            return None
        tctx = ann_ctx.type_()  # <- ¡esto es lo importante!
        base = tctx.baseType().getText()
        if base == "integer":
            return TypeKind.INTEGER
        if base == "boolean":
            return TypeKind.BOOLEAN
        if base == "string":
            return TypeKind.STRING
        # Otros identificadores/clases fuera de alcance por ahora
        return TypeKind.ERROR


    # ---------- literales ----------
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

    # ---------- primario / passthrough ----------
    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext) -> TypeKind:
        return self.visitChildren(ctx)

    # ---------- identificadores ----------
    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext) -> TypeKind:
        name = ctx.Identifier().getText()
        sym = self.symtab.resolve(name)
        if not sym:
            self.error(ctx, f"Uso de variable no declarada: '{name}'.")
            return TypeKind.ERROR
        return sym.ty

    # ---------- unario ----------
    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext) -> TypeKind:
        ty = self.visit(ctx.getChild(ctx.getChildCount() - 1))
        for i in range(ctx.getChildCount() - 1):
            op = ctx.getChild(i).getText()
            if op == '!':
                ty = self.require_boolean(ctx, ty, '!')
            elif op in ('+', '-'):
                if is_numeric(ty):
                    ty = ty
                else:
                    self.error(ctx, f"Operador unario '{op}' requiere integer/float; obtenido {ty.name.lower()}.")
                    ty = TypeKind.ERROR
        return ty

    # ---------- multiplicación / división ----------
    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext) -> TypeKind:
        ty = self.visit(ctx.getChild(0))
        i = 1
        while i < ctx.getChildCount():
            op = ctx.getChild(i).getText()
            right = self.visit(ctx.getChild(i + 1))
            if op in ('*', '/'):
                ty = self.require_numeric(ctx, ty, right, op)
            else:
                ty = TypeKind.ERROR if ty == TypeKind.ERROR or right == TypeKind.ERROR else ty
            i += 2
        return ty

    # ---------- suma / resta ----------
    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext) -> TypeKind:
        ty = self.visit(ctx.getChild(0))
        i = 1
        while i < ctx.getChildCount():
            op = ctx.getChild(i).getText()
            right = self.visit(ctx.getChild(i + 1))
            if op in ('+', '-'):
                ty = self.require_numeric(ctx, ty, right, op)
            i += 2
        return ty

    # ---------- lógico AND ----------
    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext) -> TypeKind:
        ty = self.visit(ctx.getChild(0))
        if ty != TypeKind.ERROR:
            ty = self.require_boolean(ctx, ty, '&&')
        i = 1
        while i < ctx.getChildCount():
            op = ctx.getChild(i).getText()
            right = self.visit(ctx.getChild(i + 1))
            if op == '&&':
                _ = self.require_boolean(ctx, right, '&&')
                ty = TypeKind.BOOLEAN if ty != TypeKind.ERROR and right != TypeKind.ERROR else TypeKind.ERROR
            i += 2
        return ty

    # ---------- lógico OR ----------
    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext) -> TypeKind:
        ty = self.visit(ctx.getChild(0))
        if ty != TypeKind.ERROR:
            ty = self.require_boolean(ctx, ty, '||')
        i = 1
        while i < ctx.getChildCount():
            op = ctx.getChild(i).getText()
            right = self.visit(ctx.getChild(i + 1))
            if op == '||':
                _ = self.require_boolean(ctx, right, '||')
                ty = TypeKind.BOOLEAN if ty != TypeKind.ERROR and right != TypeKind.ERROR else TypeKind.ERROR
            i += 2
        return ty

    # ---------- declaraciones ----------
    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext) -> Optional[TypeKind]:
        # ('let' | 'var') Identifier typeAnnotation? initializer? ';'
        name = ctx.Identifier().getText()

        # Cambia cualquier uso de .type() por el helper:
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
        # 'const' Identifier typeAnnotation? '=' expression ';'
        name = ctx.Identifier().getText()

        # ¡Aquí estaba el fallo!
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


    # ---------- asignaciones ----------
    def visitAssignExpr(self, ctx: CompiscriptParser.AssignExprContext) -> TypeKind:
        lhs_ctx = ctx.lhs  # leftHandSide
        # primaryAtom # IdentifierExpr, sin sufijos
        is_ident = isinstance(lhs_ctx.primaryAtom(), CompiscriptParser.IdentifierExprContext)
        has_suffix = len(lhs_ctx.suffixOp()) > 0 if hasattr(lhs_ctx, "suffixOp") else False
        if not is_ident or has_suffix:
            return self.visit(ctx.assignmentExpr())  # fuera de alcance: propiedades/índices/llamadas

        name = lhs_ctx.primaryAtom().Identifier().getText()
        sym = self.symtab.resolve(name)
        if not sym:
            self.error(ctx, f"Asignación a variable no declarada: '{name}'.")
            return TypeKind.ERROR
        if sym.is_const:
            self.error(ctx, f"No se puede asignar a constante '{name}'.")
        rhs_ty = self.visit(ctx.assignmentExpr())
        if sym.ty != TypeKind.ERROR and rhs_ty != TypeKind.ERROR and sym.ty != rhs_ty:
            self.error(ctx, f"Tipo incompatible en asignación a '{name}': esperado {sym.ty.name.lower()}, obtenido {rhs_ty.name.lower()}.")
        return sym.ty if sym.ty != TypeKind.ERROR else rhs_ty


    # ---------- bloques/ámbitos ----------
    def visitBlock(self, ctx: CompiscriptParser.BlockContext) -> Optional[TypeKind]:
        self.symtab.push(name="block", kind="block")
        for st in ctx.statement():
            self.visit(st)
        self.symtab.pop()
        return None

    # ---------- sentencias de control que abren ámbito (for/foreach/try/catch) ----------
    def visitForStatement(self, ctx: CompiscriptParser.ForStatementContext) -> Optional[TypeKind]:
        self.symtab.push(name="for", kind="block")
        # init
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())
        # cond
        if ctx.expression(0):
            cond_ty = self.visit(ctx.expression(0))
            if cond_ty != TypeKind.BOOLEAN and cond_ty != TypeKind.ERROR:
                self.error(ctx, "La condición del 'for' debe ser boolean.")
        # step
        if ctx.expression(1):
            self.visit(ctx.expression(1))
        # body
        self.visit(ctx.block())
        self.symtab.pop()
        return None

    def visitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext) -> Optional[TypeKind]:
        self.symtab.push(name="foreach", kind="block")
        # El identificador del foreach se introduce en el ámbito del foreach
        name = ctx.Identifier().getText()
        err = self.symtab.declare(Symbol(name=name, ty=TypeKind.ERROR, is_const=False,
                                         decl_line=ctx.start.line, decl_col=ctx.start.column))
        if err:
            self.error(ctx, err)
        self.visit(ctx.expression())
        self.visit(ctx.block())
        self.symtab.pop()
        return None

    # ---------- fallback ----------
    def visitChildren(self, node: ParserRuleContext) -> TypeKind:
        last: Optional[TypeKind] = None
        for i in range(node.getChildCount()):
            child = node.getChild(i)
            res = child.accept(self) if hasattr(child, "accept") else None
            last = res if res is not None else last
        return last if last is not None else TypeKind.ERROR