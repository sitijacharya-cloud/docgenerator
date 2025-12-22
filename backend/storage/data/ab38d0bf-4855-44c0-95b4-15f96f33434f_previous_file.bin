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

# Removed: SingletonMeta
# Removed: Logger

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

    # Removed: drive function
    def stop(self):
        return f"{self.make} {self.model} stopped."

    def honk(self):
        return "Beep beep!"

    @debug
    def park(self):
        return f"{self.make} {self.model} parked."

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

    # Added 2 new functions
    def eco_mode(self):
        return f"{self.make} {self.model} is now in eco mode."

    def sport_mode(self):
        return f"{self.make} {self.model} is now in sport mode."

# Aggregation example
class Garage:
    def __init__(self):
        self.vehicles: List[Vehicle] = []

    def park_vehicle(self, vehicle: Vehicle):
        self.vehicles.append(vehicle)

    def list_vehicles(self):
        return [v.make + " " + v.model for v in self.vehicles]

# Added 2 new classes
class Motorcycle(Vehicle):
    def __init__(self, make, model, cc):
        super().__init__(make, model)
        self.cc = cc

    def rev_engine(self):
        return f"{self.make} {self.model} engine revving!"

class Truck(Vehicle):
    def __init__(self, make, model, capacity):
        super().__init__(make, model)
        self.capacity = capacity

    def load_cargo(self, weight):
        return f"Loading {weight} tons into {self.make} {self.model}"

# Removed: Point

# Testing all
if __name__ == "__main__":
    tesla = ElectricCar("Tesla", "Model S", 4, 100)
    tesla.park()
    tesla.charge()
    print(tesla.full_specs)
    print(tesla.eco_mode())
    print(tesla.sport_mode())

    garage = Garage()
    garage.park_vehicle(tesla)
    garage.park_vehicle(Car("Ford", "Mustang", 2))
    garage.park_vehicle(Motorcycle("Yamaha", "R1", 1000))
    garage.park_vehicle(Truck("Volvo", "FH", 20))
    print(garage.list_vehicles())
