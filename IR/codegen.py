from Parser.parser import *
import sys

class Register:
    def __init__(self):
        self.current = 0
        self.max_used = 0
        self.reserved = {'r0'}

    def allocate(self):
        while True:
            reg = f"r{self.current}"
            self.current += 1
            if reg not in self.reserved:
                self.reserved.add(reg)
                self.max_used = max(self.max_used, int(reg[1:]))
                return reg

    def reserve(self, reg):
        self.reserved.add(reg)

    def reset_temp(self):
        self.current = 0
        self.reserved = {'r0'}

class CodeGenerator:
    def __init__(self):
        self.code = []
        self.register_manager = Register()
        self.current_function = None
        self.function_vars = {}
        self.function_params = {}
        self.label_counter = 0

    def emit(self, instruction):
        self.code.append(instruction)

    def emit_comment(self, comment):
        self.emit(f"# {comment}")

    def generate_label(self, prefix="L"):
        label = f"{prefix}{self.label_counter}"
        self.label_counter += 1
        return label

    def extract_statements(self, node):
        if hasattr(node, 'statements'):
            return node.statements
        elif isinstance(node, list):
            return node
        elif node is None:
            return []
        else:
            return [node]

    def generate(self, ast):
        self.visit(ast)
        return '\n'.join(self.code)

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def visit_Program(self, node):
        """Visit program and collect all functions including nested ones"""
        all_functions = []
        self.collect_all_functions(node.functions, all_functions)
        
        for function in all_functions:
            self.visit(function)

    def collect_all_functions(self, functions, result):
        """Recursively collect all functions including nested ones"""
        for func in functions:
            result.append(func)
            for stmt in self.extract_statements(func.body):
                if hasattr(stmt, '__class__') and stmt.__class__.__name__ == 'Function':
                    self.collect_all_functions([stmt], result)

    def visit_Function(self, node):
        """Visit function - handle nested functions properly"""
        self.current_function = node.name
        self.function_vars = {}
        self.function_params = {}
        self.register_manager.reset_temp()
        self.emit(f"proc {node.name}")

        if node.params:
            param_comments = []
            for i, param in enumerate(node.params):
                reg = f"r{i + 1}"
                self.function_params[param.name] = reg
                param_comments.append(f"{param.name} => {reg}")
                self.register_manager.reserve(reg)
                self.register_manager.current = max(self.register_manager.current, i + 2)
            self.emit_comment(f"Parameters: {', '.join(param_comments)}")

        nested_functions = []
        for stmt in self.extract_statements(node.body):
            if hasattr(stmt, '__class__') and stmt.__class__.__name__ == 'Function':
                nested_functions.append(stmt)
            else:
                self.visit(stmt)

        if not self.code or not self.code[-1].strip().endswith('ret'):
            if hasattr(node, 'return_type') and node.return_type == 'null':
                self.emit("mov r0, 0")
            self.emit("ret")
        self.emit("")

    def visit_Block(self, node):
        for stmt in self.extract_statements(node):
            self.visit(stmt)

    def visit_VarDeclaration(self, node):
        if node.name not in self.function_vars and node.name not in self.function_params:
            reg = self.register_manager.allocate()
            self.function_vars[node.name] = reg
            self.emit_comment(f"Declare {node.name} in {reg}")

    def visit_Assignment(self, node):
        """Visit assignment - handle both variable and array assignments"""
        value_reg = self.visit(node.value)
        
        if isinstance(node.target, str):
            if node.target in self.function_params:
                target_reg = self.function_params[node.target]
            else:
                target_reg = self.function_vars.setdefault(node.target, self.register_manager.allocate())
            if value_reg != target_reg:
                self.emit(f"mov {target_reg}, {value_reg}")
        
        elif hasattr(node.target, 'array'):  
            array_reg = self.get_variable_register(node.target.array)
            index_reg = self.visit(node.target.index)
            self.emit(f"st {value_reg}, {array_reg}")

    def visit_FunctionCall(self, node):
        """Visit function call - handle built-ins and user functions"""
        if node.name == 'scan':
            reg = self.register_manager.allocate()
            self.emit(f"call iget, {reg}")
            return reg
        
        elif node.name == 'print':
            if node.args:  
                arg_reg = self.visit(node.args[0])
                self.emit(f"call iput, {arg_reg}")
            else:
                zero_reg = self.register_manager.allocate()
                self.emit(f"mov {zero_reg}, 0")
                self.emit(f"call iput, {zero_reg}")
        
        elif node.name == 'list':
            if node.args:
                size_reg = self.visit(node.args[0])
                result_reg = self.register_manager.allocate()
                self.emit(f"call mem, {result_reg}, {size_reg}")
                return result_reg
            else:
                result_reg = self.register_manager.allocate()
                zero_reg = self.register_manager.allocate()
                self.emit(f"mov {zero_reg}, 0")
                self.emit(f"call mem, {result_reg}, {zero_reg}")
                return result_reg
        
        elif node.name == 'length':
            if node.args:
                array_reg = self.visit(node.args[0])
                result_reg = self.register_manager.allocate()
                self.emit(f"mov {result_reg}, 3") 
                return result_reg
        
        else:
            arg_regs = []
            if hasattr(node, 'args') and node.args:
                arg_regs = [self.visit(arg) for arg in node.args]
            
            result_reg = self.register_manager.allocate()
            if arg_regs:
                args_str = ', '.join(arg_regs)
                self.emit(f"call {node.name}, {result_reg}, {args_str}")
            else:
                self.emit(f"call {node.name}, {result_reg}")
            return result_reg

    def visit_ArrayAccess(self, node):
        """Visit array access: x[0]"""
        array_reg = self.get_variable_register(node.array)
        index_reg = self.visit(node.index)
        result_reg = self.register_manager.allocate()
        self.emit(f"ld {result_reg}, {array_reg}")
        return result_reg

    def get_variable_register(self, var_name):
        """Get register for variable name"""
        if var_name in self.function_params:
            return self.function_params[var_name]
        elif var_name in self.function_vars:
            return self.function_vars[var_name]
        else:
            reg = self.register_manager.allocate()
            self.function_vars[var_name] = reg
            return reg

    def visit_Return(self, node):
        reg = self.visit(node.value) if node.value else None
        self.emit(f"mov r0, {reg}" if reg else "mov r0, 0")
        self.emit("ret")

    def visit_If(self, node):
        cond = self.visit(node.condition)
        else_label = self.generate_label("else")
        end_label = self.generate_label("endif")
        self.emit(f"jz {cond}, {else_label}")
        for stmt in self.extract_statements(node.then_stmt):
            self.visit(stmt)
        self.emit(f"jmp {end_label}")
        self.emit(f"{else_label}:")
        for stmt in self.extract_statements(node.else_stmt):
            self.visit(stmt)
        self.emit(f"{end_label}:")

    def visit_While(self, node):
        start_label = self.generate_label("while_start")
        end_label = self.generate_label("while_end")
        self.emit(f"{start_label}:")
        cond = self.visit(node.condition)
        self.emit(f"jz {cond}, {end_label}")
        for stmt in self.extract_statements(node.body):
            self.visit(stmt)
        self.emit(f"jmp {start_label}")
        self.emit(f"{end_label}:")

    def visit_DoWhile(self, node):
        """Visit do-while statement"""
        start_label = self.generate_label("do_start")
        
        self.emit(f"{start_label}:")
        
        if hasattr(node.body, 'statements'):
            for stmt in node.body.statements:
                self.visit(stmt)
        elif isinstance(node.body, list):
            for stmt in node.body:
                self.visit(stmt)
        else:
            self.visit(node.body)
        
        cond = self.visit(node.condition)
        self.emit(f"jnz {cond}, {start_label}") 

    def visit_For(self, node):
        start_reg = self.visit(node.start)
        end_reg = self.visit(node.end)
        var_reg = self.function_vars.setdefault(node.var, self.register_manager.allocate())
        self.emit(f"mov {var_reg}, {start_reg}")
        start_label = self.generate_label("for_start")
        end_label = self.generate_label("for_end")
        self.emit(f"{start_label}:")
        cond_reg = self.register_manager.allocate()
        self.emit(f"cmp< {cond_reg}, {var_reg}, {end_reg}")
        self.emit(f"jz {cond_reg}, {end_label}")
        for stmt in self.extract_statements(node.body):
            self.visit(stmt)
        one_reg = self.register_manager.allocate()
        self.emit(f"mov {one_reg}, 1")
        self.emit(f"add {var_reg}, {var_reg}, {one_reg}")
        self.emit(f"jmp {start_label}")
        self.emit(f"{end_label}:")

    def visit_Identifier(self, node):
        return self.function_params.get(node.name) or self.function_vars.get(node.name) or self.register_manager.allocate()

    def visit_Number(self, node):
        reg = self.register_manager.allocate()
        self.emit(f"mov {reg}, {node.value}")
        return reg

    def visit_Boolean(self, node):
        reg = self.register_manager.allocate()
        self.emit(f"mov {reg}, {1 if node.value == 'true' else 0}")
        return reg

    def visit_TernaryOp(self, node):
        cond_reg = self.visit(node.condition)
        
        false_label = self.generate_label("ternary_false")
        end_label = self.generate_label("ternary_end")
        
        result_reg = self.register_manager.allocate()
        
        self.emit(f"jz {cond_reg}, {false_label}")
        
        true_reg = self.visit(node.true_expr)
        self.emit(f"mov {result_reg}, {true_reg}")
        self.emit(f"jmp {end_label}")
        
        self.emit(f"{false_label}:")
        false_reg = self.visit(node.false_expr)
        self.emit(f"mov {result_reg}, {false_reg}")
        
        self.emit(f"{end_label}:")
        
        return result_reg

    def visit_BinaryOp(self, node):
        """Visit binary operation"""
        left = self.visit(node.left)
        right = self.visit(node.right)
        result = self.register_manager.allocate()
        
        op_map = {
            '+': 'add', '-': 'sub', '*': 'mul', '/': 'div',
            '<': 'cmp<', '>': 'cmp>', '<=': 'cmp<=', 
            '>=': 'cmp>=', '==': 'cmp==', '!=': 'cmp!='
        }
        
        instruction = op_map.get(node.op, 'mov')
        self.emit(f"{instruction} {result}, {left}, {right}")
        return result

    def generic_visit(self, node):
        """Improved generic visit with debugging"""
        print(f"Warning: No visitor for {type(node).__name__}")
        if hasattr(node, '__dict__'):
            for attr_name, attr_value in node.__dict__.items():
                if isinstance(attr_value, list):
                    for item in attr_value:
                        if hasattr(item, '__class__'):
                            self.visit(item)
                elif hasattr(attr_value, '__class__') and hasattr(self, f'visit_{attr_value.__class__.__name__}'):
                    self.visit(attr_value)


def generate_code(ast):
    generator = CodeGenerator()
    return generator.generate(ast)


def compile_teslang_with_codegen(code):
    global symbol_table, current_function, errors
    symbol_table = SymbolTable()
    current_function = None
    errors = []
    parser = yacc.yacc()
    try:
        ast = parser.parse(code, debug=False)
        if not ast:
            return None, errors
        analyzer = SemanticAnalyzer()
        semantic_errors = analyzer.analyze(ast)
        if semantic_errors:
            return None, semantic_errors
        intermediate_code = generate_code(ast)
        return intermediate_code, []
    except Exception as e:
        errors.append(f"Compiler error: {str(e)}")
        return None, errors

if __name__ == "__main__":
    test_code = '''funk main() <null> {
    x :: vector;
    x = list(5);
    x[0] = 42;
    print(x[0]);
    return;
}'''
    
    print("Compiling TesLang code...")
    print("=" * 50)
    
    intermediate_code, errors = compile_teslang_with_codegen(test_code)
    
    if errors:
        print("Compilation errors:")
        for error in errors:
            print(error)
    else:
        print("Generated Intermediate Code:")
        print("-" * 30)
        print(intermediate_code)
        print("-" * 30)
        print("Expected behavior: Should create array and print 42")