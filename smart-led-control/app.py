from ohms_law import LEDCircuit, OhmsLawCalculator

def main():
    try:
        circuit = LEDCircuit(
            source_voltage=5.0,
            led_voltage=2.0,
            led_current=0.02
        )

        resistance = OhmsLawCalculator.calculate_resistor(circuit)
        power = OhmsLawCalculator.calculate_resistor_power(
            resistance,
            circuit.led_current
        )

        print(f"Required Resistance: {resistance:.2f} Ω")
        print(f"Power Dissipation {power:.4f} W")

    except ValueError as error:
        print(f"Error: {error}")

if __name__ == "__main__":
    main()