#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32

class MotorTestNode(Node):
    def __init__(self):
        super().__init__('motor_test_node')
        # Публикаторы на те же топики, что слушает ArduinoDriver
        self.pub_left = self.create_publisher(Int32, 'motor_speed_left', 10)
        self.pub_right = self.create_publisher(Int32, 'motor_speed_right', 10)

        # Параметры теста
        self.ramp_time = 3.0          # время разгона/торможения (сек)
        self.max_speed = 100
        self.update_rate = 20.0       # частота обновления (Гц)

        # Запоминаем время старта
        self.start_time = self.get_clock().now().nanoseconds / 1e9
        self.total_time = 2 * self.ramp_time   # разгон + торможение

        # Таймер для периодической публикации
        self.timer = self.create_timer(1.0 / self.update_rate, self.timer_callback)
        self.get_logger().info('Motor test node started')

    def timer_callback(self):
        now = self.get_clock().now().nanoseconds / 1e9
        t = now - self.start_time

        if t > self.total_time:
            # Тест завершён: останавливаем моторы и завершаем узел
            self.pub_left.publish(Int32(data=0))
            self.pub_right.publish(Int32(data=0))
            self.get_logger().info('Test finished, stopping motors.')
            self.timer.cancel()
            rclpy.shutdown()
            return

        # Определяем фазу: разгон или торможение
        if t <= self.ramp_time:
            # Линейный разгон от 0 до max_speed
            speed = (t / self.ramp_time) * self.max_speed
        else:
            # Линейное торможение от max_speed до 0
            t_brake = t - self.ramp_time
            speed = self.max_speed * (1 - t_brake / self.ramp_time)

        speed_int = int(round(speed))
        self.pub_left.publish(Int32(data=speed_int))
        self.pub_right.publish(Int32(data=speed_int))
        self.get_logger().debug(f'Publishing speed: {speed_int}')

def main(args=None):
    rclpy.init(args=args)
    node = MotorTestNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()