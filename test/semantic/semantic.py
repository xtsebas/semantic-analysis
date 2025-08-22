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

def test_redeclaration_same_scope_error():
    issues = run_semantic_on("""
        let x: integer = 1;
        let x: integer = 2;
    """)
    assert any("redeclarado" in i.message for i in issues)

def test_shadowing_in_inner_block_ok():
    issues = run_semantic_on("""
        let x: integer = 1;
        {
            let x: integer = 2;
            print(x + 1);
        }
        print(x + 1);
    """)
    assert not issues

def test_undeclared_use_error():
    issues = run_semantic_on("""
        print(y);
    """)
    assert any("no declarada" in i.message for i in issues)

def test_const_requires_no_reassignment_and_type_check():
    issues = run_semantic_on("""
        const PI: integer = 3;
        PI = 4;                // no se puede
        let r: string = "a";
        r = 10;                // tipo incompatible
    """)
    assert any("No se puede asignar a constante" in i.message for i in issues) \
        and any("Tipo incompatible en asignación" in i.message for i in issues)

def test_var_inference_matches_initializer():
    issues = run_semantic_on("""
        let a = 1;
        a = 2;
        a = "hola"; // incompatible
    """)
    assert any("Tipo incompatible en asignación" in i.message for i in issues)

