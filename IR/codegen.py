# codegen.py - Fixed version for TSVM compatibility
"""
TesLang Compiler - Step 3: Code Generation (Fixed for TSVM)
Generates intermediate code for tsvm virtual machine
"""

from Parser.parser import *
import sys

class Register:
    """Register allocation and management"""
    def __init__(self):
        self.current = 0
        self.max_used = 0
        self.reserved = {'r0'}  # r0 is reserved for return values
        
        
    def allocate(self):
        """Allocate a new register, skipping reserved ones"""
        while True:
            reg = f"r{self.current}"
            self.current += 1
            if reg not in self.reserved:
                self.reserved.add(reg)  # Mark as used
                self.max_used = max(self.max_used, int(reg[1:]))
                return reg

    
    def get_current(self):
        """Get current register without allocating new one"""
        return f"r{self.current}"
    
    
    def reserve(self, reg):
        self.reserved.add(reg)

    
    def reset_temp(self):
        """Reset to a safe temporary register state"""
        self.current = 0
        self.reserved = {'r0'}  # Keep only r0 reserved

class CodeGenerator:
    def __init__(self):
        self.code = []
        self.register_manager = Register()
        self.current_function = None
        self.function_vars = {}  # Maps variable names to registers for current function
        self.function_params = {}  # Maps parameter names to registers
        self.label_counter = 0
        
    def generate_label(self, prefix="L"):
        """Generate a unique label"""
        label = f"{prefix}{self.label_counter}"
        self.label_counter += 1
        return label
    
    def emit(self, instruction):
        """Emit an instruction to the code list"""
        self.code.append(instruction)
    
    def emit_comment(self, comment):
        """Emit a comment"""
        self.emit(f"# {comment}")
    
    def generate(self, ast):
        """Main code generation entry point"""
        self.visit(ast)
        return '\n'.join(self.code)
    
    def visit(self, node):
        """Generic visit method"""
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        """Default visit method"""
        pass
    
    def visit_Program(self, node):
        """Generate code for the entire program"""
        # Generate code for all functions
        for function in node.functions:
            self.visit_Function(function)
    
    def visit_Function(self, node):
        """Generate code for a function"""
        self.current_function = node.name
        self.function_vars = {}
        self.function_params = {}
        self.register_manager.reset_temp()
        
        # Emit function header
        self.emit(f"proc {node.name}")
        
        # Generate parameter mapping comment
        if node.params:
            param_comments = []
            for i, param in enumerate(node.params):
                reg = f"r{i + 1}"  # ✅ use r1, r2, r3 for arguments
                self.function_params[param.name] = reg
                param_comments.append(f"{param.name} => {reg}")
                self.register_manager.reserve(reg)
                self.register_manager.current = max(self.register_manager.current, i + 2)

            
            self.emit_comment(f"Parameters: {', '.join(param_comments)}")
        
        # Generate code for function body
        for stmt in node.body:
            self.visit(stmt)
        
        # Ensure function ends with ret
        if not self.code or not self.code[-1].strip().endswith('ret'):
            if node.return_type == 'null':
                self.emit("mov r0, 0")
            self.emit("ret")
        
        self.emit("")  # Empty line between functions
    
    def visit_VarDeclaration(self, node):
        """Generate code for variable declaration"""
        # Only allocate a register if the variable doesn't already exist
        if node.name not in self.function_vars and node.name not in self.function_params:
            reg = self.register_manager.allocate()
            self.function_vars[node.name] = reg
            self.emit_comment(f"Declare {node.name} in {reg}")
        else:
            # Variable already exists (either as parameter or previously declared)
            if node.name in self.function_params:
                reg = self.function_params[node.name]
            else:
                reg = self.function_vars[node.name]
            self.emit_comment(f"Variable {node.name} already in {reg}")
    
    def visit_Assignment(self, node):
        """Generate code for assignment"""
        if isinstance(node.target, str):
            # Simple variable assignment
            value_reg = self.visit(node.value)
            
            # Get or allocate register for target variable
            if node.target in self.function_params:
                target_reg = self.function_params[node.target]
            elif node.target in self.function_vars:
                target_reg = self.function_vars[node.target]
            else:
                target_reg = self.register_manager.allocate()
                self.function_vars[node.target] = target_reg
            
            if value_reg != target_reg:
                self.emit(f"mov {target_reg}, {value_reg}")
        
        elif isinstance(node.target, ArrayAccess):
            # Array element assignment: A[index] = value
            array_name = node.target.array
            index_reg = self.visit(node.target.index)
            value_reg = self.visit(node.value)
            
            if array_name in self.function_vars:
                array_reg = self.function_vars[array_name]
            elif array_name in self.function_params:
                array_reg = self.function_params[array_name]
            else:
                # This should not happen if semantic analysis passed
                array_reg = self.register_manager.allocate()
                self.function_vars[array_name] = array_reg
            
            # Calculate memory address: array_base + index * 4 (assuming 4 bytes per element)
            addr_reg = self.register_manager.allocate()
            four_reg = self.register_manager.allocate()
            self.emit(f"mov {four_reg}, 4")
            self.emit(f"mul {addr_reg}, {index_reg}, {four_reg}")
            self.emit(f"add {addr_reg}, {array_reg}, {addr_reg}")
            self.emit(f"st {value_reg}, {addr_reg}")
    
    def visit_FunctionCall(self, node):
        """Generate code for function call"""
        if node.name == 'scan':
            # Built-in scan function -> use iget
            result_reg = self.register_manager.allocate()
            self.emit(f"call iget, {result_reg}")
            return result_reg
        
        elif node.name == 'print':
            # Built-in print function -> use iput
            if node.args:
                arg_reg = self.visit(node.args[0])
                self.emit(f"call iput, {arg_reg}")
            return None
        
        elif node.name == 'list':
            # Built-in list creation -> use mem
            if node.args:
                size_reg = self.visit(node.args[0])
                result_reg = self.register_manager.allocate()
                # Multiply size by 4 to get bytes (assuming 4 bytes per element)
                four_reg = self.register_manager.allocate()
                bytes_reg = self.register_manager.allocate()
                self.emit(f"mov {four_reg}, 4")
                self.emit(f"mul {bytes_reg}, {size_reg}, {four_reg}")
                self.emit(f"call mem, {result_reg}, {bytes_reg}")
                return result_reg
            return None
        
        elif node.name == 'length':
            # Built-in length function (not directly supported in TSVM)
            if node.args:
                array_reg = self.visit(node.args[0])
                result_reg = self.register_manager.allocate()
                # This would need custom implementation
                self.emit(f"# length function not supported in basic TSVM")
                self.emit(f"mov {result_reg}, 0")
                return result_reg
            return None
        
        else:
            # User-defined function call
            arg_regs = []
            for arg in node.args:
                arg_reg = self.visit(arg)
                arg_regs.append(arg_reg)
            
            result_reg = self.register_manager.allocate()
            
            # TSVM calling convention: call func, result_reg, arg1, arg2, ...
            if arg_regs:
                args_str = ', '.join(arg_regs)
                self.emit(f"call {node.name}, {result_reg}, {args_str}")
            else:
                self.emit(f"call {node.name}, {result_reg}")
            
            return result_reg
        
    def visit_Return(self, node):
        """Generate code for return statement"""
        
        if node.value:
            value_reg = self.visit(node.value)
            # Always move the return value to r0 if it's not already there
            if value_reg != "r0":
                self.emit(f"mov r0, {value_reg}")
        else:
            # No return value, set r0 to 0
            self.emit("mov r0, 0")
        self.emit("ret")

    
    def visit_BinaryOp(self, node):
        """Generate code for binary operations"""
        left_reg = self.visit(node.left)
        right_reg = self.visit(node.right)
        result_reg = self.register_manager.allocate()
        
        # Map operators to tsvm instructions
        if node.op == '+':
            self.emit(f"add {result_reg}, {left_reg}, {right_reg}")
        elif node.op == '-':
            self.emit(f"sub {result_reg}, {left_reg}, {right_reg}")
        elif node.op == '*':
            self.emit(f"mul {result_reg}, {left_reg}, {right_reg}")
        elif node.op == '/':
            self.emit(f"div {result_reg}, {left_reg}, {right_reg}")
        elif node.op == '%':
            self.emit(f"mod {result_reg}, {left_reg}, {right_reg}")
        elif node.op == '<':
            self.emit(f"cmp< {result_reg}, {left_reg}, {right_reg}")
        elif node.op == '>':
            self.emit(f"cmp> {result_reg}, {left_reg}, {right_reg}")
        elif node.op == '<=':
            self.emit(f"cmp<= {result_reg}, {left_reg}, {right_reg}")
        elif node.op == '>=':
            self.emit(f"cmp>= {result_reg}, {left_reg}, {right_reg}")
        elif node.op == '==':
            self.emit(f"cmp== {result_reg}, {left_reg}, {right_reg}")
        else:
            # Fallback for unsupported operators
            self.emit(f"# Unsupported operator: {node.op}")
            self.emit(f"mov {result_reg}, {left_reg}")
        
        return result_reg
    
    def visit_UnaryOp(self, node):
        """Generate code for unary operations"""
        operand_reg = self.visit(node.operand)
        result_reg = self.register_manager.allocate()
        
        if node.op == '-':
            # Negate: multiply by -1
            neg_one_reg = self.register_manager.allocate()
            self.emit(f"mov {neg_one_reg}, -1")
            self.emit(f"mul {result_reg}, {operand_reg}, {neg_one_reg}")
        elif node.op == '!':
            # Logical NOT (not directly supported, use comparison)
            zero_reg = self.register_manager.allocate()
            self.emit(f"mov {zero_reg}, 0")
            self.emit(f"cmp== {result_reg}, {operand_reg}, {zero_reg}")
        else:
            self.emit(f"mov {result_reg}, {operand_reg}")
        
        return result_reg
    
    def visit_Identifier(self, node):
        """Generate code for identifier"""
        if node.name in self.function_params:
            return self.function_params[node.name]
        elif node.name in self.function_vars:
            return self.function_vars[node.name]
        else:
            # This should not happen if semantic analysis passed
            reg = self.register_manager.allocate()
            self.function_vars[node.name] = reg
            return reg
    
    def visit_Number(self, node):
        """Generate code for number literal"""
        reg = self.register_manager.allocate()
        self.emit(f"mov {reg}, {node.value}")
        return reg
    
    def visit_String(self, node):
        """Generate code for string literal"""
        reg = self.register_manager.allocate()
        self.emit(f"mov {reg}, \"{node.value}\"")
        return reg
    
    def visit_Boolean(self, node):
        """Generate code for boolean literal"""
        reg = self.register_manager.allocate()
        value = 1 if node.value == 'true' else 0
        self.emit(f"mov {reg}, {value}")
        return reg
    
    def visit_ArrayAccess(self, node):
        """Generate code for array access"""
        array_name = node.array
        index_reg = self.visit(node.index)
        
        if array_name in self.function_vars:
            array_reg = self.function_vars[array_name]
        elif array_name in self.function_params:
            array_reg = self.function_params[array_name]
        else:
            array_reg = self.register_manager.allocate()
            self.function_vars[array_name] = array_reg
        
        # Calculate memory address: array_base + index * 4 (assuming 4 bytes per element)
        addr_reg = self.register_manager.allocate()
        four_reg = self.register_manager.allocate()
        result_reg = self.register_manager.allocate()
        
        self.emit(f"mov {four_reg}, 4")
        self.emit(f"mul {addr_reg}, {index_reg}, {four_reg}")
        self.emit(f"add {addr_reg}, {array_reg}, {addr_reg}")
        self.emit(f"ld {result_reg}, {addr_reg}")
        return result_reg
    
    def visit_If(self, node):
        """Generate code for if statement"""
        condition_reg = self.visit(node.condition)
        
        else_label = self.generate_label("else")
        end_label = self.generate_label("endif")
        
        # Jump to else if condition is false (0)
        self.emit(f"jz {condition_reg}, {else_label}")
        
        # Generate then block
        for stmt in node.then_stmt:
            self.visit(stmt)
        
        if node.else_stmt:
            self.emit(f"jmp {end_label}")
            self.emit(f"{else_label}:")
            for stmt in node.else_stmt:
                self.visit(stmt)
            self.emit(f"{end_label}:")
        else:
            self.emit(f"{else_label}:")
    
    def visit_While(self, node):
        """Generate code for while loop"""
        loop_start = self.generate_label("while_start")
        loop_end = self.generate_label("while_end")
        
        self.emit(f"{loop_start}:")
        condition_reg = self.visit(node.condition)
        self.emit(f"jz {condition_reg}, {loop_end}")
        
        for stmt in node.body:
            self.visit(stmt)
        
        self.emit(f"jmp {loop_start}")
        self.emit(f"{loop_end}:")
    
    def visit_For(self, node):
        """Generate code for for loop"""
        # Initialize loop variable
        start_reg = self.visit(node.start)
        end_reg = self.visit(node.end)
        
        # Get or allocate register for loop variable
        if node.var in self.function_vars:
            var_reg = self.function_vars[node.var]
        else:
            var_reg = self.register_manager.allocate()
            self.function_vars[node.var] = var_reg
        
        self.emit(f"mov {var_reg}, {start_reg}")
        
        loop_start = self.generate_label("for_start")
        loop_end = self.generate_label("for_end")
        
        self.emit(f"{loop_start}:")
        
        # Check condition: var < end
        condition_reg = self.register_manager.allocate()
        self.emit(f"cmp< {condition_reg}, {var_reg}, {end_reg}")
        self.emit(f"jz {condition_reg}, {loop_end}")
        
        # Generate loop body
        for stmt in node.body:
            self.visit(stmt)
        
        # Increment loop variable
        one_reg = self.register_manager.allocate()
        self.emit(f"mov {one_reg}, 1")
        self.emit(f"add {var_reg}, {var_reg}, {one_reg}")
        
        self.emit(f"jmp {loop_start}")
        self.emit(f"{loop_end}:")


def generate_code(ast):
    """Main function to generate intermediate code"""
    generator = CodeGenerator()
    return generator.generate(ast)


# Modified main compiler function to include code generation
def compile_teslang_with_codegen(code):
    """Compile TesLang code and generate intermediate code"""
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
            return None, errors
        
        # Perform semantic analysis
        analyzer = SemanticAnalyzer()
        semantic_errors = analyzer.analyze(ast)
        
        if semantic_errors:
            return None, semantic_errors
        
        # Generate intermediate code
        intermediate_code = generate_code(ast)
        return intermediate_code, []
        
    except Exception as e:
        errors.append(f"Compiler error: {str(e)}")
        return None, errors


# Test with the provided example (fixed)
if __name__ == "__main__":
    # Test with corrected example
    test_code = '''funk add(a as int, b as int) <int>
{
    result :: int;
    result = a + b;
    return result;
}

funk main() <int>
{
    a :: int;
    b :: int;
    
    a = scan();
    b = scan();
    
    print(add(a, b));
    return 0;
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
        print("Expected behavior: Input 7, 7 -> Output 14")
        print("If getting 0 or 7, check register allocation logic")