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
        # Publisher for the detection flag
        self.publisher = self.create_publisher(Int8, 'arucoStartDetect', 10)
        # Camera device (usually /dev/video0)
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.get_logger().error('Could not open camera')
            raise RuntimeError('Camera not accessible')
        
        # ArUco dictionary and parameters
        self.aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
        self.parameters = aruco.DetectorParameters_create()
        self.target_id = 25   # Change to your desired marker ID
        
        # Timer to process frames periodically (e.g., 30 fps)
        self.timer = self.create_timer(1.0/30.0, self.detect_callback)
        self.get_logger().info('ArUco detector node started')

    def detect_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn('Failed to grab frame')
            return
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect markers
        corners, ids, rejected = aruco.detectMarkers(gray, self.aruco_dict, parameters=self.parameters)
        
        # Check if our target ID is present
        detected = 0
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                if marker_id == self.target_id:
                    detected = 1
                    # Optional: draw the marker outline on the frame (for debugging)
                    aruco.drawDetectedMarkers(frame, corners)
                    cv2.putText(frame, f"ID {self.target_id} DETECTED", (10,30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                    break
        
        # Publish result
        msg = Int8()
        msg.data = detected
        self.publisher.publish(msg)
        
        # Show frame (only if you want to see the video; remove in production)
        cv2.imshow('ArUco Detector', frame)
        cv2.waitKey(1)

    def destroy_node(self):
        self.cap.release()
        cv2.destroyAllWindows()
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