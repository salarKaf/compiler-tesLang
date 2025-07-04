# parser.py
"""Parser for TesLang Compiler using PLY"""

import ply.yacc as yacc
try:
    from Lexer.tokens import tokens
except ImportError:
    from tokens import tokens

from ast_nodes import *
from symbol_table import SymbolTable, Symbol
from semantic_analyzer import SemanticAnalyzer

# Global variables for parsing
symbol_table = None
current_function = None
errors = []

def add_error(message, line=None):
    """Add a parsing error"""
    if line:
        errors.append(f"Line {line}: {message}")
    else:
        errors.append(message)

# Grammar Rules
def p_program(p):
    '''program : function_list'''
    p[0] = Program(p[1])

def p_function_list(p):
    '''function_list : function_list function
                    | function'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_function(p):
    '''function : FUNK ID LPAREN param_list RPAREN LESS_THAN type GREATER_THAN LCURLYEBR stmt_list RCURLYEBR'''
    p[0] = Function(p[2], p[4], p[7], p[10], p.lineno(1))

def p_function_no_params(p):
    '''function : FUNK ID LPAREN RPAREN LESS_THAN type GREATER_THAN LCURLYEBR stmt_list RCURLYEBR'''
    p[0] = Function(p[2], [], p[6], p[9], p.lineno(1))

def p_param_list(p):
    '''param_list : param_list COMMA parameter
                 | parameter'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_parameter(p):
    '''parameter : ID AS type'''
    p[0] = Parameter(p[1], p[3], p.lineno(1))

def p_type(p):
    '''type : INT
           | STR  
           | MSTR
           | BOOL
           | VECTOR
           | NULL'''
    p[0] = p[1]

def p_stmt_list(p):
    '''stmt_list : stmt_list statement
                 | statement'''
    if len(p) == 2:
        if isinstance(p[1], list):
            p[0] = p[1]
        else:
            p[0] = [p[1]]
    else:
        if isinstance(p[2], list):
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1] + [p[2]]


def p_statement(p):
    '''statement : var_declaration
                 | assignment
                 | function_call_stmt
                 | return_stmt
                 | if_stmt
                 | for_stmt
                 | while_stmt'''
    if isinstance(p[1], list):
        p[0] = p[1]  # برمی‌گردونه لیست استیتمنت‌ها (مثل decl + assign)
    else:
        p[0] = p[1]


def p_var_declaration(p):
    '''var_declaration : ID DBL_COLON type SEMI_COLON
                       | ID DBL_COLON type EQ expression SEMI_COLON'''
    if len(p) == 5:
        # فقط تعریف ساده
        p[0] = VarDeclaration(p[1], p[3], p.lineno(1))
    else:
        # تعریف همراه مقداردهی
        decl = VarDeclaration(p[1], p[3], p.lineno(1))
        assign = Assignment(p[1], p[5], p.lineno(4))
        p[0] = [decl, assign]


def p_assignment(p):
    '''assignment : ID EQ expression SEMI_COLON
                 | array_access EQ expression SEMI_COLON'''
    p[0] = Assignment(p[1], p[3], p.lineno(2))

def p_array_access(p):
    '''array_access : ID LSQUAREBR expression RSQUAREBR'''
    p[0] = ArrayAccess(p[1], p[3], p.lineno(1))

def p_function_call_stmt(p):
    '''function_call_stmt : function_call SEMI_COLON'''
    p[0] = p[1]

def p_function_call(p):
    '''function_call : ID LPAREN arg_list RPAREN
                    | ID LPAREN RPAREN
                    | PRINT LPAREN arg_list RPAREN
                    | PRINT LPAREN RPAREN'''
    if len(p) == 4:
        p[0] = FunctionCall(p[1], [], p.lineno(1))
    else:
        p[0] = FunctionCall(p[1], p[3], p.lineno(1))

def p_arg_list(p):
    '''arg_list : arg_list COMMA expression
               | expression'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_return_stmt(p):
    '''return_stmt : RETURN expression SEMI_COLON
                  | RETURN SEMI_COLON'''
    if len(p) == 3:
        p[0] = Return(None, p.lineno(1))
    else:
        p[0] = Return(p[2], p.lineno(1))

def p_if_stmt(p):
    '''if_stmt : IF LSQUAREBR LSQUAREBR expression RSQUAREBR RSQUAREBR BEGIN stmt_list END
              | IF LSQUAREBR LSQUAREBR expression RSQUAREBR RSQUAREBR BEGIN stmt_list END ELSE BEGIN stmt_list END'''
    if len(p) == 10:
        p[0] = If(p[4], p[8], None, p.lineno(1))
    else:
        p[0] = If(p[4], p[8], p[12], p.lineno(1))

def p_for_stmt(p):
    '''for_stmt : FOR LPAREN ID EQ expression TO expression RPAREN BEGIN stmt_list END'''
    p[0] = For(p[3], p[5], p[7], p[10], p.lineno(1))

def p_while_stmt(p):
    '''while_stmt : WHILE LPAREN expression RPAREN BEGIN stmt_list END
                 | WHILE LPAREN expression RPAREN DO BEGIN stmt_list END'''
    if len(p) == 8:
        p[0] = While(p[3], p[6], p.lineno(1))
    else:
        p[0] = While(p[3], p[7], p.lineno(1))

def p_expression_binop(p):
    '''expression : expression PLUS expression
                 | expression MINUS expression
                 | expression MULTIPLY expression
                 | expression DIVIDE expression
                 | expression EQEQ expression
                 | expression NEQ expression
                 | expression LESS_THAN expression
                 | expression GREATER_THAN expression
                 | expression LTEQ expression
                 | expression GTEQ expression
                 | expression AND expression
                 | expression OR expression'''
    p[0] = BinaryOp(p[1], p[2], p[3], p.lineno(2))

def p_expression_unary(p):
    '''expression : NOT expression
                 | MINUS expression %prec UMINUS'''
    p[0] = UnaryOp(p[1], p[2], p.lineno(1))

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_number(p):
    '''expression : NUMBER'''
    p[0] = Number(p[1], p.lineno(1))

def p_expression_string(p):
    '''expression : STRING
                 | MSTRING'''
    p[0] = String(p[1], p.lineno(1))

def p_expression_boolean(p):
    '''expression : TRUE
                 | FALSE'''
    p[0] = Boolean(p[1], p.lineno(1))

def p_expression_id(p):
    '''expression : ID'''
    p[0] = Identifier(p[1], p.lineno(1))

def p_expression_array_access(p):
    '''expression : array_access'''
    p[0] = p[1]

def p_expression_function_call(p):
    '''expression : function_call'''
    p[0] = p[1]

def p_expression_list_call(p):
    '''expression : ID LPAREN expression RPAREN'''
    if p[1] == 'list':
        p[0] = ListCall(p[3], p.lineno(1))
    elif p[1] == 'print':
        p[0] = FunctionCall(p[1], [p[3]], p.lineno(1))
    else:
        p[0] = FunctionCall(p[1], [p[3]], p.lineno(1))

def p_expression_length(p):
    '''expression : LEN LPAREN expression RPAREN'''
    p[0] = FunctionCall('length', [p[3]], p.lineno(1))

def p_expression_ternary(p):
    '''expression : expression QMARK expression COLON expression'''
    p[0] = TernaryOp(p[1], p[3], p[5], p.lineno(2))

# Precedence and associativity
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQEQ', 'NEQ'),
    ('left', 'LESS_THAN', 'GREATER_THAN', 'LTEQ', 'GTEQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULTIPLY', 'DIVIDE'),
    ('right', 'UMINUS', 'NOT'),
)

def p_error(p):
    """Handle parsing errors"""
    if p:
        add_error(f"Syntax error at token {p.type}", p.lineno)
    else:
        add_error("Syntax error at EOF")

# Main compiler function
def compile_teslang(code):
    """Main function to compile TesLang code"""
    global symbol_table, current_function, errors
    
    # Reset global state
    symbol_table = SymbolTable()
    current_function = None
    errors = []
    
    # Build parser
    parser = yacc.yacc()
    
    # Parse the code
    try:
        ast = parser.parse(code, debug=False)
        if not ast:
            return errors
        
        # Perform semantic analysis
        analyzer = SemanticAnalyzer()
        semantic_errors = analyzer.analyze(ast)
        
        return semantic_errors
        
    except Exception as e:
        errors.append(f"Parser error: {str(e)}")
        return errors

def parse_code(code):
    """Parse code and return AST (without semantic analysis)"""
    global symbol_table, current_function, errors
    
    # Reset global state
    symbol_table = SymbolTable()
    current_function = None
    errors = []
    
    # Build parser
    parser = yacc.yacc()
    
    # Parse the code
    try:
        ast = parser.parse(code, debug=False)
        return ast
        
    except Exception as e:
        print(f"Parser error: {str(e)}")
        return None