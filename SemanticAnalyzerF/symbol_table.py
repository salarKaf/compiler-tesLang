"""Symbol Table Implementation for TesLang Compiler"""

class SymbolTable:
    """Symbol table for managing variable and function scopes"""
    
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
        self.children = []
        if parent:
            parent.children.append(self)
    
    def insert(self, name, symbol_info):
        """Insert a symbol into the current scope"""
        self.symbols[name] = symbol_info
    
    def lookup(self, name):
        """Look up a symbol in current scope and parent scopes"""
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.lookup(name)
        return None
    
    def lookup_current_scope(self, name):
        """Look up a symbol only in the current scope"""
        return self.symbols.get(name)

class Symbol:
    """Represents a symbol (variable or function) in the symbol table"""
    
    def __init__(self, name, symbol_type, data_type=None, params=None, return_type=None, initialized=False, line=None):
        self.name = name
        self.symbol_type = symbol_type  
        self.data_type = data_type
        self.params = params or []
        self.return_type = return_type
        self.initialized = initialized
        self.line = line