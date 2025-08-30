import argparse
import os
import sys

# para importar los módulos generados por ANTLR desde program/
sys.path.insert(0, os.path.dirname(__file__))

# para importar nuestro código desde src/
repo_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(repo_root, "src"))

from parser.parser import parse_file, tree_as_lisp
from semantic.semantic import SemanticVisitor


def main():
    ap = argparse.ArgumentParser(
        description="Compiscript — parsea y realiza análisis semántico de un archivo .cps"
    )
    ap.add_argument("file", help="Ruta a archivo .cps (fuente Compiscript)")
    ap.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="No imprimir el árbol si no hay errores."
    )
    args = ap.parse_args()

    if not os.path.isfile(args.file):
        print(f"ERROR: no existe el archivo: {args.file}", file=sys.stderr)
        sys.exit(2)

    # 1) Parseo
    result = parse_file(args.file)

    # 2) Errores de sintaxis
    if result.issues:
        print("Errores de sintaxis:", file=sys.stderr)
        for e in result.issues:
            print(f"  línea {e.line}, col {e.column}: {e.message}", file=sys.stderr)
        sys.exit(1)

    # 3) Análisis semántico
    visitor = SemanticVisitor()
    _ = result.tree.accept(visitor)

    if visitor.issues:
        print("Errores semánticos:", file=sys.stderr)
        for e in visitor.issues:
            print(f"  línea {e.line}, col {e.column}: {e.message}", file=sys.stderr)
        sys.exit(1)

    # 4) Dump opcional de la tabla de símbolos
    for line in visitor.symtab.export_as_lines():
        print(line)

    # 5) (Opcional) imprimir el árbol
    if not args.quiet:
        print(tree_as_lisp(result))


if __name__ == "__main__":
    main()