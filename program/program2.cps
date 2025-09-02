// Constante correctamente inicializada
const PI: integer = 314;

// Variables declaradas antes de usar
let a: integer = 1;
let b: integer = 2;

// Funcion declarada antes de llamarse (tipos estrictos)
function suma(x: integer, y: integer): integer {
  return x + y;
}

// Llamada válida
let r: integer = suma(a, b);

// Expresiones booleanas válidas para &&
let ok1: boolean = (a > 0) && (b < 5);
let ok2: boolean = (r == 3) && (a != b);

// Nada de concatenación con '+': evita "texto" + numero
// Si tu print acepta solo un valor, imprime solo enteros o solo strings por separado
print("Inicio");
print(a);
print(b);
print(r);

// Un while con condición booleana
let c: integer = 0;
while (c < 3 && ok1) {
  c = c + 1;
}

// Asignación válida
let z: integer;
z = r - a;  // ambas integer -> OK


// ======================
// ERRORES SEMÁNTICOS
// ======================

// 1) Uso de variable no declarada
x = 10;                 // ERROR: Variable 'x' no existe.

// 2) Redeclaración en el mismo ámbito
let a: integer = 7;     // ERROR: Variable 'a' ya está definida en este ámbito.

// 3) Asignación incompatible de tipos
let s: string = 123;    // ERROR: No se puede asignar INTEGER a variable s: STRING.

// 4) Condición no booleana en if
if (r + a) {            // ERROR: La condición en if debe ser booleana, no INTEGER.
  print("nunca");
}

// 5) Operación aritmética con no-numéricos
let q: integer = "2" + 1;  // ERROR: Operación aritmética requiere numéricos, no STRING y INTEGER.

// 6) Comparación relacional con no numéricos
let cmp: boolean = "hola" < 3; // ERROR: Comparación relacional requiere numéricos.

// 7) break fuera de bucle
break;                  // ERROR: break solo puede usarse dentro de un bucle.

// 8) Función duplicada
function suma(x: integer, y: integer): integer { // ERROR: Función 'suma' ya está declarada.
  return x + y;
}

// 9) Número/tipo de argumentos incorrectos
let r2: integer = suma(a);          // ERROR: Número de argumentos incorrecto.
let r3: integer = suma(a, "2");     // ERROR: Argumento 2 incompatible: se esperaba INTEGER, llegó STRING.

// 10) Función no-void sin return en todos los caminos
function f1(x: integer): integer {  // ERROR: La función 'f1' debe retornar INTEGER en todos los caminos.
  if (x > 0) {
    return x;
  }
  // falta return aquí
}

// 11) Retorno de tipo incompatible
function esPositivo(x: integer): boolean {
  return x;                          // ERROR: Tipo de retorno incompatible: se esperaba BOOLEAN, se obtuvo INTEGER.
}

// 12) foreach sobre no-arreglo
foreach (it in a) {                  // ERROR: foreach requiere un arreglo como colección.
  print(it);
}

// 13) Arreglo con elementos heterogéneos
let arr = [1, "dos", 3];             // ERROR: Todos los elementos del arreglo deben ser del mismo tipo.

// 14) Indexación con índice no-integer
let v = arr["0"];                    // ERROR: El índice de un arreglo debe ser integer.

// 15) Indexación sobre no-arreglo
let nn = 5;
let bad = nn[0];                     // ERROR: Indexación sobre un no-arreglo.

// 16) this fuera de clase
let t = this;                        // ERROR: Uso de 'this' fuera de método/constructor.


// 17) Clases y miembros
class Punto {
  x: integer;
  x: integer;                        // ERROR: Miembro duplicado 'x'.
  function setX(n: integer): void {
    this.x = n;
  }
  function getX(): integer {
    // ok
    return this.x;
  }
}

let p: Punto = new Punto();
p.setX(10);
p.setX("cero");                      // ERROR: Arg 1 incompatible: se esperaba INTEGER, llegó STRING.
p.getX = 123;                        // ERROR: No se puede asignar a método 'getX'.
a.prop = 1;                          // ERROR: Asignación a propiedad requiere objeto a la izquierda del '.'
p.y = true;                          // ERROR: 'Punto' no tiene miembro 'y'.

// 18) Constante reasignada
const K: integer = 5;
K = 6;                               // ERROR: No se puede asignar a constante 'K'.