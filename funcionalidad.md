# Analizador Semántico de Compiscript — `semantic.py`

Este README describe **cómo funciona el análisis semántico** del proyecto y, en particular, las responsabilidades y estructuras clave definidas en `semantic.py`.

> Si buscas la guía general del repo (estructura, Docker, tests), consúltala en el `README.md` principal. Aquí nos enfocamos en el **núcleo semántico**.

---

## Tabla de contenidos
- [Visión general](#visión-general)
- [Sistema de tipos](#sistema-de-tipos)
- [Símbolos y tabla de símbolos](#símbolos-y-tabla-de-símbolos)
- [Visitor semántico](#visitor-semántico)
  - [Ámbitos y bloques](#ámbitos-y-bloques)
  - [Variables y constantes](#variables-y-constantes)
  - [Asignaciones y compatibilidad de tipos](#asignaciones-y-compatibilidad-de-tipos)
  - [Control de flujo](#control-de-flujo)
  - [Funciones](#funciones)
  - [Clases, herencia y miembros](#clases-herencia-y-miembros)
  - [Expresiones](#expresiones)
- [Reglas de asignabilidad (`is_assignable`)](#reglas-de-asignabilidad-is_assignable)
- [Reporte de errores](#reporte-de-errores)
- [Depuración y consejos](#depuración-y-consejos)
- [Ejecución rápida](#ejecución-rápida)

---

## Visión general

`semantic.py` implementa un **visitor** que recorre el árbol de sintaxis generado por ANTLR y aplica reglas semánticas del lenguaje **Compiscript**. Las tareas principales son:

- Construir y mantener una **tabla de símbolos** con **ámbitos** (scopes) anidados.
- **Declarar** y **resolver** variables, funciones y clases/miembros.
- Comprobar **compatibilidad de tipos** en expresiones, asignaciones y llamadas.
- Validar **control de flujo** (e.g., condiciones booleanas, `break/continue`, returns).
- Chequear **clases**, **constructores**, **métodos** y **herencia**.
- Emitir **errores semánticos** con línea/columna y mensaje claro.

---

## Sistema de tipos

Tipos primitivos y auxiliares:

- `TypeKind`: `INTEGER`, `FLOAT`, `BOOLEAN`, `STRING`, `VOID`, `NULL`, `ERROR`.
  - Helpers: `is_numeric(t)`, `common_numeric(t1, t2)`.
- `ArrayType(elem)`: represente arreglos de un tipo base (posiblemente anidado).
- `ObjectType(class_name)`: representa instancias de clases de usuario.

Funciones de utilidad: `is_array(t)`, `array_of(elem)`, `elem_type_of(t)`, `is_object(t)`, `same_type(a, b)`.

---

## Símbolos y tabla de símbolos

Estructuras para representar entidades del programa:

- `VariableSymbol(name, type, is_const)`
- `FunctionSymbol(name, params, return_type)`
- `ClassMember(name, type, is_method, params, return_type)`
- `ClassSymbol(name, members, _base_name)`

**Tabla de símbolos (`SymbolTable`)**:

- Ámbitos con **`push_scope()`** / **`pop_scope()`** y **`current_scope()`**.
- Declaración y resolución de **variables**, **funciones** y **clases**:
  - `define_var`, `resolve_var`
  - `define_func`, `resolve_func`
  - `define_class`, `resolve_class`
- Exportación para depuración: `export_as_lines()` (imprime variables, funciones y clases por ámbito).

---

## Visitor semántico

La clase `SemanticVisitor` coordina el análisis. Campos principales:

- `issues: List[SemanticIssue]`: errores recolectados (línea, columna, mensaje).
- `symtab: SymbolTable`: tabla de símbolos global + pila de ámbitos.
- `loop_depth: int`: valida `break/continue` dentro de bucles.
- `current_function`, `current_function_has_return`: validación de returns.
- `current_class`, `in_constructor`: contexto de clase/ctor para `this` y miembros.

### Ámbitos y bloques

- `visitProgram` y `visitBlock` recorren y crean **ámbitos anidados**.
- Cada bloque (`{ ... }`) hace `push_scope()` al entrar y `pop_scope()` al salir.

### Variables y constantes

- `visitVariableDeclaration`
  - Obtiene tipo declarado (o lo infiere del inicializador si no se especifica).
  - Verifica **redeclaración** en el mismo ámbito.
  - Comprueba que el inicializador sea **asignable** al tipo.
- `visitConstantDeclaration`
  - Igual que variable, pero exige **inicialización compatible** para constantes.

### Asignaciones y compatibilidad de tipos

- `visitAssignment` / `visitAssignExpr` (simple) y `visitPropertyAssignExpr` (a campos):
  - Resuelve la variable/miembro destino y evalúa el tipo del RHS.
  - Llama a `is_assignable(target, source)`.
  - En caso de incompatibilidad, emite: `Tipos incompatibles en asignación: TARGET = SOURCE`.

### Control de flujo

- `visitIfStatement`, `visitWhileStatement`, `visitDoWhileStatement`, `visitForStatement`:
  - **Condiciones deben ser booleanas**.
  - `loop_depth` asegura que `break/continue` solo aparezcan en bucles.
- `visitReturnStatement`:
  - En funciones/métodos **no-void**, obliga a retorno de tipo compatible en todos los caminos.

### Funciones

- `visitFunctionDeclaration`:
  - Registra firma en `SymbolTable` y declara parámetros en un nuevo ámbito.
  - Verifica **número/tipo de `return`** y **parámetros duplicados**.
- Llamadas: `visitCallExpr` usa `_check_args` para validar **conteo y tipos**.

### Clases, herencia y miembros

- `visitClassDeclaration` y `visitClassMember`:
  - Declara clase, opcionalmente con **base** (herencia).
  - Registra **campos** y **métodos** (incl. `constructor` → `__ctor__`).
  - Detecta **miembros duplicados**.
- `_resolve_member`:
  - Resuelve un miembro buscando en la clase y subiendo por la **cadena de herencia**.
- Constructores: `_declare_ctor` define `this` y valida el cuerpo.

### Expresiones

- Literales: enteros, strings, `true/false`, `null`, arreglos con elementos homogéneos.
- Aritméticas: `+ - * /` **requieren numéricos**; `common_numeric` resuelve `INTEGER`/`FLOAT`.
- Lógicas: `&&`, `||`, `!` **requieren booleanos**.
- Relacionales: requieren **operandos numéricos**.
- **Concatenación**: si en `+` cualquiera **se comporta como string**, resultado es `STRING`.
  - `_behaves_as_string(t)`: `t == STRING` o `t` es `ObjectType` con `toString(): string`.
- Accesos: `obj.prop` y `obj.metodo()`, con validación de existencia y tipos.
- Indexación: `arr[i]` solo con `i: INTEGER` y `arr` de tipo arreglo.

---

## Reglas de asignabilidad (`is_assignable`)

Resumen de casos **válidos** (además de igualdad exacta de tipos):

- `FLOAT ← INTEGER`
- `STRING ← NULL`
- **`STRING ← Objeto`**  
  - Permitido por decisión de lenguaje para soportar **stringificación implícita**.
  - Alternativamente, puede condicionarse a que la clase tenga `toString(): string`.
- **Objetos con herencia**: `TargetClass ← SourceClass` si `SourceClass` es igual a `TargetClass` o una **subclase**.

Casos **inválidos** típicos:

- Mezcla de arreglo/no-arreglo.
- Conversión entre `ObjectType` y primitivos (salvo la regla `STRING ← Objeto` anterior).
- Operaciones aritméticas con no-numéricos.

---

## Reporte de errores

Cada error se agrega a `issues` como `SemanticIssue(line, column, message)`. Ejemplos habituales:

- Variable no declarada / redeclaración en mismo ámbito.
- Tipos incompatibles en asignación o en argumentos de función/método.
- Falta de `return` en funciones/métodos no-void.
- Acceso a miembros inexistentes.
- Uso indebido de `break/continue`.

---

## Depuración y consejos

- Usa `SymbolTable.export_as_lines()` para inspeccionar **qué se declaró** y **dónde**.
- Para verificar la **ruta del archivo** que realmente carga el visitor, temporalmente:
  ```python
  import inspect; print("USANDO:", inspect.getsourcefile(SemanticVisitor))
  ```
- Asegúrate de reconstruir la imagen/volumen de Docker si cambias `semantic.py`.

---

## Ejecución rápida

```bash
# desde la raíz del proyecto
python program/Driver.py program/program.cps
```

- Sin salida → **análisis correcto**.
- Con mensajes → revisa línea, columna y el tipo de error reportado.

---

**Notas**

- La regla `STRING ← Objeto` puede ajustarse a un modo **estricto** exigiendo `toString(): string` en la clase, usando `_has_to_string_method(cls_name)` y `_behaves_as_string(t)`.
- La concatenación con `+` ya contempla el caso de objetos “stringificables”, manteniendo coherencia con la asignación.
