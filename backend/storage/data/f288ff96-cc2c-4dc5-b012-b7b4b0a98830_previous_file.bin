from functools import wraps
from typing import List

# Decorator example
def debug(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with {args[1:]}, {kwargs}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result}")
        return result
    return wrapper

# Metaclass example
class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

# Base class
class Vehicle:
    def __init__(self, make, model):
        self.make = make
        self.model = model

    def start(self):
        return f"{self.make} {self.model} starting..."

# Derived class
class Car(Vehicle):
    def __init__(self, make, model, doors):
        super().__init__(make, model)
        self.doors = doors

    @debug
    def drive(self, speed):
        return f"Car driving at {speed} km/h"

# Derived class with multiple inheritance
class Electric:
    def __init__(self, battery_capacity):
        self.battery_capacity = battery_capacity

    def charge(self):
        return f"Charging battery of {self.battery_capacity} kWh"

class ElectricCar(Car, Electric):
    def __init__(self, make, model, doors, battery_capacity):
        Car.__init__(self, make, model, doors)
        Electric.__init__(self, battery_capacity)

    @property
    def full_specs(self):
        return f"{self.make} {self.model}, {self.doors} doors, {self.battery_capacity} kWh battery"

# Aggregation example
class Garage:
    def __init__(self):
        self.vehicles: List[Vehicle] = []

    def park_vehicle(self, vehicle: Vehicle):
        self.vehicles.append(vehicle)

    def list_vehicles(self):
        return [v.make + " " + v.model for v in self.vehicles]

# Singleton example
class Logger(metaclass=SingletonMeta):
    def __init__(self):
        self.logs = []

    @debug
    def log(self, message):
        self.logs.append(message)

# Operator overloading example
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

# Testing all
if __name__ == "__main__":
    tesla = ElectricCar("Tesla", "Model S", 4, 100)
    tesla.drive(120)
    tesla.charge()
    print(tesla.full_specs)

    garage = Garage()
    garage.park_vehicle(tesla)
    garage.park_vehicle(Car("Ford", "Mustang", 2))
    print(garage.list_vehicles())

    logger = Logger()
    logger.log("Test message 1")
    logger2 = Logger()
    logger2.log("Test message 2")
    print(logger.logs)  # should show both messages due to singleton

    p1 = Point(1, 2)
    p2 = Point(3, 4)
    print(p1 + p2)
