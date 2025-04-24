import cv2
import os
import turtle
import json
import boto3
import time
import ast
import pygame
import s3fs
from dotenv import load_dotenv
import numpy as np
from pyzbar.pyzbar import decode



class QRKiosk: 
    def __init__(self):
        
        # Initializing Variables
        self.state = "IDLE"
        self.data = None
        self.valid = None
        self.scan_state = True
        self.frame = None
        self.assignedColor = None
        self.decoded_info = ""
        self.prev_data = None
        self.scannerCount = 0
        self.errorCount = 0
        self.parentId = 0
        self.studentId = 0
        self.ColorList = ["Red", "Blue", "Green", "Yellow"]
        self.cap = cv2.VideoCapture(0)

        # Setting Window Properties
        cv2.namedWindow('Live Feed')
        cv2.moveWindow("Live Feed", 0,0)
        cv2.setWindowProperty("Live Feed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    def preprocess_img(self, frame):
        # Function to apply a filter to the camera feed
        # to allow the camera to read the Code in lighted areas

        # Converting frame to Grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # enhancing contrast of grayscale img
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced_gray = clahe.apply(gray)

        # applying a binary filter on img
        processed = cv2.adaptiveThreshold(enhanced_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)       
        
        return processed

    def decodeQR(self, frame):
        # Function that will decode the scanned QR code 
        # and return the info

        # Scanning for QR Code
        info = decode(frame)

        try:

            # For item in QR code scanned
            for qr in info:

                # Obtaining data from QR code
                self.decoded_info = qr.data.decode('utf-8')

            # If info has data within it
            if info and len(self.decoded_info) > 0:
                if self.data == self.decoded_info:
                    return None

                # Creating Dictionary of data
                data_dic = json.loads(self.decoded_info)

                print("QR Code Scanned")
                return data_dic
        except:
            return self.prev_data

    def validateQR(self, decode_info):
        # Function to determine if the QR code scanned
        # is one created from our system

        # Variables
        load_dotenv()
        detector = cv2.QRCodeDetector()

        # Setting up boto3 client
        s3 = boto3.client(
            "s3",
            aws_access_key_id = os.getenv("ac_key"),
            aws_secret_access_key = os.getenv("sac_key"),
        )

        # Setting up S3 File System
        fs = s3fs.S3FileSystem(key = os.getenv("ac_key"), secret=os.getenv("sac_key"))

        # Storing Bucket Name
        bucket_name = "clamsqrcodebucket"

        # Creating Object Variable of Bucket objects
        object_list = s3.list_objects_v2(Bucket=bucket_name).get("Contents")

        # Iterating over object in bucket
        for obj in object_list:

            # Creating img key var
            img_key = obj["Key"]
            print(img_key)

            # opening image
            with fs.open(f"{bucket_name}/{img_key}", "rb") as f:
                
                image_bytes = f.read()

            # creating array of img bytes
            image_array = np.frombuffer(image_bytes, np.uint8)
            
            # Creating Img
            img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            # Saving data of test qr
            retval, data,  points, straight_qrcodedeMulti = detector.detectAndDecodeMulti(img)
            #print("Data " + data)
            data_str = data[0]


            data_dic = ast.literal_eval(data_str)

            print(data_dic)

            print("Testing QR Code Data")

            # Comparing scanned data to QR codes in S3
            if(data_dic  == decode_info):

                print("QR Code Valid")

                return True

        print("QR Code Not Valid")

        return False
            
    def RetriveQRScanState(self, pId):
        # Function that will retrive the scan state of the QR Code
        # to prevent duplicate scans

        # Variable
        table = "Parent_Table"
        load_dotenv()


        # Creating Dynamodb Resource and Parent Table
        dynamodb_resources = boto3.resource("dynamodb", aws_access_key_id = os.environ.get("ac_key"), aws_secret_access_key = os.environ.get("sac_key"), region_name='us-east-2')
        P_table = dynamodb_resources.Table(table)

        response = P_table.get_item(
            Key={"Parent_Id": pId},
            ProjectionExpression="ScanState",
        )

        print("Retrevied QR Scan State")
        print(response["Item"].get("ScanState"))
        return response["Item"].get("ScanState")

    def ConeAssignment(self, scannerCount, ColorList):
        # Function that will assign the cone color to QR code

        # Creating Assigned color var from the color list 
        # and one less than the scanner count
        assignedColor = ColorList[scannerCount-1]

        print("The following color has been assigned:")
        print(assignedColor)

        return assignedColor

    def DisplayConeColor(self, assignedColor):
        # Function to display the assigned color on the screen

        # Creating Screen variable 
        ColorScreen = turtle.Screen()

        # setting up the screen
        ColorScreen.setup(width = 800, height= 480, startx= 0, starty= 0)


        # Setting assigned color 
        ColorScreen.bgcolor(assignedColor)
        ColorScreen.update()
        
        # Waiting 3 seconds
        time.sleep(3)

        # Closing Screen
        ColorScreen.bye()

    def updateQRScanState(self, pId):
        # Function to update the QR Code Scan state for each parent

        # Variables
        table = "Parent_Table"

        # Creating Dynamodb Resource and Parent table
        dynamodb_resources = boto3.resource("dynamodb", aws_access_key_id = os.environ.get("ac_key"), aws_secret_access_key = os.environ.get("sac_key"), region_name='us-east-2')
        Parent_Table = dynamodb_resources.Table(table)

        # Updating table field
        response = Parent_Table.update_item(
            Key={"Parent_Id": pId},
            UpdateExpression="set ScanState = :s",
            # ExpressionAttributeNames={
            # "#Scan_State": "Scan_State",
            # },
            ExpressionAttributeValues={
                ":s" : True,
            }, 
            ReturnValues="UPDATED_NEW",
        )

        print("Updated Scan State")

    def UpdateChildInfo(self, student_Id, assignedColor):
        # Function that updates the assigned color for the student

        # Variables
        load_dotenv()
        table = "Student_Table"

        # Creating Dynamodb resource and Table
        dynamodb_resources = boto3.resource("dynamodb", aws_access_key_id = os.environ.get("ac_key"), aws_secret_access_key = os.environ.get("sac_key"), region_name='us-east-2')
        Student_Table = dynamodb_resources.Table(table)

        # Updating Table
        response = Student_Table.update_item(
            Key={"Student_Id": student_Id},
            UpdateExpression="set Assigned_Color = :A",
            ExpressionAttributeValues={
                ":A": assignedColor,
            }, 
            ReturnValues="UPDATED_NEW",
        )

        print("Updated Child Assigned Color")

    def displayFeedback(self, valid):
        # Function to display the feedback if the QR
        # code is valid or not

        if valid:

            # Approved QR code img file 
            img = cv2.imread("/home/admin/Desktop/Senior Project/Resources/greenCheck.png")
            
            # Creating Window
            cv2.namedWindow("Valid")

            # Setting Window Properties
            cv2.setWindowProperty("Valid", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.moveWindow("Valid", 0,0)

            # Displaying Img
            cv2.imshow("Valid", img)
            cv2.waitKey(3000)

            # Closing Img
            cv2.destroyWindow("Valid")
        
        else:

            # Rejected QR code img file
            img = cv2.imread("/home/admin/Desktop/Senior Project/Resources/redX.png")
            
            # Creating Window
            cv2.namedWindow("Invalid")

            # Setting Window Properties
            cv2.setWindowProperty("Invalid", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            
            # Displaying Img
            cv2.imshow("Invalid", img)
            cv2.waitKey(3000)

            # Closing Img
            cv2.destroyWindow("Invalid")

    def DisplayErrorMsg(self):
        # Function to Display the Error Message after too many
        # wrong QR Codes have been scanned

        print("Displaying Error Message")

        # Initialize Pygame
        pygame.init()

        # Set the dimensions of the screen
        screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)
        pygame.display.set_caption("Error Message")

        # Set the background color to red
        screen.fill((255, 0, 0))

        # Create a font object
        font = pygame.font.SysFont('Arial', 36)

        # Render the text
        text = font.render("Error, Please find faculty for assistance", True, (255, 255, 255))

        # Position the text in the center
        text_rect = text.get_rect(center=(400, 240))

        # Draw the text on the screen
        screen.blit(text, text_rect)

        # Update the screen
        pygame.display.update()

        # Wait for 3 seconds
        time.sleep(3)

        # Close Pygame
        pygame.quit() 

    def run(self):
        # Main Function 

        while True:

            # IDLE STATE
            if self.state == "IDLE": 
                print("Waiting for QR Code...")
                self.data = None
                
                ret, self.frame = self.cap.read()

                # If no camera detected 
                if not ret:
                    print("No Camera Detected")
                    break
                
                # Applying Filter to Frame
                processed = self.preprocess_img(self.frame)
        
                # Show Live feed
                cv2.imshow("Live Feed", self.frame)

                # Detecting QR code
                self.data = self.decodeQR(processed)

                # Changing State if data != prev data
                print(self.data)
                
                if self.data and self.data != self.prev_data:
                    self.prev_data = self.data
                    self.state = "VALIDATING"

            # VALIDATING STATE
            elif self.state == "VALIDATING":
                print("Testing Validity of QR Code")
                
                self.valid = self.validateQR(self.data)     
                #self.scan_state = self.RetriveQRScanState(self.data["Parent_Id"])
                
                # If code valid and not been scanned and not self.scan_state
                if(self.valid):

                    # Displaying Feedback
                    self.displayFeedback(self.valid)

                    self.parentId = self.data["Parent_Id"]

                    # Incrementing Scanner Count
                    self.scannerCount += 1

                    # Resetting Error Count
                    self.errorCount = 0
                    
                    # Changing State
                    self.state = "ASSIGNING"

                elif(self.valid == False):
                    
                    # Displaying Feedback
                    self.displayFeedback(self.valid)

                    # Incrementing Error Count
                    self.errorCount += 1

                    # Changing State
                    self.state = "RESETTING"
                


            # ASSIGNING STATE
            elif self.state == "ASSIGNING":
                print("Assigning Color Cone")

                # Running Cone Assignment 
                self.assignedColor = self.ConeAssignment(self.scannerCount, self.ColorList)

                # Displaying Cone Assignment
                print("Display Cone Color")
                self.DisplayConeColor(self.assignedColor)

                # Updating Database Items
                print("Updating Info")
                
                # Updating Assigned Color for each Student
                for student in self.data["Students Info"]:
                    self.studentId = student["Student_Id"]
                    self.UpdateChildInfo(int(self.studentId), self.assignedColor)

                # Updating QR Code Scan State for parent
                self.updateQRScanState(self.parentId)

                # Changing State
                self.state = "RESETTING"

            # COOL DOWN STATE
            elif self.state == "RESETTING":
                print("RESETTING")
                print("______________________________")
                self.valid = None
                self.data = None
                self.assignedColor = None
                self.parentId = 0
                self.studentId = 0

                cv2.waitKey(1000)
                
                # Error Count equal 3 condition
                if (self.errorCount == 3):
                    self.DisplayErrorMsg()
                    self.errorCount = 0
                    self.state = "IDLE"

                # Scanner Count reset
                elif self.scannerCount == len(self.ColorList):
                    self.scannerCount = 0

                # Changing State
                self.state = "IDLE"

            # Delay for key detection
            key = cv2.waitKey(1)

            if(key == ord('q')):
                break

if __name__ == "__main__":
    kiosk = QRKiosk()
    kiosk.run()
