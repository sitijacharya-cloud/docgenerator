class Calculator:
    """A simple calculator."""
    
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b

class DataProcessor:
    """Process data."""
    
    def __init__(self):
        self.calc = Calculator()
    
    def process(self, data):
        return self.calc.add(data, 10)