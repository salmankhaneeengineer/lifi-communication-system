# Basic Angle Test Example

This example demonstrates how to run a basic angle test with the LiFi simulation.

## Setup

```python
# Import the simulation
from src.lifi_simulation import LiFiSimulator

# Create a simulator with default parameters
simulator = LiFiSimulator(
    ambient_noise=0.05,
    interference=0.02,
    natural_disturbance=0.01,
    led_beam_width=120
)

# Run an angle test
results = simulator.run_angle_test(
    message="Hello LiFi",
    start_angle=0,
    end_angle=180,
    angle_step=15,
    distance=10,
    threshold=0.5
)

# Save results to CSV
simulator.save_results_to_csv(results, "angle_test")
