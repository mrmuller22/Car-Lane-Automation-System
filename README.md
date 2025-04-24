# Car-Lane-Automation-System

Description:

The dismissal process for students being picked up by car is often confusing, frustrating, and inefficient. I was tasked with designing a system to streamline and automate this process.

This system uses a QR code scanning kiosk to organize car arrivals and sequentially assign them to a cone and improve the experience for both staff and parents.

The goals for this system were:
1. Generate unique QR codes for each parent containing their student’s information.
2. Develop a kiosk station to scan parent QR codes and assign them to a designated color cone zone.
3. Build a user-friendly GUI that allows parents to enter and update their information.
4. Enable real-time updates to user data and cone assignments.

Features:
This project features a Raspberry Pi-powered kiosk that scans QR codes using a USB camera and processes the data in real time. The system is built with embedded Python and uses a state machine to manage its operational flow. AWS Lambda functions are used to generate the QR codes for each parent. When a QR code is scanned, the Raspberry Pi communicates with our DynamoDB database. The kiosk then assigns the arriving parent a color-coded cone for pickup coordination. Another Raspberry pi is displaying a webpage that displays which color cone student(s) need to go to meet their parents in real time. The project also includes a GUI for parent registration and updates, cloud-based data handling with S3, and image processing using OpenCV and Pyzbar to detect and decode QR codes efficiently.

The periphals used:
USB Camera
Raspberry Pi
LCD Screen
Programming Language: Python

Libraries/Frameworks: boto3 (AWS integration), s3sf (s3 file handling), numpy, pyzbar (QR code scanning), and opencv (image processing)

Environment: Raspberry Pi OS (Desktop)

Video of Working System:
https://github.com/user-attachments/assets/5a0c0438-07e9-4974-b267-20207c48ac24

