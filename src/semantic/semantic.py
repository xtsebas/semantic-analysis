from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any

# Nota: No heredamos del visitor generado. ANTLR igual invocará
# visit<NombreContexto> si el método existe en esta clase.
class CompiscriptVisitor:
    def visitChildren(self, ctx):
        n = ctx.getChildCount() if hasattr(ctx, "getChildCount") else 0
        last = None
        for i in range(n):
            c = ctx.getChild(i)
            if hasattr(c, "accept"):
                last = c.accept(self)
        return last

# ========================
# Tipos
# ========================
class TypeKind(Enum):
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    STRING = auto()
    VOID = auto()
    NULL = auto()
    ERROR = auto()

    @staticmethod
    def is_numeric(t: "TypeKind") -> bool:
        return t in (TypeKind.INTEGER, TypeKind.FLOAT)

    @staticmethod
    def common_numeric(t1: "TypeKind", t2: "TypeKind") -> "TypeKind":
        if TypeKind.ERROR in (t1, t2):
            return TypeKind.ERROR
        if t1 == TypeKind.FLOAT or t2 == TypeKind.FLOAT:
            return TypeKind.FLOAT
        if t1 == TypeKind.INTEGER and t2 == TypeKind.INTEGER:
            return TypeKind.INTEGER
        return TypeKind.ERROR

@dataclass(frozen=True)
class ArrayType:
    elem: Any  # TypeKind | ArrayType

def is_array(t) -> bool: return isinstance(t, ArrayType)
def array_of(elem) -> ArrayType: return ArrayType(elem)
def elem_type_of(t): return t.elem if isinstance(t, ArrayType) else None

@dataclass(frozen=True)
class ObjectType:
    class_name: str

def is_object(t) -> bool: return isinstance(t, ObjectType)

def same_type(a, b) -> bool:
    if isinstance(a, ArrayType) and isinstance(b, ArrayType):
        return same_type(a.elem, b.elem)
    return a == b

@dataclass
class SemanticIssue:
    line: int
    column: int
    message: str

# ========================
# Símbolos
# ========================
@dataclass
class VariableSymbol:
    name: str
    type: Any
    is_const: bool = False

@dataclass
class FunctionSymbol:
    name: str
    params: List[Tuple[str, Any]]
    return_type: Any

@dataclass
class ClassMember:
    name: str
    type: Any
    is_method: bool = False
    params: Optional[List[Tuple[str, Any]]] = None
    return_type: Optional[Any] = None

@dataclass
class ClassSymbol:
    name: str
    members: Dict[str, ClassMember] = field(default_factory=dict)
    _base_name: Optional[str] = None

class SymbolTable:
    def __init__(self):
        self.globals: Dict[str, Any] = {}
        self.scopes: List[Dict[str, Any]] = [self.globals]
        self.classes: Dict[str, ClassSymbol] = {}
        self.functions: Dict[str, FunctionSymbol] = {}

    # Ámbitos
    def push_scope(self):
        self.scopes.append({})
    def pop_scope(self):
        self.scopes.pop()
    def current_scope(self) -> Dict[str, Any]:
        return self.scopes[-1]

    # Definir/Resolver
    def define_var(self, sym: VariableSymbol) -> bool:
        scope = self.current_scope()
        if sym.name in scope:
            return False
        scope[sym.name] = sym
        return True

    def resolve_var(self, name: str) -> Optional[VariableSymbol]:
        for scope in reversed(self.scopes):
            sym = scope.get(name)
            if isinstance(sym, VariableSymbol):
                return sym
        return None

    def define_func(self, f: FunctionSymbol) -> bool:
        if f.name in self.functions:
            return False
        self.functions[f.name] = f
        self.current_scope()[f.name] = f
        return True

    def resolve_func(self, name: str) -> Optional[FunctionSymbol]:
        if name in self.functions:
            return self.functions[name]
        for scope in reversed(self.scopes):
            sym = scope.get(name)
            if isinstance(sym, FunctionSymbol):
                return sym
        return None

    def define_class(self, c: ClassSymbol) -> bool:
        if c.name in self.classes:
            return False
        self.classes[c.name] = c
        self.current_scope()[c.name] = c
        return True

    def resolve_class(self, name: str) -> Optional[ClassSymbol]:
        if name in self.classes:
            return self.classes[name]
        for scope in reversed(self.scopes):
            sym = scope.get(name)
            if isinstance(sym, ClassSymbol):
                return sym
        return None

    def export_as_lines(self) -> List[str]:
        lines: List[str] = []
        lines.append("== SYMBOL TABLE ==")
        for i, scope in enumerate(self.scopes):
            scope_tag = "global" if i == 0 else f"scope_{i}"
            lines.append(f"[{scope_tag}]")
            for k, v in scope.items():
                if isinstance(v, VariableSymbol):
                    lines.append(f"  var {v.name}: {self._tname(v.type)}{' (const)' if v.is_const else ''}")
                elif isinstance(v, FunctionSymbol):
                    sig = ", ".join(f"{n}: {self._tname(t)}" for n, t in v.params)
                    lines.append(f"  func {v.name}({sig}) -> {self._tname(v.return_type)}")
                elif isinstance(v, ClassSymbol):
                    lines.append(f"  class {v.name} ...")
                else:
                    lines.append(f"  {k}: {type(v).__name__}")
        lines.append("== FUNCTIONS ==")
        for f in self.functions.values():
            sig = ", ".join(f"{n}: {self._tname(t)}" for n, t in f.params)
            lines.append(f"  {f.name}({sig}) -> {self._tname(f.return_type)}")
        lines.append("== CLASSES ==")
        for c in self.classes.values():
            lines.append(f"  class {c.name}")
            for m in c.members.values():
                if m.is_method:
                    ps = ", ".join(f"{n}: {self._tname(t)}" for n, t in (m.params or []))
                    rt = self._tname(m.return_type) if m.return_type else "VOID"
                    lines.append(f"    method {m.name}({ps}) -> {rt}")
                else:
                    lines.append(f"    field  {m.name}: {self._tname(m.type)}")
        return lines

    def _tname(self, t: Any) -> str:
        if isinstance(t, ArrayType): return f"{self._tname(t.elem)}[]"
        if isinstance(t, ObjectType): return t.class_name
        if isinstance(t, TypeKind): return t.name
        return str(t)

# ========================
# Visitor semántico
# ========================
class SemanticVisitor(CompiscriptVisitor):
    def __init__(self):
        self.issues: List[SemanticIssue] = []
        self.symtab = SymbolTable()
        self.loop_depth: int = 0
        self.current_function: Optional[FunctionSymbol] = None
        self.current_function_has_return: bool = False
        self.current_class: Optional[ClassSymbol] = None
        self.in_constructor: bool = False

    # ---- utilidades
    def error(self, ctx, msg: str):
        line = getattr(ctx, "start", None).line if hasattr(ctx, "start") else -1
        col  = getattr(ctx, "start", None).column if hasattr(ctx, "start") else -1
        self.issues.append(SemanticIssue(line, col, msg))

    def expect_boolean(self, ctx, t: Any, where: str):
        if t != TypeKind.BOOLEAN and t != TypeKind.ERROR:
            self.error(ctx, f"La condición en {where} debe ser booleana, no {self.symtab._tname(t)}.")
    
    def _get_type_node(self, ctx):
        if ctx is None:
            return None
        if hasattr(ctx, "type_"):
            return ctx.type_()
        if hasattr(ctx, "type"):
            return ctx.type()
        return None
    
    def _type_of_simple_identifier(self, node, fallback_type):
        """
        Si `node` textual es un identificador simple (sin '.', '(', '['),
        y existe una VariableSymbol con ese nombre en el scope, devuelve su tipo.
        En otro caso, vuelve a fallback_type.
        """
        try:
            txt = node.getText()
        except Exception:
            return fallback_type
        if not txt or any(ch in txt for ch in ".([)]"):
            return fallback_type
        var = self.symtab.resolve_var(txt)
        return var.type if var else fallback_type

    # ========================
    # program / block / statements
    # ========================
    def visitProgram(self, ctx):
        for st in ctx.statement():
            self.visit(st)
        return None

    def visitBlock(self, ctx):
        self.symtab.push_scope()
        for st in ctx.statement():
            self.visit(st)
        self.symtab.pop_scope()
        return None

    # variableDeclaration: ('let' | 'var') Identifier typeAnnotation? initializer? ';'
    def visitVariableDeclaration(self, ctx):
        name = ctx.Identifier().getText()
        vtype = TypeKind.ERROR
        if ctx.typeAnnotation():
            vtype = self.type_from_type(self._get_type_node(ctx.typeAnnotation()))
        init_t = None
        if ctx.initializer():
            init_t = self.visit(ctx.initializer().expression())
            if vtype == TypeKind.ERROR and init_t is not None:
                vtype = init_t
        if init_t is not None and not self.is_assignable(vtype, init_t):
            self.error(ctx, f"No se puede asignar {self.symtab._tname(init_t)} a variable {name}: {self.symtab._tname(vtype)}.")
        if not self.symtab.define_var(VariableSymbol(name, vtype, is_const=False)):
            self.error(ctx, f"Variable '{name}' ya está definida en este ámbito.")
        return None

    def visitConstantDeclaration(self, ctx):
        name = ctx.Identifier().getText()
        vtype = TypeKind.ERROR
        if ctx.typeAnnotation():
            vtype = self.type_from_type(self._get_type_node(ctx.typeAnnotation()))
        rhs_t = self.visit(ctx.expression())
        if vtype == TypeKind.ERROR:
            vtype = rhs_t
        if not self.is_assignable(vtype, rhs_t):
            self.error(ctx, f"No se puede inicializar const {name}: se esperaba {self.symtab._tname(vtype)}, llegó {self.symtab._tname(rhs_t)}.")
        if not self.symtab.define_var(VariableSymbol(name, vtype, is_const=True)):
            self.error(ctx, f"Constante '{name}' ya está definida en este ámbito.")
        return None

    # assignment (statement rule):
    #   Identifier '=' expression ';'
    #   | expression '.' Identifier '=' expression ';'
    def visitAssignment(self, ctx):
        if ctx.Identifier():
            # asignación simple
            name = ctx.Identifier().getText()
            var = self.symtab.resolve_var(name)
            if not var:
                self.error(ctx, f"Variable '{name}' no existe.")
                return TypeKind.ERROR
            if var.is_const:
                self.error(ctx, f"No se puede asignar a constante '{name}'.")
                return var.type
            rhs_t = self.visit(ctx.expression(0))
            if not self.is_assignable(var.type, rhs_t):
                self.error(ctx, f"Tipos incompatibles en asignación: {self.symtab._tname(var.type)} = {self.symtab._tname(rhs_t)}.")
            return var.type
        else:
            # property assignment: expression '.' Identifier '=' expression ';'
            recv_t = self.visit(ctx.expression(0))
            if not is_object(recv_t):
                self.error(ctx, "Asignación a propiedad requiere objeto a la izquierda del '.'.")
                return TypeKind.ERROR
            csym = self.symtab.resolve_class(recv_t.class_name)
            if not csym:
                self.error(ctx, f"Clase '{recv_t.class_name}' no está declarada.")
                return TypeKind.ERROR
            mname = ctx.Identifier(0).getText()
            member, owner = self._resolve_member(csym, mname)
            if not member:
                self.error(ctx, f"'{recv_t.class_name}' no tiene miembro '{mname}'.")
                return TypeKind.ERROR
            if member.is_method:
                self.error(ctx, f"No se puede asignar a método '{mname}'.")
                return TypeKind.ERROR
            rhs_t = self.visit(ctx.expression(1))
            rhs_t = self._type_of_simple_identifier(ctx.expression(1), rhs_t)
            if not self.is_assignable(member.type, rhs_t):
                self.error(ctx, f"Tipos incompatibles al asignar {mname}: {self.symtab._tname(member.type)} = {self.symtab._tname(rhs_t)}.")
            return member.type


    def visitExpressionStatement(self, ctx):
        self.visit(ctx.expression())
        return None

    def visitPrintStatement(self, ctx):
        self.visit(ctx.expression())
        return None

    # if/while/do-while/for/foreach
    def visitIfStatement(self, ctx):
        cond_t = self.visit(ctx.expression())
        self.expect_boolean(ctx, cond_t, "if")
        blocks = ctx.block()
        if len(blocks) >= 1: self.visit(blocks[0])
        if len(blocks) == 2: self.visit(blocks[1])
        return None

    def visitWhileStatement(self, ctx):
        cond_t = self.visit(ctx.expression())
        self.expect_boolean(ctx, cond_t, "while")
        self.loop_depth += 1
        self.visit(ctx.block())
        self.loop_depth -= 1
        return None

    def visitDoWhileStatement(self, ctx):
        self.loop_depth += 1
        self.visit(ctx.block())
        self.loop_depth -= 1
        cond_t = self.visit(ctx.expression())
        self.expect_boolean(ctx, cond_t, "do-while")
        return None

    def visitForStatement(self, ctx):
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())
        # cond
        if ctx.expression(0):
            cond_t = self.visit(ctx.expression(0))
            self.expect_boolean(ctx, cond_t, "for")
        # update
        if ctx.expression(1):
            self.visit(ctx.expression(1))
        self.loop_depth += 1
        self.visit(ctx.block())
        self.loop_depth -= 1
        return None

    def visitForeachStatement(self, ctx):
        coll_t = self.visit(ctx.expression())
        elem_t = self.array_element_type_of(coll_t)
        if elem_t is None:
            self.error(ctx, "foreach requiere un arreglo como colección.")
            elem_t = TypeKind.ERROR
        self.symtab.push_scope()
        it_name = ctx.Identifier().getText()
        self.symtab.define_var(VariableSymbol(it_name, elem_t, is_const=False))
        self.loop_depth += 1
        self.visit(ctx.block())
        self.loop_depth -= 1
        self.symtab.pop_scope()
        return None

    def visitBreakStatement(self, ctx):
        if self.loop_depth == 0:
            self.error(ctx, "break solo puede usarse dentro de un bucle.")
        return None

    def visitContinueStatement(self, ctx):
        if self.loop_depth == 0:
            self.error(ctx, "continue solo puede usarse dentro de un bucle.")
        return None

    def visitReturnStatement(self, ctx):
        if self.current_function is None:
            self.error(ctx, "return no puede usarse fuera de una función.")
            return None
        expr_ctx = ctx.expression()
        if self.current_function.return_type == TypeKind.VOID:
            if expr_ctx is not None:
                self.error(ctx, "Esta función es void: 'return' no debe tener expresión.")
        else:
            if expr_ctx is None:
                self.error(ctx, f"Falta expresión en return; se esperaba {self.symtab._tname(self.current_function.return_type)}.")
            else:
                et = self.visit(expr_ctx)
                if not self.is_assignable(self.current_function.return_type, et):
                    self.error(ctx, f"Tipo de retorno incompatible: se esperaba {self.symtab._tname(self.current_function.return_type)}, se obtuvo {self.symtab._tname(et)}.")
        self.current_function_has_return = True
        return None

    # switch/try-catch: validación mínima (visitar hijos)
    def visitSwitchStatement(self, ctx):
        self.visit(ctx.expression())
        for c in ctx.switchCase():
            for st in c.statement():
                self.visit(st)
        if ctx.defaultCase():
            for st in ctx.defaultCase().statement():
                self.visit(st)
        return None

    def visitTryCatchStatement(self, ctx):
        self.visit(ctx.block(0))
        self.symtab.push_scope()
        catch_id = ctx.Identifier().getText()
        self.symtab.define_var(VariableSymbol(catch_id, TypeKind.STRING, is_const=False))
        self.visit(ctx.block(1))
        self.symtab.pop_scope()
        return None

    # ========================
    # Funciones
    # ========================
    def visitFunctionDeclaration(self, ctx):
        name = ctx.Identifier().getText()
        params: List[Tuple[str, Any]] = []
        if ctx.parameters():
            for p in ctx.parameters().parameter():
                pname = p.Identifier().getText()
                ptype = self.type_from_type(self._get_type_node(p)) if (hasattr(p, "type") or hasattr(p, "type_")) else TypeKind.ERROR
                params.append((pname, ptype))
        ret_t = self.type_from_type(self._get_type_node(ctx)) if (hasattr(ctx, "type") or hasattr(ctx, "type_")) else TypeKind.VOID

        fsym = FunctionSymbol(name, params, ret_t)
        if not self.symtab.define_func(fsym):
            self.error(ctx, f"Función '{name}' ya está declarada.")

        outer_fn, outer_has = self.current_function, self.current_function_has_return
        self.current_function, self.current_function_has_return = fsym, False

        self.symtab.push_scope()
        for pname, ptype in params:
            if not self.symtab.define_var(VariableSymbol(pname, ptype, is_const=False)):
                self.error(ctx, f"Parámetro '{pname}' duplicado.")
        self.visit(ctx.block())
        self.symtab.pop_scope()

        if fsym.return_type != TypeKind.VOID and not self.current_function_has_return:
            self.error(ctx, f"La función '{name}' debe retornar {self.symtab._tname(ret_t)} en todos los caminos.")
        self.current_function, self.current_function_has_return = outer_fn, outer_has
        return None


    # ========================
    # Clases / miembros / métodos / ctor / herencia
    # ========================
    def visitClassDeclaration(self, ctx):
        cname = ctx.Identifier(0).getText()
        base_name = ctx.Identifier(1).getText() if ctx.Identifier().__len__() == 2 else None

        csym = ClassSymbol(name=cname, members={}, _base_name=base_name)
        if not self.symtab.define_class(csym):
            self.error(ctx, f"Clase '{cname}' ya está declarada.")
            return None

        prev_class = self.current_class
        self.current_class = csym
        self.symtab.push_scope()

        for m in ctx.classMember():
            self.visit(m)

        self.symtab.pop_scope()
        self.current_class = prev_class
        return None

    def visitClassMember(self, ctx):
        if ctx.functionDeclaration():
            fd = ctx.functionDeclaration()
            fname = fd.Identifier().getText()
            if fname == "constructor":
                self._declare_ctor(fd)
            else:
                self._declare_method(fd)
        elif ctx.variableDeclaration():
            vd = ctx.variableDeclaration()
            name = vd.Identifier().getText()
            vtype = TypeKind.ERROR
            if vd.typeAnnotation():
                vtype = self.type_from_type(self._get_type_node(vd.typeAnnotation()))
            if name in self.current_class.members:
                self.error(ctx, f"Miembro duplicado '{name}'.")
            else:
                self.current_class.members[name] = ClassMember(name=name, type=vtype, is_method=False)
        elif ctx.constantDeclaration():
            cd = ctx.constantDeclaration()
            name = cd.Identifier().getText()
            vtype = TypeKind.ERROR
            if cd.typeAnnotation():
                vtype = self.type_from_type(self._get_type_node(cd.typeAnnotation()))
            if name in self.current_class.members:
                self.error(ctx, f"Miembro duplicado '{name}'.")
            else:
                self.current_class.members[name] = ClassMember(name=name, type=vtype, is_method=False)
        return None

    def _declare_method(self, fd):
        mname = fd.Identifier().getText()
        params: List[Tuple[str, Any]] = []
        if fd.parameters():
            for p in fd.parameters().parameter():
                pname = p.Identifier().getText()
                ptype = self.type_from_type(self._get_type_node(p)) if (hasattr(p, "type") or hasattr(p, "type_")) else TypeKind.ERROR
                params.append((pname, ptype))
        ret_t = self.type_from_type(self._get_type_node(fd)) if (hasattr(fd, "type") or hasattr(fd, "type_")) else TypeKind.VOID

        # registra o sobrescribe (permitimos override simple)
        self.current_class.members[mname] = ClassMember(
            name=mname, type=TypeKind.VOID, is_method=True, params=params, return_type=ret_t
        )

        outer_fn, outer_has = self.current_function, self.current_function_has_return
        self.current_function, self.current_function_has_return = \
            FunctionSymbol(f"{self.current_class.name}.{mname}", params, ret_t), False

        self.symtab.push_scope()
        self.symtab.define_var(VariableSymbol("this", ObjectType(self.current_class.name), is_const=True))
        for pname, ptype in params:
            self.symtab.define_var(VariableSymbol(pname, ptype, is_const=False))
        self.visit(fd.block())
        self.symtab.pop_scope()

        if ret_t != TypeKind.VOID and not self.current_function_has_return:
            self.error(fd, f"El método '{mname}' debe retornar {self.symtab._tname(ret_t)} en todos los caminos.")

        self.current_function, self.current_function_has_return = outer_fn, outer_has

    def _declare_ctor(self, fd):
        params: List[Tuple[str, Any]] = []
        if fd.parameters():
            for p in fd.parameters().parameter():
                pname = p.Identifier().getText()
                ptype = self.type_from_type(self._get_type_node(p)) if (hasattr(p, "type") or hasattr(p, "type_")) else TypeKind.ERROR
                params.append((pname, ptype))
        if "__ctor__" in self.current_class.members:
            self.error(fd, f"La clase '{self.current_class.name}' ya tiene constructor.")
        else:
            self.current_class.members["__ctor__"] = ClassMember(
                name="__ctor__", type=TypeKind.VOID, is_method=True,
                params=params, return_type=TypeKind.VOID
            )
        self.in_constructor = True
        self.symtab.push_scope()
        self.symtab.define_var(VariableSymbol("this", ObjectType(self.current_class.name), is_const=True))
        for pname, ptype in params:
            self.symtab.define_var(VariableSymbol(pname, ptype, is_const=False))
        self.visit(fd.block())
        self.symtab.pop_scope()
        self.in_constructor = False


    def _resolve_member(self, class_sym: ClassSymbol, name: str):
        if name in class_sym.members:
            return class_sym.members[name], class_sym
        # subir por la cadena de herencia
        if class_sym._base_name:
            base = self.symtab.resolve_class(class_sym._base_name)
            if base:
                return self._resolve_member(base, name)
        return None, None

    # ========================
    # Expresiones
    # ========================

    # expression: assignmentExpr;
    def visitExpression(self, ctx):
        return self.visit(ctx.assignmentExpr())

    # assignmentExpr:
    #   lhs=leftHandSide '=' assignmentExpr            # AssignExpr
    # | lhs=leftHandSide '.' Identifier '=' assignmentExpr # PropertyAssignExpr
    # | conditionalExpr                                # ExprNoAssign
    def visitAssignExpr(self, ctx):
        _ = self.visit(ctx.leftHandSide())  # resuelve y anota _lhs_var si aplica
        var = getattr(ctx.leftHandSide(), "_lhs_var", None)
        rhs_t = self.visit(ctx.assignmentExpr())
        if var is None:
            self.error(ctx, "Lado izquierdo de '=' no es una variable asignable.")
            return TypeKind.ERROR
        if var.is_const:
            self.error(ctx, f"No se puede asignar a constante '{var.name}'.")
            return var.type
        if not self.is_assignable(var.type, rhs_t):
            self.error(ctx, f"Tipos incompatibles en asignación: {self.symtab._tname(var.type)} = {self.symtab._tname(rhs_t)}.")
        return var.type


    def visitPropertyAssignExpr(self, ctx):
        base_t = self.visit(ctx.leftHandSide())
        if not is_object(base_t):
            self.error(ctx, "Asignación a propiedad requiere objeto a la izquierda del '.'.")
            return TypeKind.ERROR
        csym = self.symtab.resolve_class(base_t.class_name)
        if not csym:
            self.error(ctx, f"Clase '{base_t.class_name}' no está declarada.")
            return TypeKind.ERROR
        mname = ctx.Identifier().getText()
        member, owner = self._resolve_member(csym, mname)
        if not member:
            self.error(ctx, f"'{base_t.class_name}' no tiene miembro '{mname}'.")
            return TypeKind.ERROR
        if member.is_method:
            self.error(ctx, f"No se puede asignar a método '{mname}'.")
            return TypeKind.ERROR
        rhs_t = self.visit(ctx.assignmentExpr())
        rhs_t = self._type_of_simple_identifier(ctx.assignmentExpr(), rhs_t)
        if not self.is_assignable(member.type, rhs_t):
            self.error(ctx, f"Tipos incompatibles al asignar {mname}: {self.symtab._tname(member.type)} = {self.symtab._tname(rhs_t)}.")
        return member.type

    def visitExprNoAssign(self, ctx):
        return self.visit(ctx.conditionalExpr())

    # conditionalExpr : logicalOrExpr ('?' expression ':' expression)? # TernaryExpr
    def visitTernaryExpr(self, ctx):
        cond_t = self.visit(ctx.logicalOrExpr())
        if ctx.expression().__len__() == 0:
            return cond_t
        self.expect_boolean(ctx, cond_t, "?:")
        t_t = self.visit(ctx.expression(0))
        f_t = self.visit(ctx.expression(1))
        # tipo resultante simplificado: si iguales -> común; si numéricos -> común numérico; si uno es string -> string
        if same_type(t_t, f_t):
            return t_t
        if TypeKind.is_numeric(t_t) and TypeKind.is_numeric(f_t):
            return TypeKind.common_numeric(t_t, f_t)
        if TypeKind.STRING in (t_t, f_t):
            return TypeKind.STRING
        return TypeKind.ERROR

    # Passthroughs
    def visitLogicalOrPassthrough(self, ctx):  return self.visit(ctx.logicalAndExpr())
    def visitLogicalAndPassthrough(self, ctx): return self.visit(ctx.equalityExpr())
    def visitEqualityPassthrough(self, ctx):   return self.visit(ctx.relationalExpr())
    def visitRelationalPassthrough(self, ctx): return self.visit(ctx.additiveExpr())
    def visitAdditivePassthrough(self, ctx):   return self.visit(ctx.multiplicativeExpr())
    def visitMultiplicativePassthrough(self, ctx): return self.visit(ctx.unaryExpr())
    def visitUnaryPassthrough(self, ctx):      return self.visit(ctx.primaryExpr())

    # Operadores
    def visitLogicalOrOp(self, ctx):
        lt = self.visit(ctx.logicalOrExpr())
        rt = self.visit(ctx.logicalAndExpr())
        if lt != TypeKind.BOOLEAN or rt != TypeKind.BOOLEAN:
            self.error(ctx, f"Operación lógica requiere booleanos, no {self.symtab._tname(lt)} y {self.symtab._tname(rt)}.")
            return TypeKind.ERROR
        return TypeKind.BOOLEAN

    def visitLogicalAndOp(self, ctx):
        lt = self.visit(ctx.logicalAndExpr())
        rt = self.visit(ctx.equalityExpr())
        if lt != TypeKind.BOOLEAN or rt != TypeKind.BOOLEAN:
            self.error(ctx, f"Operación lógica requiere booleanos, no {self.symtab._tname(lt)} y {self.symtab._tname(rt)}.")
            return TypeKind.ERROR
        return TypeKind.BOOLEAN

    def visitEqualityOp(self, ctx):
        lt = self.visit(ctx.equalityExpr())
        rt = self.visit(ctx.relationalExpr())
        return TypeKind.BOOLEAN if same_type(lt, rt) or TypeKind.STRING in (lt, rt) else TypeKind.BOOLEAN

    def visitRelationalOp(self, ctx):
        lt = self.visit(ctx.relationalExpr())
        rt = self.visit(ctx.additiveExpr())
        if not (TypeKind.is_numeric(lt) and TypeKind.is_numeric(rt)):
            self.error(ctx, f"Comparación relacional requiere numéricos, no {self.symtab._tname(lt)} y {self.symtab._tname(rt)}.")
        return TypeKind.BOOLEAN

    def visitAdditiveOp(self, ctx):
        lt = self.visit(ctx.additiveExpr())
        rt = self.visit(ctx.multiplicativeExpr())
        op = ctx.op.text
        if op == '+' and (lt == TypeKind.STRING or rt == TypeKind.STRING):
            return TypeKind.STRING
        if not (TypeKind.is_numeric(lt) and TypeKind.is_numeric(rt)):
            self.error(ctx, f"Operación aritmética requiere numéricos, no {self.symtab._tname(lt)} y {self.symtab._tname(rt)}.")
            return TypeKind.ERROR
        return TypeKind.common_numeric(lt, rt)

    def visitMultiplicativeOp(self, ctx):
        lt = self.visit(ctx.multiplicativeExpr())
        rt = self.visit(ctx.unaryExpr())
        if not (TypeKind.is_numeric(lt) and TypeKind.is_numeric(rt)):
            self.error(ctx, f"Operación aritmética requiere numéricos, no {self.symtab._tname(lt)} y {self.symtab._tname(rt)}.")
            return TypeKind.ERROR
        return TypeKind.common_numeric(lt, rt)

    def visitUnaryOp(self, ctx):
        t = self.visit(ctx.unaryExpr())
        if ctx.op.text == '!':
            if t != TypeKind.BOOLEAN:
                self.error(ctx, f"'!' requiere booleano, no {self.symtab._tname(t)}.")
                return TypeKind.ERROR
            return TypeKind.BOOLEAN
        # '-' unario
        if not TypeKind.is_numeric(t):
            self.error(ctx, f"Negación numérica requiere numérico, no {self.symtab._tname(t)}.")
            return TypeKind.ERROR
        return t

    # primaryExpr
    def visitLiteralPrimary(self, ctx):
        return self.visit(ctx.literalExpr())

    def visitLeftHandSidePrimary(self, ctx):
        base_t = self.visit(ctx.leftHandSide())
        return base_t

    def visitParenthesizedExpr(self, ctx):
        return self.visit(ctx.expression())

    # literalExpr
    def visitLiteralExpr(self, ctx):
        if ctx.arrayLiteral():
            return self.visit(ctx.arrayLiteral())
        if ctx.getText() == "null":
            return TypeKind.NULL
        if ctx.getText() == "true" or ctx.getText() == "false":
            return TypeKind.BOOLEAN
        # Literal → IntegerLiteral | StringLiteral
        lit = ctx.Literal()
        if lit is not None:
            text = lit.getText()
            if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
                return TypeKind.STRING
            return TypeKind.INTEGER
        return TypeKind.ERROR

    # leftHandSide: primaryAtom (suffixOp)*
    def visitLeftHandSide(self, ctx):
        cur_t = self.visit(ctx.primaryAtom())

        # si el primary era un identificador variable, adjunta al LHS
        prim = ctx.primaryAtom()
        if hasattr(prim, "_resolved_var"):
            setattr(ctx, "_lhs_var", getattr(prim, "_resolved_var"))

        for sfx in ctx.suffixOp():
            head = sfx.getChild(0).getText()
            if head == '.':  # PropertyAccessExpr
                setattr(sfx, "_lhs_type", cur_t)
                cur_t = self.visit(sfx)
                # si accedimos a un campo (no método), perdería _lhs_var (ya no es asignable directo)
                if hasattr(ctx, "_lhs_var"):
                    delattr(ctx, "_lhs_var")
            elif head == '[':  # IndexExpr
                setattr(sfx, "_lhs_type", cur_t)
                cur_t = self.visit(sfx)
                if hasattr(ctx, "_lhs_var"):
                    delattr(ctx, "_lhs_var")
            else:  # CallExpr
                # llamada: ¿función global guardada en primary?
                if hasattr(prim, "_as_func"):
                    setattr(sfx, "_callee_info", prim._as_func)
                elif isinstance(cur_t, ClassMember) and cur_t.is_method:
                    setattr(sfx, "_callee_info", ("method", None, cur_t))
                else:
                    setattr(sfx, "_callee_info", None)
                cur_t = self.visit(sfx)
                if hasattr(ctx, "_lhs_var"):
                    delattr(ctx, "_lhs_var")
        return cur_t

    def visitIdentifierExpr(self, ctx):
        name = ctx.Identifier().getText()
        var = self.symtab.resolve_var(name)
        if var:
            # marca SOLO en este nodo; leftHandSide lo leerá
            setattr(ctx, "_resolved_var", var)
            return var.type
        # ¿función global?
        f = self.symtab.resolve_func(name)
        if f:
            setattr(ctx, "_as_func", f)
            return TypeKind.ERROR
        # puede ser nombre de clase (solo con 'new'); como expresión sola no es válido
        return TypeKind.ERROR

    def visitNewExpr(self, ctx):
        cname = ctx.Identifier().getText()
        csym = self.symtab.resolve_class(cname)
        if not csym:
            self.error(ctx, f"Clase '{cname}' no existe.")
            return TypeKind.ERROR

        arg_types = []
        if ctx.arguments():
            for e in ctx.arguments().expression():
                arg_types.append(self.visit(e))

        # 1) ctor local
        ctor = csym.members.get("__ctor__")
        if ctor:
            expected = ctor.params or []
            self._check_args(ctx, expected, arg_types, f"{cname}.constructor")
            return ObjectType(cname)

        # 2) si no hay, busca en la base
        base_name = csym._base_name
        while ctor is None and base_name:
            base_cls = self.symtab.resolve_class(base_name)
            if base_cls:
                ctor = base_cls.members.get("__ctor__")
                if ctor:
                    expected = ctor.params or []
                    self._check_args(ctx, expected, arg_types, f"{base_cls.name}.constructor")
                    break
                base_name = base_cls._base_name
            else:
                break

        if ctor is None and arg_types:
            self.error(ctx, f"'{cname}' no tiene constructor que acepte argumentos.")
        return ObjectType(cname)


    def visitThisExpr(self, ctx):
        if self.current_class is None:
            self.error(ctx, "Uso de 'this' fuera de método/constructor.")
            return TypeKind.ERROR
        return ObjectType(self.current_class.name)

    # suffixOp:
    #   '(' arguments? ')'                        # CallExpr
    # | '[' expression ']'                        # IndexExpr
    # | '.' Identifier                            # PropertyAccessExpr
    def visitCallExpr(self, ctx):
        args_types: List[Any] = []
        if ctx.arguments():
            for e in ctx.arguments().expression():
                args_types.append(self.visit(e))

        callee_info = getattr(ctx, "_callee_info", None)

        if isinstance(callee_info, FunctionSymbol):
            fsym = callee_info
            self._check_args(ctx, fsym.params, args_types, fsym.name)
            return fsym.return_type

        if isinstance(callee_info, tuple) and callee_info and callee_info[0] == "method":
            (_tag, class_sym, member) = callee_info
            self._check_args(ctx, member.params or [], args_types, f"{(class_sym.name if class_sym else '?')}.{member.name}")
            return member.return_type or TypeKind.VOID

        # También puede venir desde PropertyAccessExpr que guardó _member_handle
        parent = ctx.parentCtx
        handle = None
        for i in range(parent.getChildCount()):
            ch = parent.getChild(i)
            h = getattr(ch, "_member_handle", None)
            if h: handle = h
        if handle:
            (_tag, class_sym, member) = handle
            self._check_args(ctx, member.params or [], args_types, f"{class_sym.name}.{member.name}")
            return member.return_type or TypeKind.VOID

        self.error(ctx, "Llamada sin callee resoluble.")
        return TypeKind.ERROR

    def visitIndexExpr(self, ctx):
        base_t = getattr(ctx, "_lhs_type", None)
        idx_t = self.visit(ctx.expression())
        if idx_t != TypeKind.INTEGER:
            self.error(ctx, "El índice de un arreglo debe ser integer.")
        et = elem_type_of(base_t)
        if et is None:
            self.error(ctx, "Indexación sobre un no-arreglo.")
            return TypeKind.ERROR
        return et

    def visitPropertyAccessExpr(self, ctx):
        lhs_t = getattr(ctx, "_lhs_type", None)
        if not is_object(lhs_t):
            self.error(ctx, "Acceso a miembro sobre algo que no es objeto.")
            return TypeKind.ERROR
        csym = self.symtab.resolve_class(lhs_t.class_name)
        if not csym:
            self.error(ctx, f"Clase '{lhs_t.class_name}' no está declarada.")
            return TypeKind.ERROR
        mname = ctx.Identifier().getText()
        member, owner = self._resolve_member(csym, mname)
        if not member:
            self.error(ctx, f"'{lhs_t.class_name}' no tiene miembro '{mname}'.")
            return TypeKind.ERROR
        if member.is_method:
            # guardamos manejador para que el siguiente CallExpr lo resuelva
            setattr(ctx, "_member_handle", ("method", owner, member))
            return member  # placeholder para threading
        return member.type

    # arguments: expression (',' expression)*
    # (se maneja dentro de visitCallExpr)

    # arrayLiteral: '[' (expression (',' expression)*)? ']'
    def visitArrayLiteral(self, ctx):
        elems = [self.visit(e) for e in ctx.expression()]
        if not elems:
            return array_of(TypeKind.ERROR)  # arreglo vacío: tipo desconocido
        et = elems[0]
        for t in elems[1:]:
            if not same_type(t, et):
                self.error(ctx, "Todos los elementos del arreglo deben ser del mismo tipo.")
                return array_of(TypeKind.ERROR)
        return array_of(et)

    # ========================
    # Tipos y asignabilidad
    # ========================
    def array_element_type_of(self, t):
        return elem_type_of(t)

    def type_from_type(self, tctx) -> Any:
        if tctx is None:
            return TypeKind.ERROR
        base_ctx = tctx.baseType()
        base = base_ctx.getText() if base_ctx else ""
        bl = base.lower()
        if bl == 'integer': cur: Any = TypeKind.INTEGER
        elif bl == 'boolean': cur = TypeKind.BOOLEAN
        elif bl == 'string': cur = TypeKind.STRING
        else:
            # Identificador de clase
            cls = self.symtab.resolve_class(base)
            cur = ObjectType(base) if cls else TypeKind.ERROR
        # contar '[]'
        brackets = 0
        for i in range(tctx.getChildCount()):
            if tctx.getChild(i).getText() == '[':
                brackets += 1
        for _ in range(brackets):
            cur = array_of(cur)
        return cur


    def is_assignable(self, target: Any, source: Any) -> bool:
        # arrays
        if is_array(target) and is_array(source):
            return self.is_assignable(target.elem, source.elem)
        if is_array(target) != is_array(source):
            return False
        # objetos
        if is_object(target) and is_object(source):
            # compatibilidad nominal simple: mismo nombre de clase o derivada
            return self._is_class_assignable(target.class_name, source.class_name)
        if is_object(target) or is_object(source):
            return False
        # primitivos
        if target == source:
            return True
        if target == TypeKind.FLOAT and source == TypeKind.INTEGER:
            return True
        if source == TypeKind.NULL and target in (TypeKind.STRING,):
            return True
        return False

    def _is_class_assignable(self, target_cls: str, source_cls: str) -> bool:
        if target_cls == source_cls:
            return True
        # permitir asignación si source es subclase de target (subtyping)
        sc = self.symtab.resolve_class(source_cls)
        while sc and sc._base_name:
            if sc._base_name == target_cls:
                return True
            sc = self.symtab.resolve_class(sc._base_name)
        return False

    # ========================
    # Visit fallback
    # ========================
    def visit(self, node):
        if node is None:
            return None
        mname = f"visit{type(node).__name__}"
        m = getattr(self, mname, None)
        if callable(m):
            return m(node)
        if hasattr(node, "accept"):
            return node.accept(self)
        return self.visitChildren(node)

    # ========================
    # Helpers de argumentos
    # ========================
    def _check_args(self, ctx, expected_params, args_types, fname):
        if len(args_types) != len(expected_params):
            self.error(ctx, f"Número de argumentos incorrecto en '{fname}': se esperaban {len(expected_params)}, llegaron {len(args_types)}.")
            return
        for i, ((_, pt), at) in enumerate(zip(expected_params, args_types), 1):
            if not self.is_assignable(pt, at):
                self.error(ctx, f"Argumento {i} incompatible en '{fname}': se esperaba {self.symtab._tname(pt)}, llegó {self.symtab._tname(at)}.")