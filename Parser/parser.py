# parser.py
"""Parser for TesLang Compiler using PLY - Fixed for Nested Functions"""

import ply.yacc as yacc
try:
    from Lexer.tokens import tokens
except ImportError:
    from tokens import tokens

from Parser.ast_nodes import *

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from SemanticAnalyzerF.symbol_table import SymbolTable, Symbol
from SemanticAnalyzerF.semantic_analyzer import SemanticAnalyzer

# Global variables for parsing
symbol_table = None
function_context_stack = []  # Stack to track nested function contexts
errors = []
current_function_name = None


def add_error(message, line=None):
    """Add a parsing error"""
    if line:
        errors.append(f"Line {line}: {message}")
    else:
        errors.append(message)

def push_function_context(function_name):
    """Push a new function context onto the stack"""
    function_context_stack.append(function_name)

def pop_function_context():
    """Pop the current function context from the stack"""
    if function_context_stack:
        return function_context_stack.pop()
    return None

def get_current_function():
    """Get the current function context"""
    return function_context_stack[-1] if function_context_stack else None

def is_inside_function():
    """Check if we're currently inside a function"""
    global current_function_name
    return current_function_name is not None

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
    '''function : FUNK ID LPAREN param_list RPAREN LESS_THAN type GREATER_THAN LCURLYEBR stmt_list RCURLYEBR
               | FUNK ID LPAREN RPAREN LESS_THAN type GREATER_THAN LCURLYEBR stmt_list RCURLYEBR
               | FUNK ID LPAREN param_list RPAREN LESS_THAN type GREATER_THAN ARROW RETURN expression SEMI_COLON
               | FUNK ID LPAREN RPAREN LESS_THAN type GREATER_THAN ARROW RETURN expression SEMI_COLON'''
    
    global current_function_name
    old_function = current_function_name
    current_function_name = p[2]
    
    if len(p) == 12:  # تابع با پارامتر و بدنه
        p[0] = Function(p[2], p[4], p[7], p[10], p.lineno(1))
    elif len(p) == 11:  # تابع بدون پارامتر و با بدنه
        p[0] = Function(p[2], [], p[6], p[9], p.lineno(1))
    elif len(p) == 13:  # تابع کوتاه با پارامتر
        return_stmt = Return(p[11], p.lineno(10))
        p[0] = Function(p[2], p[4], p[7], [return_stmt], p.lineno(1))
    else:  # تابع کوتاه بدون پارامتر
        return_stmt = Return(p[10], p.lineno(9))
        p[0] = Function(p[2], [], p[6], [return_stmt], p.lineno(1))
    
    current_function_name = old_function

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
                 | statement
                 | empty'''
    # اگر داخل تابع نیستیم و statement یک Function است، context را مدیریت کنیم
    if len(p) == 2 and hasattr(p[1], '__class__') and p[1].__class__.__name__ == 'Function':
        push_function_context(p[1].name)
        
    if p[1] is None:
        p[0] = []
    elif len(p) == 2:
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
                 | while_stmt
                 | do_while_stmt
                 | block_stmt
                 | function'''
    if isinstance(p[1], list):
        p[0] = p[1]
    else:
        p[0] = p[1]

def p_var_declaration(p):
    '''var_declaration : ID DBL_COLON type SEMI_COLON
                       | ID DBL_COLON type EQ expression SEMI_COLON'''
    if len(p) == 5:
        p[0] = VarDeclaration(p[1], p[3], p.lineno(1))
    else:
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
                    | PRINT LPAREN RPAREN
                    | LEN LPAREN expression RPAREN'''
    if len(p) == 4:
        p[0] = FunctionCall(p[1], [], p.lineno(1))
    else:
        if p[1] == 'length':
            p[0] = FunctionCall('length', [p[3]], p.lineno(1))
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
    
    # Don't check function context here - let semantic analyzer handle it
    if len(p) == 3:
        p[0] = Return(None, p.lineno(1))
    else:
        p[0] = Return(p[2], p.lineno(1))

def p_if_stmt(p):
    '''if_stmt : IF LSQUAREBR LSQUAREBR expression RSQUAREBR RSQUAREBR statement
              | IF LSQUAREBR LSQUAREBR expression RSQUAREBR RSQUAREBR statement ELSE statement'''
    if len(p) == 8:
        p[0] = If(p[4], p[7], None, p.lineno(1))
    else:
        p[0] = If(p[4], p[7], p[9], p.lineno(1))

def p_for_stmt(p):
    '''for_stmt : FOR LPAREN ID EQ expression TO expression RPAREN BEGIN stmt_list END'''
    p[0] = For(p[3], p[5], p[7], p[10], p.lineno(1))


def p_while_stmt(p):
    '''while_stmt : WHILE LSQUAREBR LSQUAREBR expression RSQUAREBR RSQUAREBR statement'''
    p[0] = While(p[4], p[7], p.lineno(1))

def p_do_while_stmt(p):
    '''do_while_stmt : DO statement WHILE LSQUAREBR LSQUAREBR expression RSQUAREBR RSQUAREBR'''
    p[0] = DoWhile(p[2], p[6], p.lineno(1))

def p_block_stmt(p):
    '''block_stmt : BEGIN stmt_list END'''
    p[0] = Block(p[2], p.lineno(1))

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
                 | MINUS expression %prec UMINUS
                 | PLUS expression %prec UPLUS'''
    p[0] = UnaryOp(p[1], p[2], p.lineno(1))

def p_expression_ternary(p):
    '''expression : expression QMARK expression COLON expression'''
    p[0] = TernaryOp(p[1], p[3], p[5], p.lineno(2))

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_array_literal(p):
    '''expression : LSQUAREBR arg_list RSQUAREBR
                 | LSQUAREBR RSQUAREBR'''
    if len(p) == 3:
        p[0] = ArrayLiteral([], p.lineno(1))
    else:
        p[0] = ArrayLiteral(p[2], p.lineno(1))

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

def p_empty(p):
    '''empty :'''
    pass

# Precedence and associativity
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQEQ', 'NEQ'),
    ('left', 'LESS_THAN', 'GREATER_THAN', 'LTEQ', 'GTEQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULTIPLY', 'DIVIDE'),
    ('right', 'UMINUS', 'UPLUS', 'NOT'),
    ('right', 'QMARK', 'COLON'),
)

def p_error(p):
    if p:
        msg = f"Line {p.lineno}: Syntax error near '{p.value}' (token: {p.type})"

        if p.type == 'ID':
            lowercase_keywords = ['begin', 'end', 'if', 'else', 'while', 'do', 'for', 'return']
            if p.value.lower() in lowercase_keywords and p.value != p.value.lower():
                msg += f" — did you mean '{p.value.lower()}'? Keywords must be lowercase"
            else:
                msg += " — unexpected identifier"
                if p.lineno > 1:
                    msg += " — possible missing semicolon on the previous line"

        elif p.type == 'LCURLYEBR':
            msg += " — did you mean to use 'begin' instead of '{'?"
        elif p.type == 'LPAREN':
            msg += " — maybe you're missing [[ ]] for conditions?"

        add_error(msg, p.lineno)
    else:
        add_error("Syntax error: unexpected end of file")

# Main compiler function
def compile_teslang(code):
    """Main function to compile TesLang code"""
    global symbol_table, function_context_stack, errors, current_function_name    
    # Reset global state
    symbol_table = SymbolTable()
    function_context_stack = []
    errors = []
    current_function_name = None
    
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
        
        # Combine parsing and semantic errors
        all_errors = errors + semantic_errors
        return all_errors
        
    except Exception as e:
        errors.append(f"Parser error: {str(e)}")
        return errors

def parse_code(code):
    """Parse code and return AST (without semantic analysis)"""
    global symbol_table, function_context_stack, errors, current_function_name    
    # Reset global state
    symbol_table = SymbolTable()
    function_context_stack = []
    errors = []
    current_function_name = None
    
    # Build parser
    parser = yacc.yacc()
    
    # Parse the code
    try:
        ast = parser.parse(code, debug=False)
        return ast
        
    except Exception as e:
        print(f"Parser error: {str(e)}")
        return None