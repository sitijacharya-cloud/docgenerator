# --- Simple Calculator Module ---
class Calculator:
    @staticmethod
    def add(a, b):
        return a + b
    
    @staticmethod
    def subtract(a, b):
        return a - b
    
    @staticmethod
    def multiply(a, b):
        return a * b
    
    @staticmethod
    def divide(a, b):
        if b == 0:
            return "Error: Division by zero"
        return a / b


# Example usage
print("Add:", Calculator.add(10, 5))
print("Subtract:", Calculator.subtract(10, 5))
print("Multiply:", Calculator.multiply(10, 5))
print("Divide:", Calculator.divide(10, 5))
