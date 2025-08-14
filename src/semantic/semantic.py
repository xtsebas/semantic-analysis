from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

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
    ERROR = auto()  


@dataclass
class SemanticIssue:
    line: int
    column: int
    message: str


def is_numeric(t: TypeKind) -> bool:
    return t in (TypeKind.INTEGER, TypeKind.FLOAT)


def numeric_result(a: TypeKind, b: TypeKind) -> TypeKind:
    """
    Reglas de promoción numérica simples:
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
    Implementa Parte 1 del sistema de tipos:
      - Aritmética: + - * / solo entre integer/float
      - Lógica: && || ! solo sobre boolean
    """
    def __init__(self) -> None:
        super().__init__()
        self.issues: List[SemanticIssue] = []

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

    # ---------- literales ----------
    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext) -> TypeKind:
        text = ctx.getText()
        # Orden importa (true/false antes que identificadores)
        if text == "true" or text == "false":
            return TypeKind.BOOLEAN
        if text.startswith('"') and text.endswith('"'):
            return TypeKind.STRING
        if text == "null":
            return TypeKind.NULL
        # números (muy simple: si contiene '.', lo tratamos como float)
        try:
            if "." in text:
                float(text)
                return TypeKind.FLOAT
            else:
                int(text)
                return TypeKind.INTEGER
        except Exception:
            # Desconocido -> propaga; no es objetivo de Parte 1
            return TypeKind.ERROR

    # ---------- primario / passthrough ----------
    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext) -> TypeKind:
        # Delega al hijo adecuado
        return self.visitChildren(ctx)

    # ---------- unario ----------
    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext) -> TypeKind:
        # Gram. típica: ('!' | '+' | '-')* primaryExpr
        # Tomamos el tipo del operando y validamos por cada prefijo.
        ty = self.visit(ctx.getChild(ctx.getChildCount() - 1))  # último hijo es el operando
        # Recorre prefijos desde la izquierda
        for i in range(ctx.getChildCount() - 1):
            op = ctx.getChild(i).getText()
            if op == '!':
                ty = self.require_boolean(ctx, ty, '!')
            elif op in ('+', '-'):
                if is_numeric(ty):
                    # unario mantiene el tipo (int o float)
                    ty = ty
                else:
                    self.error(ctx, f"Operador unario '{op}' requiere integer/float; obtenido {ty.name.lower()}.")
                    ty = TypeKind.ERROR
        return ty

    # ---------- multiplicación / división ----------
    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext) -> TypeKind:
        # típica forma: unaryExpr (( '*' | '/' | '%') unaryExpr)*
        # (aquí solo chequeamos * y / según el alcance de la tarea)
        # localizamos los operandos: son los hijos en posiciones impares 0-based: 0,2,4,...
        ty = self.visit(ctx.getChild(0))
        i = 1
        while i < ctx.getChildCount():
            op = ctx.getChild(i).getText()
            right = self.visit(ctx.getChild(i + 1))
            if op in ('*', '/'):
                ty = self.require_numeric(ctx, ty, right, op)
            else:
                # otros operadores (p.ej. % si existiera) pueden tratarse luego
                ty = TypeKind.ERROR if ty == TypeKind.ERROR or right == TypeKind.ERROR else ty
            i += 2
        return ty

    # ---------- suma / resta ----------
    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext) -> TypeKind:
        # típica forma: multiplicativeExpr (( '+' | '-') multiplicativeExpr)*
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
        # logicalAndExpr: equalityExpr ('&&' equalityExpr)*;
        ty = self.visit(ctx.getChild(0))
        # El primer operando debe ser boolean también
        if ty != TypeKind.ERROR:
            ty = self.require_boolean(ctx, ty, '&&')
        i = 1
        while i < ctx.getChildCount():
            op = ctx.getChild(i).getText()
            right = self.visit(ctx.getChild(i + 1))
            if op == '&&':
                # Cada lado debe ser boolean
                _ = self.require_boolean(ctx, right, '&&')
                ty = TypeKind.BOOLEAN if ty != TypeKind.ERROR and right != TypeKind.ERROR else TypeKind.ERROR
            i += 2
        return ty

    # ---------- lógico OR ----------
    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext) -> TypeKind:
        # logicalOrExpr: logicalAndExpr ('||' logicalAndExpr)*;
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

    # ---------- fallback ----------
    def visitChildren(self, node: ParserRuleContext) -> TypeKind:
        # Por defecto, retorna el tipo del último hijo visitado si existe
        last: Optional[TypeKind] = None
        for i in range(node.getChildCount()):
            child = node.getChild(i)
            res = child.accept(self) if hasattr(child, "accept") else None
            last = res if res is not None else last
        # Si no hubo ningún hijo con tipo, devolvemos ERROR para no romper
        return last if last is not None else TypeKind.ERROR
