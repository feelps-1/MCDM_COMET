from dataclasses import dataclass

@dataclass
class LEDCircuit:
    source_voltage: float
    led_voltage: float
    led_current: float

class OhmsLawCalculator:

    @staticmethod
    def calculate_resistor(circuit:LEDCircuit) -> float:
        if circuit.source_voltage <= circuit.led_voltage:
            raise ValueError("The source voltage must be greater than the LED voltage.")
        
        if circuit.led_current <= 0:
            raise ValueError("The current must be greater than zero.")
        
        return (
            circuit.source_voltage - circuit.led_voltage
        ) / circuit.led_current
    
    @staticmethod
    def calculate_resistor_power(
        resistance: float,
        current: float
    ) -> float: 
        return (current ** 2) * resistance





