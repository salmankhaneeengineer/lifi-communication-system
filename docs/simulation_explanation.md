# LiFi Simulation Explanation

## Theory of Operation

The LiFi simulation models light-based data transmission between a transmitter and receiver. The key physical principles involved:

### 1. Inverse Square Law

Light intensity decreases with the square of the distance:

$$I \propto \frac{1}{d^2}$$

### 2. Angular Attenuation

Light intensity varies with angle following a modified cosine law:

$$I \propto \cos(\theta)^{1/p}$$

where $p$ is a power factor related to the LED beam width.

## Simulation Components

### LiFiChannel

Models the physical medium through which light travels, accounting for:
- Distance attenuation
- Angular attenuation
- Noise and interference

### LiFiTransmitter

Simulates the LED transmitter:
- Converts data to binary bits
- Controls signal timing
- Records transmission metadata

### LiFiReceiver

Simulates the photodetector:
- Detects light intensity changes
- Samples bits based on threshold
- Reconstructs the original message

## Performance Metrics

The simulation calculates:
- Character accuracy
- Bit Error Rate (BER)
- Signal strength
