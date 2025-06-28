# parser.py
import ply.yacc as yacc
try:
    from Lexer.tokens import tokens
except ImportError:
    from tokens import tokens
import sys

# Symbol Table Implementation
class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
        self.children = []
        if parent:
            parent.children.append(self)
    
    def insert(self, name, symbol_info):
        self.symbols[name] = symbol_info
    
    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.lookup(name)
        return None
    
    def lookup_current_scope(self, name):
        return self.symbols.get(name)

class Symbol:
    def __init__(self, name, symbol_type, data_type=None, params=None, return_type=None, initialized=False, line=None):
        self.name = name
        self.symbol_type = symbol_type  # 'variable', 'function'
        self.data_type = data_type
        self.params = params or []
        self.return_type = return_type
        self.initialized = initialized
        self.line = line

# AST Node Classes
class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, functions):
        self.functions = functions

class Function(ASTNode):
    def __init__(self, name, params, return_type, body, line):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body
        self.line = line

class Parameter(ASTNode):
    def __init__(self, name, param_type, line):
        self.name = name
        self.param_type = param_type
        self.line = line

class VarDeclaration(ASTNode):
    def __init__(self, name, var_type, line):
        self.name = name
        self.var_type = var_type
        self.line = line

class Assignment(ASTNode):
    def __init__(self, target, value, line):
        self.target = target
        self.value = value
        self.line = line

class FunctionCall(ASTNode):
    def __init__(self, name, args, line):
        self.name = name
        self.args = args
        self.line = line

class Return(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line

class If(ASTNode):
    def __init__(self, condition, then_stmt, else_stmt, line):
        self.condition = condition
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt
        self.line = line

class For(ASTNode):
    def __init__(self, var, start, end, body, line):
        self.var = var
        self.start = start
        self.end = end
        self.body = body
        self.line = line

class While(ASTNode):
    def __init__(self, condition, body, line):
        self.condition = condition
        self.body = body
        self.line = line

class BinaryOp(ASTNode):
    def __init__(self, left, op, right, line):
        self.left = left
        self.op = op
        self.right = right
        self.line = line

class UnaryOp(ASTNode):
    def __init__(self, op, operand, line):
        self.op = op
        self.operand = operand
        self.line = line

class Identifier(ASTNode):
    def __init__(self, name, line):
        self.name = name
        self.line = line

class Number(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line

class String(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line

class Boolean(ASTNode):
    def __init__(self, value, line):
        self.value = value
        self.line = line

class TernaryOp(ASTNode):
    def __init__(self, condition, true_expr, false_expr, line):
        self.condition = condition
        self.true_expr = true_expr
        self.false_expr = false_expr
        self.line = line

class ArrayAccess(ASTNode):
    def __init__(self, array, index, line):
        self.array = array
        self.index = index
        self.line = line

class ListCall(ASTNode):
    def __init__(self, size, line):
        self.size = size
        self.line = line

# Global variables for parsing
symbol_table = None
current_function = None
errors = []

def add_error(message, line=None):
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
        p[0] = [p[1]]
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
    p[0] = p[1]

def p_var_declaration(p):
    '''var_declaration : ID DBL_COLON type SEMI_COLON'''
    p[0] = VarDeclaration(p[1], p[3], p.lineno(1))

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
    if p:
        add_error(f"Syntax error at token {p.type}", p.lineno)
    else:
        add_error("Syntax error at EOF")

# Semantic Analysis
class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.current_function = None
        self.errors = []

    def add_error(self, message, line=None):
        if line:
            self.errors.append(f"Line {line}: Error: {message}")
        else:
            self.errors.append(f"Error: {message}")

    def analyze(self, ast):
        self.visit(ast)
        return self.errors

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for child in getattr(node, '__dict__', {}).values():
            if isinstance(child, list):
                for item in child:
                    if isinstance(item, ASTNode):
                        self.visit(item)
            elif isinstance(child, ASTNode):
                self.visit(child)

    def visit_Program(self, node):
        for func in node.functions:
            if not self.symbol_table.lookup_current_scope(func.name):
                params = [(p.name, p.param_type) for p in func.params]
                symbol = Symbol(func.name, 'function', params=params, return_type=func.return_type, line=func.line)
                self.symbol_table.insert(func.name, symbol)
        for func in node.functions:
            self.visit_Function(func)

    def visit_Function(self, node):
        self.current_function = node
        func_scope = SymbolTable(self.symbol_table)
        old_table = self.symbol_table
        self.symbol_table = func_scope

        for param in node.params:
            symbol = Symbol(param.name, 'variable', param.param_type, initialized=True, line=param.line)
            self.symbol_table.insert(param.name, symbol)

        for stmt in node.body:
            self.visit(stmt)

        self.symbol_table = old_table
        self.current_function = None

    def visit_VarDeclaration(self, node):
        if self.symbol_table.lookup_current_scope(node.name):
            self.add_error(f"variable '{node.name}' is already defined", node.line)
        else:
            symbol = Symbol(node.name, 'variable', node.var_type, initialized=False, line=node.line)
            self.symbol_table.insert(node.name, symbol)

    def visit_Assignment(self, node):
        self.visit(node.value)

        if isinstance(node.target, str):
            var_symbol = self.symbol_table.lookup(node.target)
            if not var_symbol:
                self.add_error(f"function '{self.current_function.name}': variable '{node.target}' is not defined", node.line)
                return
            var_symbol.initialized = True
            value_type = self.get_expression_type(node.value)
            if value_type and var_symbol.data_type != value_type:
                self.add_error(f"function '{self.current_function.name}': variable '{node.target}' expected to be of type '{value_type}' but it is '{var_symbol.data_type}' instead", node.line)

        elif isinstance(node.target, ArrayAccess):
            self.visit(node.target.index)
            array_symbol = self.symbol_table.lookup(node.target.array)
            if not array_symbol:
                self.add_error(f"function '{self.current_function.name}': variable '{node.target.array}' is not defined", node.line)
                return
            if array_symbol.data_type != 'vector':
                self.add_error(f"function '{self.current_function.name}': expected '{node.target.array}' to be of type 'vector', but got '{array_symbol.data_type}' instead", node.line)

    def visit_FunctionCall(self, node):
        for arg in node.args:
            self.visit(arg)

        if node.name in ['print', 'list', 'length' , 'scan']:
            return self.handle_builtin_function(node)

        func_symbol = self.symbol_table.lookup(node.name)
        if not func_symbol:
            self.add_error(f"function '{node.name}' is not defined", node.line)
            return

        expected_params = len(func_symbol.params)
        actual_args = len(node.args)
        if expected_params != actual_args:
            self.add_error(f"function '{node.name}': expects {expected_params} arguments but got {actual_args}", node.line)
            return

        for i, (arg, (param_name, param_type)) in enumerate(zip(node.args, func_symbol.params)):
            arg_type = self.get_expression_type(arg)
            if arg_type and arg_type != param_type:
                self.add_error(f"function '{node.name}': expected '{param_name}' to be of type '{param_type}', but got '{arg_type}' instead", node.line)

    def handle_builtin_function(self, node):
        if node.name == 'print': return 'null'
        elif node.name == 'list': return 'vector'
        elif node.name == 'length': return 'int'
        elif node.name == 'scan':   return 'int'
        return None
    
    
    def visit_Return(self, node):
        if not self.current_function:
            self.add_error("return statement outside of function", node.line)
            return
        
        # بررسی مقدار داخل return
        if node.value:
            self.visit(node.value)  # ← همین خط مهمه

        expected_type = self.current_function.return_type
        actual_type = 'null' if node.value is None else self.get_expression_type(node.value)
        
        if actual_type and expected_type != actual_type:
            self.add_error(
                f"function '{self.current_function.name}': wrong return type. expected '{expected_type}' but got '{actual_type}'",
                node.line
            )


    def visit_Identifier(self, node):
        var_symbol = self.symbol_table.lookup(node.name)
        if not var_symbol:
            self.add_error(f"function '{self.current_function.name}': variable '{node.name}' is not defined", node.line)
        elif not var_symbol.initialized:
            self.add_error(f"function '{self.current_function.name}': Variable '{node.name}' is used before being assigned", node.line)

    def visit_TernaryOp(self, node):
        self.visit(node.condition)
        self.visit(node.true_expr)
        self.visit(node.false_expr)
        cond_type = self.get_expression_type(node.condition)
        if cond_type and cond_type != 'bool':
            self.add_error(f"ternary operator condition must be boolean, got '{cond_type}'", node.line)

    def get_expression_type(self, node):
        if isinstance(node, Number): return 'int'
        elif isinstance(node, String): return 'str'
        elif isinstance(node, Boolean): return 'bool'
        elif isinstance(node, Identifier):
            symbol = self.symbol_table.lookup(node.name)
            return symbol.data_type if symbol else None
        elif isinstance(node, FunctionCall):
            if node.name == 'list': return 'vector'
            elif node.name == 'length': return 'int'
            elif node.name == 'print': return 'null'
            else:
                func = self.symbol_table.lookup(node.name)
                return func.return_type if func else None
        elif isinstance(node, ArrayAccess): return 'int'
        elif isinstance(node, BinaryOp):
            return 'bool' if node.op in ['==', '!=', '<', '>', '<=', '>=', '&&', '||'] else 'int'
        elif isinstance(node, ListCall): return 'vector'
        elif isinstance(node, TernaryOp):
            t = self.get_expression_type(node.true_expr)
            f = self.get_expression_type(node.false_expr)
            return t if t == f else None
        return None

# Main compiler function
def compile_teslang(code):
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

# Test with the provided example
if __name__ == "__main__":
    test_code = '''
funk find(A as vector, n as int) <int>
{
k :: int;
j :: int;
for (i = 0 to length(A))
begin
if [[ n == k ]]
begin
return j;
end
j = x + 1;
end
return -1;
}
funk main() <null>
{
A :: int;
a :: int;
A = list(3);
A[0] = 1;
A[1] = 2;
A[2] = 3;
print(find(A, a));
print(find(A));
print(find(a, A));
return A;
}
'''
    
    errors = compile_teslang(test_code)
    for error in errors:
        print(error)