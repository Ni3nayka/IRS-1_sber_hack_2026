# IRS-1_
IRS-1 - Intelligent (mobile) robotic systems

# arduinoDriver
ros2 run arduinoDriver arduinoDriver_node.py
ros2 run arduinoDriver arduinoDriver_node.py --ros-args -p port:=/dev/ttyUSB0 -p rate:=20.0 --remap motor_speed_left:=/left_wheel_speed
