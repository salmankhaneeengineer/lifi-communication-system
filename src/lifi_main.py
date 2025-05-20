import time
import random
import csv
import os
import math
from datetime import datetime

class LiFiChannel:
    """Simulates the light transmission channel between transmitter and receiver"""
    
    def __init__(self, distance=1.0, angle=0, noise_level=0.0, interference=0.0, 
                 natural_disturbance=0.0, led_beam_width=120):
        self.distance = max(0.1, distance)  # Ensure distance is never zero, minimum 0.1cm
        self.angle = angle  # angle in degrees (0 to 180)
        self.noise_level = noise_level  # 0.0 to 1.0
        self.interference = interference  # random interference (0.0 to 1.0)
        self.natural_disturbance = natural_disturbance  # environmental light fluctuation
        self.led_beam_width = led_beam_width  # LED beam width in degrees
        self.transmission_history = []  # Store signal values for analysis
        
    def transmit(self, signal):
        """Simulate signal transmission through the channel with directional effects"""
        # Calculate signal attenuation based on distance (inverse square law)
        # Ensure distance is never zero to prevent division by zero
        safe_distance = max(0.1, self.distance)
        distance_attenuation = 10.0 / (safe_distance ** 2)
        
        # Calculate angular attenuation using a more realistic LED beam pattern
        # This uses a modified cosine model that allows wider beam angles
        angle_rad = math.radians(self.angle)
        half_beam_width = math.radians(self.led_beam_width / 2)
        
        if self.angle <= 90:
            # Front half: use cosine with power adjustment based on beam width
            power_factor = max(0.1, 2.0 / self.led_beam_width * 90)  # Prevent division by zero
            angular_attenuation = math.cos(angle_rad) ** (1/power_factor)
        else:
            # Back half: minimal leakage
            angular_attenuation = 0.05 * math.cos((angle_rad - math.pi) / 2)
        
        # Ensure minimal signal at extreme angles
        angular_attenuation = max(0.01, angular_attenuation)
            
        # Combined attenuation
        attenuation = distance_attenuation * angular_attenuation
        
        # Apply noise
        if random.random() < self.noise_level:
            # Flip the signal randomly based on noise level
            signal = 1 - signal
            
        # Add random interference
        if random.random() < self.interference:
            # Reduce signal strength
            attenuation *= random.uniform(0.5, 0.9)
            
        # Add natural disturbance (light fluctuations)
        if self.natural_disturbance > 0:
            attenuation *= 1 + random.uniform(-self.natural_disturbance, self.natural_disturbance)
            
        # Calculate received signal (attenuated)
        received_signal = signal * attenuation
        
        # Record for analysis
        self.transmission_history.append(received_signal)
        
        # Return the received signal
        return received_signal


class LiFiTransmitter:
    """Simulates the LiFi transmitter based on the Arduino code"""
    
    def __init__(self, channel, led_pin=12, sampling_time=5):
        self.channel = channel
        self.led_pin = led_pin
        self.sampling_time = sampling_time
        self.led_state = False
        self.log_messages = []
        self.transmit_times = []
        self.transmitted_bits = []
        
    def log(self, message):
        """Log messages for debugging"""
        self.log_messages.append(f"TX: {message}")
        
    def transmit_byte(self, data_byte):
        """Simulate transmitting a byte through the LED"""
        # Start bit (LED LOW)
        self.led_state = False
        self.transmit_times.append(time.time())
        self.transmitted_bits.append(0)  # Start bit
        self.channel.transmit(0)
        time.sleep(self.sampling_time / 1000)  # Convert to seconds
        
        # Transmit 8 bits
        for i in range(8):
            bit_val = (data_byte >> i) & 0x01
            self.led_state = bool(bit_val)
            self.transmit_times.append(time.time())
            self.transmitted_bits.append(bit_val)
            self.channel.transmit(bit_val)
            time.sleep(self.sampling_time / 1000)
            
        # Stop bit (LED HIGH)
        self.led_state = True
        self.transmit_times.append(time.time())
        self.transmitted_bits.append(1)  # Stop bit
        self.channel.transmit(1)
        time.sleep(self.sampling_time / 1000)
        
    def transmit_string(self, text):
        """Transmit a string by sending each byte"""
        # Reset transmission records
        self.transmit_times = []
        self.transmitted_bits = []
        
        # Add handshake and end marker as in the original code
        full_text = "<~!" + text + "#"
        self.log(f"Transmitting: {full_text}")
        
        # Record start time
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Transmit each character
        for char in full_text:
            self.log(f"Transmitting byte: {ord(char)} ({char})")
            self.transmit_byte(ord(char))
            time.sleep(0.02)  # Small delay between characters
            
        # Return transmission metadata
        return {
            "start_time": start_time,
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "transmitted_data": full_text,
            "bit_timing": self.transmit_times
        }


class LiFiReceiver:
    """Simulates the LiFi receiver based on the Arduino code"""
    
    def __init__(self, channel, ldr_pin=3, sampling_time=5, threshold=0.5):
        self.channel = channel
        self.ldr_pin = ldr_pin
        self.sampling_time = sampling_time
        self.threshold = threshold
        self.received_data = ""
        self.handshake_received = False
        self.log_messages = []
        self.bit_errors = 0
        self.total_bits = 0
        self.receive_times = []
        self.received_bits = []
        self.register_values = []
        
    def log(self, message):
        """Log messages for debugging"""
        self.log_messages.append(f"RX: {message}")
        
    def get_ldr(self):
        """Simulate reading from the light sensor"""
        # Get the latest signal from the channel
        if self.channel.transmission_history:
            signal = self.channel.transmission_history[-1]
            # Record register value
            self.register_values.append(signal)
            # Convert to boolean based on threshold
            return signal < self.threshold
        return True
        
    def get_byte(self):
        """Receive a byte by sampling 8 bits"""
        data_byte = 0
        
        # Wait for some time to align with the transmitter timing
        time.sleep(self.sampling_time * 1.5 / 1000)
        
        # Sample 8 bits
        for i in range(8):
            # Get the bit value from the LDR
            bit_val = self.get_ldr()
            self.receive_times.append(time.time())
            self.received_bits.append(int(bit_val))
            
            # Set the corresponding bit in the byte
            data_byte |= (int(bit_val) << i)
            
            # Increment total bits
            self.total_bits += 1
            
            # Wait for the next bit
            time.sleep(self.sampling_time / 1000)
            
        return chr(data_byte)
        
    def receive_transmission(self, expected_message):
        """Receive a transmission and compare with expected message"""
        self.received_data = ""
        self.handshake_received = False
        self.bit_errors = 0
        self.total_bits = 0
        self.receive_times = []
        self.received_bits = []
        self.register_values = []
        buffer = ""
        
        # Start reception time
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Continue receiving while there is data
        attempt_counter = 0
        max_attempts = 1000  # To prevent infinite loops
        
        while attempt_counter < max_attempts:
            # Detect a valid transition (high to low)
            previous_state = True
            current_state = self.get_ldr()
            
            if not current_state and previous_state:
                # Received a valid transition, get a byte
                received_char = self.get_byte()
                
                if not self.handshake_received:
                    # Check for handshake
                    buffer += received_char
                    if buffer.endswith("<~!"):
                        self.log("Handshake detected")
                        self.handshake_received = True
                        buffer = ""
                else:
                    # Check for end marker
                    if received_char == "#":
                        self.log("End marker detected")
                        break
                    else:
                        # Add the character to the received data
                        self.received_data += received_char
                        self.log(f"Received character: {received_char}")
                
            # Update the previous state
            previous_state = current_state
            
            # Delay to allow for more data
            time.sleep(0.01)
            attempt_counter += 1
            
        # End reception time
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
        # Calculate bit errors by comparing received data with expected data
        min_len = min(len(self.received_data), len(expected_message))
        
        for i in range(min_len):
            if self.received_data[i] != expected_message[i]:
                # Compare bit by bit
                rx_byte = ord(self.received_data[i])
                tx_byte = ord(expected_message[i])
                
                for bit_pos in range(8):
                    rx_bit = (rx_byte >> bit_pos) & 0x01
                    tx_bit = (tx_byte >> bit_pos) & 0x01
                    
                    if rx_bit != tx_bit:
                        self.bit_errors += 1
        
        # Account for missing or extra characters
        char_diff = abs(len(self.received_data) - len(expected_message))
        self.bit_errors += char_diff * 8  # Each missing/extra char is 8 bits
        
        # Calculate BER (Bit Error Rate)
        ber = self.bit_errors / max(self.total_bits, 1)
        
        return {
            "received_message": self.received_data,
            "message_success": self.received_data == expected_message,
            "char_accuracy": min_len / max(len(expected_message), 1) if len(expected_message) > 0 else 0,
            "bit_errors": self.bit_errors,
            "total_bits": self.total_bits,
            "ber": ber,
            "start_time": start_time,
            "end_time": end_time,
            "register_values": self.register_values
        }


class LiFiSimulator:
    """Main simulator class for angular and distance testing"""
    
    def __init__(self, ambient_noise=0.05, interference=0.02, natural_disturbance=0.01, led_beam_width=120):
        self.ambient_noise = ambient_noise
        self.interference = interference
        self.natural_disturbance = natural_disturbance
        self.led_beam_width = led_beam_width
        self.results = []
        
    def run_angle_test(self, message, start_angle, end_angle, angle_step, 
                       distance, noise_level=None, interference=None,
                       natural_disturbance=None, led_beam_width=None,
                       threshold=0.5):
        """Run test with receivers at different angles"""
        if noise_level is None:
            noise_level = self.ambient_noise
        if interference is None:
            interference = self.interference
        if natural_disturbance is None:
            natural_disturbance = self.natural_disturbance
        if led_beam_width is None:
            led_beam_width = self.led_beam_width
            
        test_results = []
        angles = range(start_angle, end_angle + 1, angle_step)
        
        print(f"\nRunning angle test from {start_angle}° to {end_angle}° (step: {angle_step}°) at distance {distance}cm")
        print(f"Message: '{message}'")
        print(f"Threshold: {threshold}, Noise: {noise_level}, Interference: {interference}, Natural Disturbance: {natural_disturbance}")
        print("-" * 80)
        print(f"{'Angle':^8}|{'Distance':^8}|{'Accuracy':^8}|{'BER':^8}|{'Signal':^8}|{'Tx Time':^19}|{'Rx Time':^19}|{'Received'}") 
        print("-" * 80)
        
        for angle in angles:
            # Set up the channel with the specified angle
            channel = LiFiChannel(
                distance=distance,
                angle=angle,
                noise_level=noise_level,
                interference=interference,
                natural_disturbance=natural_disturbance,
                led_beam_width=led_beam_width
            )
            
            # Set up the transmitter and receiver
            transmitter = LiFiTransmitter(channel)
            receiver = LiFiReceiver(channel, threshold=threshold)
            
            # Transmit the message
            tx_result = transmitter.transmit_string(message)
            
            # Receive the message and get results
            rx_result = receiver.receive_transmission(message)
            
            # Calculate theoretical signal strength
            safe_distance = max(0.1, distance)  # Ensure distance is never zero
            angle_rad = math.radians(angle)
            
            # Calculate power factor safely
            power_factor = max(0.1, 2.0 / led_beam_width * 90) if led_beam_width > 0 else 0.1
            
            if angle <= 90:
                signal_strength = (math.cos(angle_rad) ** (1/power_factor)) * (10.0 / (safe_distance ** 2))
            else:
                signal_strength = 0.05 * math.cos((angle_rad - math.pi) / 2) * (10.0 / (safe_distance ** 2))
            signal_strength = max(0.01, signal_strength)
            
            # Add results
            result = {
                "angle": angle,
                "distance": distance,
                "noise_level": noise_level,
                "interference": interference,
                "natural_disturbance": natural_disturbance,
                "led_beam_width": led_beam_width,
                "threshold": threshold,
                "signal_strength": signal_strength,
                "received_message": rx_result["received_message"],
                "message_success": rx_result["message_success"],
                "char_accuracy": rx_result["char_accuracy"],
                "bit_errors": rx_result["bit_errors"],
                "total_bits": rx_result["total_bits"],
                "ber": rx_result["ber"],
                "tx_start_time": tx_result["start_time"],
                "tx_end_time": tx_result["end_time"],
                "tx_data": tx_result["transmitted_data"],
                "rx_start_time": rx_result["start_time"],
                "rx_end_time": rx_result["end_time"],
                "register_samples": rx_result["register_values"][:10] if rx_result["register_values"] else []
            }
            
            # Print results
            print(f"{angle:^8}|{distance:^8}|{result['char_accuracy']*100:^7.1f}%|{result['ber']*100:^7.2f}%|{signal_strength:^8.3f}|{result['tx_start_time'][-12:]:^19}|{result['rx_start_time'][-12:]:^19}|{result['received_message']}")
            
            # Add to results list
            test_results.append(result)
            
        return test_results
    
    def run_distance_test(self, message, angle, start_distance, end_distance, 
                          distance_step, noise_level=None, interference=None,
                          natural_disturbance=None, led_beam_width=None,
                          threshold=0.5):
        """Run test with receivers at different distances"""
        if noise_level is None:
            noise_level = self.ambient_noise
        if interference is None:
            interference = self.interference
        if natural_disturbance is None:
            natural_disturbance = self.natural_disturbance
        if led_beam_width is None:
            led_beam_width = self.led_beam_width
            
        test_results = []
        distances = []
        
        # Create distance steps
        current_distance = start_distance
        while current_distance <= end_distance:
            distances.append(current_distance)
            current_distance += distance_step
        
        print(f"\nRunning distance test from {start_distance}cm to {end_distance}cm (step: {distance_step}cm) at angle {angle}°")
        print(f"Message: '{message}'")
        print(f"Threshold: {threshold}, Noise: {noise_level}, Interference: {interference}, Natural Disturbance: {natural_disturbance}")
        print("-" * 80)
        print(f"{'Angle':^8}|{'Distance':^8}|{'Accuracy':^8}|{'BER':^8}|{'Signal':^8}|{'Tx Time':^19}|{'Rx Time':^19}|{'Received'}")
        print("-" * 80)
        
        for distance in distances:
            # Set up the channel with the specified distance
            channel = LiFiChannel(
                distance=distance,
                angle=angle,
                noise_level=noise_level,
                interference=interference,
                natural_disturbance=natural_disturbance,
                led_beam_width=led_beam_width
            )
            
            # Set up the transmitter and receiver
            transmitter = LiFiTransmitter(channel)
            receiver = LiFiReceiver(channel, threshold=threshold)
            
            # Transmit the message
            tx_result = transmitter.transmit_string(message)
            
            # Receive the message and get results
            rx_result = receiver.receive_transmission(message)
            
            # Calculate theoretical signal strength safely
            safe_distance = max(0.1, distance)  # Ensure distance is never zero
            angle_rad = math.radians(angle)
            
            # Calculate power factor safely
            power_factor = max(0.1, 2.0 / led_beam_width * 90) if led_beam_width > 0 else 0.1
            
            if angle <= 90:
                signal_strength = (math.cos(angle_rad) ** (1/power_factor)) * (10.0 / (safe_distance ** 2))
            else:
                signal_strength = 0.05 * math.cos((angle_rad - math.pi) / 2) * (10.0 / (safe_distance ** 2))
            signal_strength = max(0.01, signal_strength)
            
            # Add results
            result = {
                "angle": angle,
                "distance": distance,
                "noise_level": noise_level,
                "interference": interference,
                "natural_disturbance": natural_disturbance,
                "led_beam_width": led_beam_width,
                "threshold": threshold,
                "signal_strength": signal_strength,
                "received_message": rx_result["received_message"],
                "message_success": rx_result["message_success"],
                "char_accuracy": rx_result["char_accuracy"],
                "bit_errors": rx_result["bit_errors"],
                "total_bits": rx_result["total_bits"],
                "ber": rx_result["ber"],
                "tx_start_time": tx_result["start_time"],
                "tx_end_time": tx_result["end_time"],
                "tx_data": tx_result["transmitted_data"],
                "rx_start_time": rx_result["start_time"],
                "rx_end_time": rx_result["end_time"],
                "register_samples": rx_result["register_values"][:10] if rx_result["register_values"] else []
            }
            
            # Print results
            print(f"{angle:^8}|{distance:^8}|{result['char_accuracy']*100:^7.1f}%|{result['ber']*100:^7.2f}%|{signal_strength:^8.3f}|{result['tx_start_time'][-12:]:^19}|{result['rx_start_time'][-12:]:^19}|{result['received_message']}")
            
            # Add to results list
            test_results.append(result)
            
        return test_results
    
    def run_batch_test(self, test_configs):
        """Run multiple tests with different parameters"""
        all_results = []
        
        print(f"\nRunning batch test with {len(test_configs)} configurations")
        
        for i, config in enumerate(test_configs):
            print(f"\nBatch Test #{i+1}")
            
            if config.get("test_type") == "angle":
                # Run angle test
                results = self.run_angle_test(
                    message=config.get("message", "Hello LiFi"),
                    start_angle=config.get("start_angle", 0),
                    end_angle=config.get("end_angle", 180),
                    angle_step=config.get("angle_step", 15),
                    distance=config.get("distance", 10),
                    noise_level=config.get("noise_level", self.ambient_noise),
                    interference=config.get("interference", self.interference),
                    natural_disturbance=config.get("natural_disturbance", self.natural_disturbance),
                    led_beam_width=config.get("led_beam_width", self.led_beam_width),
                    threshold=config.get("threshold", 0.5)
                )
            elif config.get("test_type") == "distance":
                # Run distance test
                results = self.run_distance_test(
                    message=config.get("message", "Hello LiFi"),
                    angle=config.get("angle", 0),
                    start_distance=config.get("start_distance", 5),
                    end_distance=config.get("end_distance", 50),
                    distance_step=config.get("distance_step", 5),
                    noise_level=config.get("noise_level", self.ambient_noise),
                    interference=config.get("interference", self.interference),
                    natural_disturbance=config.get("natural_disturbance", self.natural_disturbance),
                    led_beam_width=config.get("led_beam_width", self.led_beam_width),
                    threshold=config.get("threshold", 0.5)
                )
            else:
                print(f"Unknown test type: {config.get('test_type')}")
                continue
            
            # Add batch ID
            for result in results:
                result["batch_id"] = i+1
                result["batch_config"] = str(config)
                
            all_results.extend(results)
            
        return all_results
    
    def save_results_to_csv(self, results, test_type="test"):
        """Save test results to a CSV file"""
        if not results:
            print("No results to save.")
            return
        
        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lifi_{test_type}_{timestamp}.csv"
        
        # Create 'results' directory if it doesn't exist
        if not os.path.exists('results'):
            os.makedirs('results')
            
        filepath = os.path.join('results', filename)
        
        # Get fieldnames from the first result
        fieldnames = list(results[0].keys())
        
        # Handle register samples separately to prevent CSV corruption 
        if "register_samples" in fieldnames:
            fieldnames.remove("register_samples")
            
        # Write results to CSV
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                # Make a copy without register_samples
                row = {k: v for k, v in result.items() if k != "register_samples"}
                writer.writerow(row)
                
        # Save register values to a separate file if needed
        if any("register_samples" in result for result in results):
            reg_filename = f"lifi_{test_type}_registers_{timestamp}.csv"
            reg_filepath = os.path.join('results', reg_filename)
            
            with open(reg_filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["test_id", "angle", "distance", "sample_index", "register_value"])
                
                for i, result in enumerate(results):
                    if "register_samples" in result and result["register_samples"]:
                        for j, value in enumerate(result["register_samples"]):
                            writer.writerow([i, result["angle"], result["distance"], j, value])
                
            print(f"\nRegister values saved to: {reg_filepath}")
                
        print(f"\nResults saved to: {filepath}")
        return filepath


def main():
    """Main entry point for the simulator"""
    simulator = LiFiSimulator(ambient_noise=0.05, interference=0.02, natural_disturbance=0.01, led_beam_width=120)
    
    while True:
        print("\n=== Enhanced LiFi Angle and Distance Simulator ===")
        print("1. Run Angle Test (fixed distance, varying angles)")
        print("2. Run Distance Test (fixed angle, varying distances)")
        print("3. Run Batch Test (multiple configurations)")
        print("4. Set Global Parameters")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            # Run angle test
            message = input("Enter message to transmit: ")
            if not message:
                message = "Hello LiFi"
                
            start_angle = int(input("Enter start angle (0 to 180): ") or "0")
            end_angle = int(input("Enter end angle (0 to 180): ") or "180")
            angle_step = int(input("Enter angle step: ") or "15")
            distance = float(input("Enter fixed distance (cm): ") or "10")
            threshold = float(input("Enter receiver threshold (0.0-1.0): ") or "0.5")
            
            results = simulator.run_angle_test(message, start_angle, end_angle, angle_step, distance, threshold=threshold)
            simulator.save_results_to_csv(results, "angle")
            
        elif choice == '2':
            # Run distance test
            message = input("Enter message to transmit: ")
            if not message:
                message = "Hello LiFi"
                
            angle = int(input("Enter fixed angle (0 to 180): ") or "0")
            start_distance = float(input("Enter start distance (cm): ") or "5")
            end_distance = float(input("Enter end distance (cm): ") or "50")
            distance_step = float(input("Enter distance step: ") or "5")
            threshold = float(input("Enter receiver threshold (0.0-1.0): ") or "0.5")
            
            results = simulator.run_distance_test(message, angle, start_distance, end_distance, distance_step, threshold=threshold)
            simulator.save_results_to_csv(results, "distance")
            
        elif choice == '3':
            # Run batch test
            print("\nBatch Test Configuration")
            print("Enter multiple test configurations (one per line)")
            print("Format: test_type,param1=value1,param2=value2,...")
            print("Examples:")
            print("  angle,message=Test,start_angle=0,end_angle=90,angle_step=10,distance=15,threshold=0.4")
            print("  distance,message=Hello,angle=45,start_distance=10,end_distance=40,distance_step=5")
            print("Enter 'done' on a new line when finished")
            
            configs = []
            while True:
                line = input("> ")
                if line.lower() == 'done':
                    break
                    
                # Parse the configuration
                try:
                    parts = line.split(',')
                    test_type = parts[0].strip()
                    
                    config = {"test_type": test_type}
                    for part in parts[1:]:
                        if '=' in part:
                            key, value = part.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Try to convert to appropriate type
                            try:
                                if '.' in value:
                                    config[key] = float(value)
                                else:
                                    config[key] = int(value)
                            except ValueError:
                                config[key] = value
                                
                    configs.append(config)
                    print(f"Added configuration: {config}")
                except Exception as e:
                    print(f"Error parsing configuration: {e}")
            
            if configs:
                results = simulator.run_batch_test(configs)
                simulator.save_results_to_csv(results, "batch")
            else:
                print("No configurations added.")
            
        elif choice == '4':
            # Set global parameters
            print("\nCurrent Global Parameters:")
            print(f"Ambient Noise Level: {simulator.ambient_noise}")
            print(f"Interference Level: {simulator.interference}")
            print(f"Natural Disturbance: {simulator.natural_disturbance}")
            print(f"LED Beam Width: {simulator.led_beam_width}°")
            
            new_noise = float(input(f"\nEnter ambient noise level (0.0-1.0): ") or str(simulator.ambient_noise))
            new_interference = float(input(f"Enter interference level (0.0-1.0): ") or str(simulator.interference))
            new_disturbance = float(input(f"Enter natural disturbance level (0.0-1.0): ") or str(simulator.natural_disturbance))
            new_beam_width = float(input(f"Enter LED beam width (degrees): ") or str(simulator.led_beam_width))
            
            simulator.ambient_noise = new_noise
            simulator.interference = new_interference
            simulator.natural_disturbance = new_disturbance
            simulator.led_beam_width = new_beam_width
            
            print("\nParameters updated:")
            print(f"Ambient Noise Level: {simulator.ambient_noise}")
            print(f"Interference Level: {simulator.interference}")
            print(f"Natural Disturbance: {simulator.natural_disturbance}")
            print(f"LED Beam Width: {simulator.led_beam_width}°")
            
        elif choice == '5':
            print("Exiting simulator...")
            break
            
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


if __name__ == "__main__":
    main()