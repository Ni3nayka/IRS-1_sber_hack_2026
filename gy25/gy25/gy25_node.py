#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import serial
import threading
import struct
import time

class Gy25Node(Node):
    def __init__(self):
        super().__init__('gy25_node')

        # Declare parameters
        self.declare_parameter('port', '')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('topic_roll', '/gy25/roll')
        self.declare_parameter('topic_pitch', '/gy25/pitch')
        self.declare_parameter('topic_yaw', '/gy25/yaw')

        port = self.get_parameter('port').get_parameter_value().string_value
        baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        topic_roll = self.get_parameter('topic_roll').get_parameter_value().string_value
        topic_pitch = self.get_parameter('topic_pitch').get_parameter_value().string_value
        topic_yaw = self.get_parameter('topic_yaw').get_parameter_value().string_value

        # Create publishers
        self.pub_roll = self.create_publisher(Int32, topic_roll, 10)
        self.pub_pitch = self.create_publisher(Int32, topic_pitch, 10)
        self.pub_yaw = self.create_publisher(Int32, topic_yaw, 10)

        # Open serial port
        try:
            self.ser = serial.Serial(port, baudrate, timeout=0.1)
            self.get_logger().info(f'Connected to {port} at {baudrate} baud')
        except Exception as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            return

        # Start background thread for reading
        self.running = True
        self.thread = threading.Thread(target=self.read_loop)
        self.thread.daemon = True
        self.thread.start()

    def read_loop(self):
        """Continuously read and parse GY-25 data."""
        buffer = bytearray()
        while self.running and rclpy.ok():
            try:
                # Read up to 100 bytes (or until timeout)
                data = self.ser.read(100)
                if not data:
                    continue
                buffer.extend(data)

                # Search for start bytes 0xAA, 0xAA
                while len(buffer) >= 2:
                    if buffer[0] == 0xAA and buffer[1] == 0xAA:
                        # We have a potential start
                        if len(buffer) >= 8:  # 2 start + 6 data + 1 checksum = 9 bytes total
                            packet = buffer[:9]  # 2 start + 6 data + checksum
                            # Validate checksum
                            checksum = sum(packet[2:8]) & 0xFF
                            if checksum == packet[8]:
                                # Parse angles (little‑endian, signed 16‑bit, scaled by 100)
                                roll = struct.unpack('<h', packet[2:4])[0]
                                pitch = struct.unpack('<h', packet[4:6])[0]
                                yaw = struct.unpack('<h', packet[6:8])[0]
                                # Publish as Int32 (the original integer scaled value)
                                self.pub_roll.publish(Int32(data=roll))
                                self.pub_pitch.publish(Int32(data=pitch))
                                self.pub_yaw.publish(Int32(data=yaw))
                                self.get_logger().debug(f'Published: roll={roll}, pitch={pitch}, yaw={yaw}')
                            else:
                                self.get_logger().warn('Checksum mismatch, discarding packet')
                            # Remove processed bytes
                            buffer = buffer[9:]
                        else:
                            # Not enough data yet, wait for more
                            break
                    else:
                        # Discard bytes until we find a start byte
                        buffer.pop(0)

            except serial.SerialException as e:
                self.get_logger().error(f'Serial error: {e}')
                time.sleep(1)  # wait before re‑trying
            except Exception as e:
                self.get_logger().error(f'Unexpected error: {e}')

    def destroy_node(self):
        """Clean up on shutdown."""
        self.running = False
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = Gy25Node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()