"""Semantic Analyzer for TesLang Compiler"""


from SemanticAnalyzerF.symbol_table import SymbolTable, Symbol
from Parser.ast_nodes import *

class SemanticAnalyzer:
    """Performs semantic analysis on the AST"""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.current_function = None
        self.errors = []

    def add_error(self, message, line=None):
        """Add a semantic error to the error list"""
        if line:
            self.errors.append(f"Line {line}: Error: {message}")
        else:
            self.errors.append(f"Error: {message}")

    def analyze(self, ast):
        """Main entry point for semantic analysis"""
        self.visit(ast)
        return self.errors

    def visit(self, node):
        """Visit a node using the visitor pattern"""
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Default visitor for nodes without specific visitors"""
        for child in getattr(node, '__dict__', {}).values():
            if isinstance(child, list):
                for item in child:
                    if isinstance(item, ASTNode):
                        self.visit(item)
            elif isinstance(child, ASTNode):
                self.visit(child)

    def visit_Program(self, node):
        """Visit the program node - first pass to collect function declarations"""
        for func in node.functions:
            if not self.symbol_table.lookup_current_scope(func.name):
                params = [(p.name, p.param_type) for p in func.params]
                symbol = Symbol(func.name, 'function', params=params, return_type=func.return_type, line=func.line)
                self.symbol_table.insert(func.name, symbol)
        
        for func in node.functions:
            self.visit_Function(func)
            
    def visit_Function(self, node):
        old_function = self.current_function
        self.current_function = node

        func_scope = SymbolTable(self.symbol_table)
        old_table = self.symbol_table
        self.symbol_table = func_scope

        for param in node.params:
            symbol = Symbol(param.name, 'variable', param.param_type, initialized=True, line=param.line)
            self.symbol_table.insert(param.name, symbol)

        for stmt in (node.body.statements if hasattr(node.body, 'statements') else 
                    (node.body if isinstance(node.body, list) else [node.body])):
            if isinstance(stmt, Function):
                params = [(p.name, p.param_type) for p in stmt.params]
                symbol = Symbol(stmt.name, 'function', params=params, return_type=stmt.return_type, line=stmt.line)
                self.symbol_table.insert(stmt.name, symbol)

        if hasattr(node.body, 'statements'):
            for stmt in node.body.statements:
                self.visit(stmt)
        elif isinstance(node.body, list):
            for stmt in node.body:
                self.visit(stmt)
        else:
            self.visit(node.body)

        self.symbol_table = old_table
        self.current_function = old_function


    def visit_VarDeclaration(self, node):
        """Visit a variable declaration node"""
        if self.symbol_table.lookup_current_scope(node.name):
            self.add_error(f"variable '{node.name}' is already defined", node.line)
        else:
            symbol = Symbol(node.name, 'variable', node.var_type, initialized=False, line=node.line)
            self.symbol_table.insert(node.name, symbol)

    def visit_Assignment(self, node):
        """Visit an assignment node"""
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
        """Visit a function call node"""
        for arg in node.args:
            self.visit(arg)

        if node.name in ['print', 'list', 'length', 'scan']:
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
        """Handle built-in functions"""
        if node.name == 'print': 
            return 'null'
        elif node.name == 'list': 
            return 'vector'
        elif node.name == 'length': 
            return 'int'
        elif node.name == 'scan':   
            return 'int'
        return None
    
    def visit_Return(self, node):
        """Visit a return statement"""
        if not self.current_function:
            self.add_error("return statement outside of function", node.line)
            return
        
        if node.value:
            self.visit(node.value)

        expected_type = self.current_function.return_type
        actual_type = 'null' if node.value is None else self.get_expression_type(node.value)
        
        if actual_type and expected_type != actual_type:
            self.add_error(
                f"function '{self.current_function.name}': wrong return type. expected '{expected_type}' but got '{actual_type}'",
                node.line
            )
            
    def visit_For(self, node):
        """Visit a for loop"""
        var_symbol = self.symbol_table.lookup(node.var)
        if not var_symbol:
            symbol = Symbol(node.var, 'variable', 'int', initialized=True, line=node.line)
            self.symbol_table.insert(node.var, symbol)
        else:
            var_symbol.initialized = True

        self.visit(node.start)
        self.visit(node.end)

        start_type = self.get_expression_type(node.start)
        end_type = self.get_expression_type(node.end)

        if start_type != 'int' or end_type != 'int':
            self.add_error(f"function '{self.current_function.name}': loop range must be of type 'int'", node.line)

        if hasattr(node.body, 'statements'):
            for stmt in node.body.statements:
                self.visit(stmt)
        elif isinstance(node.body, list):
            for stmt in node.body:
                self.visit(stmt)
        else:
            self.visit(node.body)


    def visit_Identifier(self, node):
        """Visit an identifier node"""
        var_symbol = self.symbol_table.lookup(node.name)
        if not var_symbol:
            self.add_error(f"function '{self.current_function.name}': variable '{node.name}' is not defined", node.line)
        elif not var_symbol.initialized:
            self.add_error(f"function '{self.current_function.name}': Variable '{node.name}' is used before being assigned", node.line)

    def visit_TernaryOp(self, node):
        """Visit a ternary operator node"""
        self.visit(node.condition)
        self.visit(node.true_expr)
        self.visit(node.false_expr)
        
        cond_type = self.get_expression_type(node.condition)
        if cond_type and cond_type != 'bool':
            self.add_error(f"ternary operator condition must be boolean, got '{cond_type}'", node.line)

    def get_expression_type(self, node):
        """Get the type of an expression"""
        if isinstance(node, Number): 
            return 'int'
        elif isinstance(node, String): 
            return 'str'
        elif isinstance(node, Boolean): 
            return 'bool'
        elif isinstance(node, Identifier):
            symbol = self.symbol_table.lookup(node.name)
            return symbol.data_type if symbol else None
        elif isinstance(node, FunctionCall):
            if node.name == 'list': 
                return 'vector'
            elif node.name == 'length': 
                return 'int'
            elif node.name == 'print': 
                return 'null'
            elif node.name == 'scan':
                return 'int'
            else:
                func = self.symbol_table.lookup(node.name)
                return func.return_type if func else None
        elif isinstance(node, ArrayAccess): 
            return 'int'
        elif isinstance(node, BinaryOp):
            return 'bool' if node.op in ['==', '!=', '<', '>', '<=', '>=', '&&', '||'] else 'int'
        elif isinstance(node, ListCall): 
            return 'vector'
        elif isinstance(node, TernaryOp):
            t = self.get_expression_type(node.true_expr)
            f = self.get_expression_type(node.false_expr)
            return t if t == f else None
        return None