# Analizador Semántico de Compiscript

Este proyecto implementa el **analizador sintáctico** y **semántico** para el lenguaje **Compiscript**, junto con un IDE mínimo y una batería de tests.

---

## 🗂 Estructura del repositorio

```text
semantic-analysis/
│
├── program/                   # Gramática y ejemplos
│   ├── Compiscript.bnf        # Definición BNF (documentación)
│   ├── Compiscript.g4         # Gramática ANTLR v4
│   ├── Driver.py              # Entrypoint: parseo + análisis semántico
│   └── program.cps            # Ejemplo de programa en Compiscript
│
├── src/                       # Código fuente del compilador
│   ├── ide/
│   │   └── ide.py             # Editor ligero / CLI para cargar .cps
│   │
│   ├── parser/
│   │   └── parser.py          # Wrapper sobre el lexer/parser de ANTLR
│   │
│   └── semantic/
│       └── semantic.py        # Reglas semánticas (tabla de símbolos, chequeos)
│
├── test/                      # Tests unitarios (pytest)
│   ├── syntax/
│   │   └── syntax.py          # Casos de parsing exitoso / errores de sintaxis
│   │
│   └── semantic/
│       └── semantic.py        # Casos correctos / errores semánticos
│
├── antlr-4.13.1-complete.jar  # Herramienta ANTLR v4
├── Dockerfile                 # Imagen Docker con Java, Python y ANTLR
├── dockerignore.txt           # Archivos ignorados al construir la imagen
├── python-venv.sh             # Script para crear entorno virtual Python
├── requirements.txt           # Dependencias Python (pytest, antlr4-python3-runtime…)
├── .gitignore
└── README.md                  # ← ¡Este archivo!
```

---

## 📦 Contenido de cada directorio / archivo

- **program/**  
  - `Compiscript.g4` – Gramática ANTLR en formato v4.  
  - `Compiscript.bnf` – Versión BNF para documentación.  
  - `Driver.py` – Punto de entrada: invoca al parser y luego al analizador semántico.  
  - `program.cps` – Ejemplo de código fuente en Compiscript.

- **src/parser/parser.py**  
  - Carga el lexer y parser generados por ANTLR.  
  - Expone funciones para parsear árboles de sintaxis (CPS → ParseTree).

- **src/semantic/semantic.py**  
  - Implementa `Visitor` o `Listener` para recorrer el ParseTree.  
  - Construye y gestiona la **tabla de símbolos** (alcances, variables, funciones).  
  - Verifica tipos, ámbitos, firmas de funciones, control de flujo, clases, estructuras…

- **src/ide/ide.py**  
  - Pequeño editor/CLI que permite abrir un `.cps`, parsearlo y mostrar errores sintácticos o semánticos en consola.

- **test/syntax/syntax.py**  
  - Pruebas unitarias para el parser:  
    - Programas válidos → sin errores.  
    - Programas con errores de sintaxis → detectados.

- **test/semantic/semantic.py**  
  - Pruebas unitarias para el análisis semántico:  
    - Casos válidos (tipos correctos, ámbito, firmas).  
    - Casos con errores semánticos (redeclaración, tipos incompatibles…).

- **antlr-4.13.1-complete.jar**  
  - Versión embebida de ANTLR v4 para generar lexer/parser.

- **python-venv.sh**  
  - Script para crear y activar un entorno virtual (`venv`) con Python 3.8+.

- **requirements.txt**  
  ```text
  antlr4-python3-runtime
  pytest
  ```

- **Dockerfile** / **dockerignore.txt**  
  - Imagen basada en Alpine/Java/Python. Incluye ANTLR y dependencias.  
  - Permite ejecutar todo dentro de un contenedor aislado.

---

## ⚙️ Requisitos

- Java 11+ (para ANTLR)  
- Python 3.8+  
- `antlr-4.13.1-complete.jar` (ya incluido)  
- `git`  
- Opcional: [Docker](https://www.docker.com/) + `docker build` / `docker run`  

---

## 🚀 Instalación y puesta en marcha

1. **Clonar el repositorio**  
   ```bash
   git clone https://github.com/tu-org/semantic-analysis.git
   cd semantic-analysis
   ```

2. **Entorno Python**  
   ```bash
   chmod +x python-venv.sh
   ./python-venv.sh          # crea y activa venv
   pip install -r requirements.txt
   ```

3. **Generar parser con ANTLR**  
   ```bash
   java -jar antlr-4.13.1-complete.jar      -Dlanguage=Python3      -o src/parser/program      program/Compiscript.g4
   ```

4. **Ejecutar ejemplo**  
   ```bash
   # desde la raíz del proyecto, con venv activado
   python program/Driver.py program/program.cps
   ```
   - Sin salida → programa válido.  
   - Mensajes de error → sintaxis o semántica violadas.

---

## 🔧 Ejecutar tests

Con pytest instalado y venv activo:
```bash
pytest -q
```

---

## 🐳 Uso con Docker

1. **Construir imagen**  
   ```bash
   docker build -t cps-analyzer .
   ```
2. **Correr contenedor**  
   ```bash
   docker run --rm -v "$(pwd)":/work -w /work cps-analyzer      bash -c "antlr-4 program/Compiscript.g4 && python program/Driver.py program/program.cps"
   ```

---
