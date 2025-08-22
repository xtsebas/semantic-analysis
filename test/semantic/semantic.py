import pytest
from antlr4 import InputStream, CommonTokenStream
from program.CompiscriptLexer import CompiscriptLexer
from program.CompiscriptParser import CompiscriptParser
from src.semantic.semantic import run_semantic_analysis

def parse_code(src: str):
    input_stream = InputStream(src)
    lexer = CompiscriptLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = CompiscriptParser(tokens)
    tree = parser.program()   #
    return tree, tokens

def get_errors(src: str):
    tree, tokens = parse_code(src)
    issues = run_semantic_analysis(tree, tokens)
    return [i for i in issues if i.kind == "error"]

# ------- Const: inicialización obligatoria -------
def test_const_requires_initializer():
    code = """
    {
      const PI: integer;
    }
    """
    errs = get_errors(code)
    assert any("const" in e.message.lower() and "deben inicializarse" in e.message for e in errs)

def test_const_with_initializer_ok():
    code = """
    {
      const PI: integer = 314;
    }
    """
    errs = get_errors(code)
    assert not errs

# ------- Asignaciones -------
def test_assignment_type_mismatch():
    code = """
    {
      let a: integer = 1;
      a = "hola";
    }
    """
    errs = get_errors(code)
    assert any("No se puede asignar valor de tipo 'string' a variable 'a' de tipo 'integer'" in e.message for e in errs)

def test_assignment_numeric_promotion_ok():
    code = """
    {
      let x: float = 0.0;
      let y: integer = 2;
      x = y;  // int -> float permitido
    }
    """
    errs = get_errors(code)
    assert not errs

# ------- Comparaciones -------
def test_relational_incompatible_types():
    code = """
    {
      let a: integer = 1;
      let s: string = "x";
      let b: boolean = a < s;
    }
    """
    errs = get_errors(code)
    assert any("Comparación '<' entre tipos incompatibles 'integer' y 'string'" in e.message for e in errs)

def test_equality_numeric_promotion_ok():
    code = """
    {
      let a: integer = 1;
      let b: float = 1.0;
      let c: boolean = a == b;
    }
    """
    errs = get_errors(code)
    assert not errs

def test_equality_incompatible_lists():
    code = """
    {
      let xs: integer[] = [1,2,3];
      let s: string = "x";
      let b: boolean = xs == s;
    }
    """
    errs = get_errors(code)
    assert any("Comparación '=='" in e.message and "incompatibles" in e.message for e in errs)

# ------- Listas -------
def test_list_uniform_element_types_error():
    code = """
    {
      let xs = [1, "a", 3];
    }
    """
    errs = get_errors(code)
    assert any("Los elementos de una lista deben ser del mismo tipo." in e.message for e in errs)

def test_list_assignment_element_type_ok():
    code = """
    {
      let xs: integer[] = [1,2,3];
      xs[0] = 10;
    }
    """
    errs = get_errors(code)
    assert not errs

def test_list_assignment_element_type_mismatch():
    code = """
    {
      let xs: integer[] = [1,2,3];
      xs[0] = "hola";
    }
    """
    errs = get_errors(code)
    assert any("No se puede asignar 'string' a un elemento de lista de tipo 'integer'" in e.message for e in errs)

def test_list_index_must_be_integer():
    code = """
    {
      let xs: integer[] = [1,2,3];
      let a = xs["0"];
    }
    """
    errs = get_errors(code)
    assert any("índice de una lista" in e.message.lower() for e in errs)

def test_null_comparison_with_list_ok():
    code = """
    {
      let xs: integer[] = [1,2];
      let b: boolean = xs == null;
    }
    """
    errs = get_errors(code)
    assert not errs
