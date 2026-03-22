#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int8
import cv2
import cv2.aruco as aruco
import numpy as np

class ArucoDetector(Node):
    def __init__(self):
        super().__init__('aruco_detector')
        # Публикатор в топик arucoStartDetect
        self.publisher = self.create_publisher(Int8, 'arucoStartDetect', 10)
        
        # Открываем камеру (0 — первая USB-камера)
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.get_logger().error('Не удалось открыть камеру')
            raise RuntimeError('Камера недоступна')
        
        # Настройка детектора ArUco (OpenCV 4.x)
        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
        self.parameters = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.aruco_dict, self.parameters)
        self.target_id = 25   # ID искомого маркера
        
        # Таймер для периодического опроса камеры (30 fps)
        self.timer = self.create_timer(1.0 / 30.0, self.detect_callback)
        self.get_logger().info('Нода детектора ArUco запущена')

    def detect_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn('Не удалось получить кадр')
            return
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Детекция маркеров
        corners, ids, rejected = self.detector.detectMarkers(gray)
        
        # Логируем все найденные ID
        if ids is not None:
            marker_ids = ids.flatten().tolist()
            self.get_logger().info(f'Обнаружены маркеры: {marker_ids}')
        else:
            self.get_logger().info('Маркеры не обнаружены')
        
        # Проверяем наличие целевого ID
        detected = 0
        if ids is not None and self.target_id in ids:
            detected = 1
        
        # Публикуем результат
        msg = Int8()
        msg.data = detected
        self.publisher.publish(msg)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ArucoDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()