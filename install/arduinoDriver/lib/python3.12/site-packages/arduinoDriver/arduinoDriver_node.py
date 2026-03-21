#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import serial
import serial.tools.list_ports
import time

class ArduinoController(Node):
    def __init__(self):
        super().__init__('arduino_controller')

        # Параметры
        self.declare_parameter('port', '')           # автоматическое определение, если не задано
        self.declare_parameter('baudrate', 9600)
        self.declare_parameter('rate', 10.0)         # Гц

        self.port = self.get_parameter('port').get_parameter_value().string_value
        self.baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        self.rate = self.get_parameter('rate').get_parameter_value().double_value

        # Переменные для хранения последних полученных значений
        self.speed_left = 0
        self.speed_right = 0
        self.servo_angle_1 = 0
        self.servo_angle_2 = 0

        # Подписки на топики (названия можно менять через remap)
        self.sub_speed_left = self.create_subscription(
            Int32, 'motor_speed_left', self.speed_left_callback, 10)
        self.sub_speed_right = self.create_subscription(
            Int32, 'motor_speed_right', self.speed_right_callback, 10)
        self.sub_servo1 = self.create_subscription(
            Int32, 'servo_angle_1', self.servo_1_callback, 10)
        self.sub_servo2 = self.create_subscription(
            Int32, 'servo_angle_2', self.servo_2_callback, 10)

        # Подключение к Arduino
        self.serial_conn = None
        self.connect_serial()

        # Таймер для отправки команд с заданной частотой
        self.timer = self.create_timer(1.0 / self.rate, self.send_commands)

        self.get_logger().info('Arduino controller node started')

    def connect_serial(self):
        """Устанавливает соединение с Arduino по последовательному порту."""
        if self.port:
            port = self.port
        else:
            # Автоматический поиск Arduino
            ports = serial.tools.list_ports.comports()
            arduino_ports = [p.device for p in ports if 'Arduino' in p.description or 'usb' in p.device]
            if not arduino_ports:
                self.get_logger().error('Arduino not found')
                return
            port = arduino_ports[0]
            self.get_logger().info(f'Using automatically detected port: {port}')

        try:
            self.serial_conn = serial.Serial(port, self.baudrate, timeout=1)
            time.sleep(2)  # даём Arduino время на инициализацию
            self.get_logger().info(f'Connected to {port} at {self.baudrate} baud')
        except Exception as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            self.serial_conn = None

    def speed_left_callback(self, msg):
        self.speed_left = msg.data

    def speed_right_callback(self, msg):
        self.speed_right = msg.data

    def servo_1_callback(self, msg):
        self.servo_angle_1 = msg.data

    def servo_2_callback(self, msg):
        self.servo_angle_2 = msg.data

    def send_commands(self):
        """Отправляет команды на Arduino, если соединение активно."""
        if self.serial_conn is None or not self.serial_conn.is_open:
            self.get_logger().warn('Serial connection not available')
            return

        # Формируем строки команд
        motor_cmd = f"N {self.speed_left} {self.speed_right}\n"
        servo_cmd = f"A {self.servo_angle_1} {self.servo_angle_2}\n"

        try:
            self.serial_conn.write(motor_cmd.encode())
            self.serial_conn.write(servo_cmd.encode())
            # Можно добавить небольшую задержку между командами, если Arduino их не успевает обрабатывать
            # time.sleep(0.005)
        except Exception as e:
            self.get_logger().error(f'Serial write error: {e}')

    def destroy_node(self):
        """Закрывает последовательный порт при завершении узла."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ArduinoController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()