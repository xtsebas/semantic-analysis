from pathlib import Path
import textwrap

from src.parser.parser import parse_file
from src.semantic.semantic import SemanticVisitor, TypeKind

def run_semantic_on(code: str):
    tmp = Path("test/_tmp_prog.cps")
    tmp.write_text(textwrap.dedent(code), encoding="utf-8")
    result = parse_file(str(tmp))
    v = SemanticVisitor()
    _ = result.tree.accept(v)
    return v.issues

def test_arith_ok_int_and_float():
    issues = run_semantic_on("""
        print(1 + 2 * 3);
        print(1.0 + 2);
        print(10 / 2);
    """)
    assert not issues

def test_arith_error_with_boolean():
    issues = run_semantic_on("""
        print(1 + true);
    """)
    assert issues and "aritmética" in issues[0].message

def test_logic_ok():
    issues = run_semantic_on("""
        print(!(true && (false || true)));
    """)
    assert not issues

def test_logic_error_non_boolean():
    issues = run_semantic_on("""
        print(1 && 2);
    """)
    assert issues and "lógico" in issues[0].message

def test_unary_plus_minus_and_not():
    issues = run_semantic_on("""
        print(+1);
        print(-2.5);
        print(!false);
    """)
    assert not issues

def test_unary_error():
    issues = run_semantic_on("""
        print(!1);
        print(+"hola");
    """)
    assert len(issues) >= 2
