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
