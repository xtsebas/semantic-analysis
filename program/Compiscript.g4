grammar Compiscript;

// ------------------
// Parser Rules
// ------------------

program: statement* EOF;

statement
  : variableDeclaration
  | constantDeclaration
  | assignment
  | functionDeclaration
  | classDeclaration
  | expressionStatement
  | printStatement
  | block
  | ifStatement
  | whileStatement
  | doWhileStatement
  | forStatement
  | foreachStatement
  | tryCatchStatement
  | switchStatement
  | breakStatement
  | continueStatement
  | returnStatement
  ;

block: '{' statement* '}';

variableDeclaration
  : ('let' | 'var') Identifier typeAnnotation? initializer? ';'
  ;

constantDeclaration
  : 'const' Identifier typeAnnotation? '=' expression ';'
  ;

typeAnnotation: ':' type;
initializer: '=' expression;

assignment
  : Identifier '=' expression ';'
  | expression '.' Identifier '=' expression ';' // property assignment
  ;

expressionStatement: expression ';';
printStatement: 'print' '(' expression ')' ';';

ifStatement: 'if' '(' expression ')' block ('else' block)?;
whileStatement: 'while' '(' expression ')' block;
doWhileStatement: 'do' block 'while' '(' expression ')' ';';
forStatement: 'for' '(' (variableDeclaration | assignment | ';') expression? ';' expression? ')' block;
foreachStatement: 'foreach' '(' Identifier 'in' expression ')' block;
breakStatement: 'break' ';';
continueStatement: 'continue' ';';
returnStatement: 'return' expression? ';';

tryCatchStatement: 'try' block 'catch' '(' Identifier ')' block;

switchStatement: 'switch' '(' expression ')' '{' switchCase* defaultCase? '}';
switchCase: 'case' expression ':' statement*;
defaultCase: 'default' ':' statement*;

functionDeclaration: 'function' Identifier '(' parameters? ')' (':' type)? block;
parameters: parameter (',' parameter)*;
parameter: Identifier (':' type)?;

classDeclaration: 'class' Identifier (':' Identifier)? '{' classMember* '}';
classMember: functionDeclaration | variableDeclaration | constantDeclaration;

// ------------------
// Expression Rules — Recursión izquierda con labels
// ------------------

expression: assignmentExpr;

assignmentExpr
  : lhs=leftHandSide '=' assignmentExpr            # AssignExpr
  | lhs=leftHandSide '.' Identifier '=' assignmentExpr # PropertyAssignExpr
  | conditionalExpr                                # ExprNoAssign
  ;

conditionalExpr
  : logicalOrExpr ('?' expression ':' expression)? # TernaryExpr
  ;

logicalOrExpr
  : logicalOrExpr '||' logicalAndExpr              # LogicalOrOp
  | logicalAndExpr                                 # LogicalOrPassthrough
  ;

logicalAndExpr
  : logicalAndExpr '&&' equalityExpr               # LogicalAndOp
  | equalityExpr                                   # LogicalAndPassthrough
  ;

equalityExpr
  : equalityExpr op=('==' | '!=') relationalExpr   # EqualityOp
  | relationalExpr                                 # EqualityPassthrough
  ;

relationalExpr
  : relationalExpr op=('<' | '<=' | '>' | '>=') additiveExpr  # RelationalOp
  | additiveExpr                                              # RelationalPassthrough
  ;

additiveExpr
  : additiveExpr op=('+' | '-') multiplicativeExpr # AdditiveOp
  | multiplicativeExpr                             # AdditivePassthrough
  ;

multiplicativeExpr
  : multiplicativeExpr op=('*' | '/' | '%') unaryExpr # MultiplicativeOp
  | unaryExpr                                         # MultiplicativePassthrough
  ;

unaryExpr
  : op=('-' | '!') unaryExpr                       # UnaryOp
  | primaryExpr                                    # UnaryPassthrough
  ;

primaryExpr
  : literalExpr                                    # LiteralPrimary
  | leftHandSide                                   # LeftHandSidePrimary
  | '(' expression ')'                             # ParenthesizedExpr
  ;

literalExpr
  : Literal
  | arrayLiteral
  | 'null'
  | 'true'
  | 'false'
  ;

leftHandSide
  : primaryAtom (suffixOp)*
  ;

primaryAtom
  : Identifier                                 # IdentifierExpr
  | 'new' Identifier '(' arguments? ')'        # NewExpr
  | 'this'                                     # ThisExpr
  ;

suffixOp
  : '(' arguments? ')'                        # CallExpr
  | '[' expression ']'                        # IndexExpr
  | '.' Identifier                            # PropertyAccessExpr
  ;

arguments: expression (',' expression)*;

arrayLiteral: '[' (expression (',' expression)*)? ']';

// ------------------
// Types
// ------------------

type: baseType ('[' ']')*;
baseType: 'boolean' | 'integer' | 'string' | Identifier;

// ------------------
// Lexer Rules
// ------------------

Literal
  : IntegerLiteral
  | StringLiteral
  ;

IntegerLiteral: [0-9]+;
StringLiteral: '"' (~["\r\n])* '"';

Identifier: [a-zA-Z_][a-zA-Z0-9_]*;

WS: [ \t\r\n]+ -> skip;
COMMENT: '//' ~[\r\n]* -> skip;
MULTILINE_COMMENT: '/*' .*? '*/' -> skip;