# !/usr/bin/env python3

import ev3dev.ev3 as ev3
import time
import math

class Odometry:


# =========================== Initialising ===========================

    def __init__(self):
        """
        Initializes the sensors, everything for driving and odometry
        """

        self.initializeSensors()

        # initialize wheels
        self.leftWheel = ev3.LargeMotor('outA')
        self.rightWheel = ev3.LargeMotor('outB')

        # default values for speed and PID
        self.defaultSpeed = 200 #210
        self.targetBrightness = 200
        self.brightness = self.targetBrightness
        self.lastBrightness = self.targetBrightness

        # default values for color detection
        self.colorFound = None
        self.rgb = self.rawColorValue()
        self.blue = 0
        self.red = 0
        self.field = None

        # default PID controller variables
        self.integral = 0
        self.integral_list = []

        # default chessboard variables
        self.chessboardFound = False
        self.blue_even = None
        self.red_even = None

        # ==>> robot needs to know it starting position <<==
        # and then it should update its position
        # it starts thinking its headed north and is at (0,0)
        self.direction = 0
        self.length_segment = 42
        self.x = 0
        self.y = 0
        self.segments_moved_x = 0
        self.segments_moved_y = 0

        # distance wheels to each other in cm
        # higher values ditances will be perceived a litte longer (13 => 35,38,57,39,34)
        # lower values distances will be perceived a little shorter (11 => 37,40,33,46)
        self.a = 12.5 # or 12-13
        self.circumference = 2 * 2.8 * math.pi

        self.comes_from_obstacle = False

        self.resetOdometry()

    def initializeWheels(self):
        """
        Reset the wheels to the default speed and default mode
        """
        self.rightWheel.reset()
        self.leftWheel.reset()
        self.rightWheel.speed_sp = self.defaultSpeed
        self.leftWheel.speed_sp = self.defaultSpeed
        self.leftWheel.command = "run-forever"
        self.rightWheel.command = "run-forever"
        self.initialPositionLeft = self.leftWheel.position
        self.initialPositionRight = self.rightWheel.position

    def resetOdometry(self):
        """
        Resets the odometry calculations
        """
        # default values odometry:
        # distance the wheels have travelled since the last check
        self.dl = 0
        self.dr = 0

        self.gamma_old = 0
        self.delta_x = 0
        self.delta_y = 0
        self.segments_moved_x = 0
        self.segments_moved_y = 0






# =========================== Driving ===========================

    def brake(self):
        """
        Brakes the motors
        """
        self.rightWheel.stop_action = "brake"
        self.leftWheel.stop_action = "brake"
    
    def resetWheels(self):
        """
        Resets the wheels
        """
        self.rightWheel.reset()
        self.leftWheel.reset()

    def PID(self):
        """
        PID controller for line following
        """

        # For PID controller
        Kp = 0.85        # Proportional correction factor
        Ki = 0.01        # Integral correction factor
        Kd = 0.45        # Differential correction factor, must stay below 1

        error = self.targetBrightness - self.brightness
        correction = error * Kp
        self.integral += error

        self.integral_list.append(error)
        if(len(self.integral_list) > 30):
            # Remove the first element from the list and from the integral
            item = self.integral_list.pop(0)
            self.integral -= item
        correction += (self.integral * Ki)

        # Differential correction
        # This changes the correction based on the difference
        # between the last and current error rate
        last_error = self.targetBrightness - self.lastBrightness
        difference = last_error - error
        correction += (abs(difference) * Kd)

        if correction > 0:
            self.leftWheel.speed_sp = (self.defaultSpeed - abs(correction))
            self.rightWheel.speed_sp = self.defaultSpeed
        else:
            self.leftWheel.speed_sp = self.defaultSpeed
            self.rightWheel.speed_sp = (self.defaultSpeed - abs(correction))
        
        self.leftWheel.command = "run-forever"
        self.rightWheel.command = "run-forever"

    def updateBrightness(self):
        """
        Updates the colors and calculates the brightness via the color sensor
        Will mainly (but not exclusivly) get used in line following and field detection
        """

        self.lastBrightness = self.brightness
        self.rgb = self.rawColorValue()
        r = self.rgb[0]
        g = self.rgb[1]
        b = self.rgb[2]
        self.brightness = (0.2126*r + 0.7152*g + 0.0722*b)

    def checkColor(self):
        """
        Scans color via sensor and updates self.colorFound
        Will get called after updating brightness, 
        so it doesn't need to update it again to not but an unnecessary burden on the CPU
        """

        tolerance = 30 # increases the accepted intervall
        r = self.rgb[0]
        g = self.rgb[1]
        b = self.rgb[2]

        if r > (30 - tolerance) and r < (45 + tolerance) \
                and g > (120 - tolerance) and g < (150 + tolerance) \
                and b > (130 - tolerance) and b < (160 + tolerance) \
                and self.brightness > (100 - tolerance) \
                and self.brightness < (120 + tolerance):
            self.colorFound = "blue"
            
        elif r > (160 - tolerance) and r < (190 + tolerance) \
                and g > (20 - tolerance) and g < (45 + tolerance) \
                and b > (20 - tolerance) and b < (40 + tolerance) \
                and self.brightness > (50 - tolerance) \
                and self.brightness < (60 + tolerance):
            self.colorFound = "red"

        # None of the tested colors found
        else: 
            self.colorFound = None

    def checkForField(self):
        """
        Checks if the robot is at on a field, usually but not always at the intersection
        It has to see a color twice to reduce false positives
        """
        # When we find an intersection, we have reached the end of the line
        if (self.colorFound == "blue"):
            self.blue += 1
            self.red = 0
            if self.blue >= 2: # it needs to see blue twice to reduce false positives
                self.field = "blue"
                #print("(checkForField) Field found: blue")

        elif (self.colorFound == "red"):
            self.red += 1
            self.blue = 0
            if self.red >= 2: # # it needs to see red twice to reduce false positives
                self.field = "red"
                #print("(checkForField) Field found: red")

        else:
            # Reset to default values to begin counting again
            self.red = 0
            self.blue = 0
            self.field = None

    def driveABitForward(self, default = 1):
        """
        This method will be used to drive the robot a bit forward to halt on the center of the intersection.
        Being at the center of the field yields better results for path scanning and turning. 
        """
        # when it sees a red or blue spot, it need to go a bit further
        self.rightWheel.speed_sp = 200
        self.leftWheel.speed_sp = 200
        self.leftWheel.command = "run-forever"
        self.rightWheel.command = "run-forever"
        time.sleep(0.55 * default)

        # stop the motors
        self.brake()
        self.resetWheels()

    def scanPaths(self):
        """
        When the robot reaches a blue or red spot, it needs to scan the outgoing paths.
        Possible paths are at 0, 90, 180 or 270 degrees

        :return paths: list of directions with available path
        """

        tolerance = 50 # increases the accepted intervall

        # default values for path detection
        initial_position = self.leftWheel.position # initial position is here local!
        difference = 0
        degrees0 = False
        degrees90 = False
        degrees180 = False
        degrees270 = False

        result = []

        while (difference <= 740) and (self.readButton() != True): #TODO # 750
            self.rightWheel.speed_sp = -130
            self.leftWheel.speed_sp = 130
            self.leftWheel.command = "run-forever"
            self.rightWheel.command = "run-forever"

            self.updateBrightness()

            difference = self.leftWheel.position - initial_position

            if (self.brightness < 160) and (difference > (0 - tolerance)) and (difference < (20+tolerance)):
                degrees0 = True
                if degrees0:
                    #print("(scanPaths) Path straight ahead")
                    result.append(0) # double values will be ignored due being converted to set

            if (self.brightness < 160) and (difference > (160 - tolerance)) and (difference < (200+tolerance)):
                degrees90 = True
                if degrees90:
                    result.append(90)
                    #print("(scanPaths) Path at 90 Degrees")

            if (self.brightness < 160) and (difference > (340 - tolerance)) and (difference < (380+tolerance)):
                degrees180 = True
                if degrees180:
                    result.append(180)
                    #print("(scanPaths) Path at 180 Degrees")

            if (self.brightness < 160) and (difference > (520 - tolerance)) and (difference < (560+tolerance)):
                degrees270 = True
                if degrees270:
                    result.append(270)
                    #print("(scanPaths) Path at 270 Degrees")

            if (self.brightness < 160) and (difference > (700 - tolerance)) and (difference < (740+tolerance)):
                degrees0 = True
                if degrees0:
                    result.append(0)
                    #print("(scanPaths) Path straight ahead")
                break 

        self.brake()
        self.resetWheels() # Stop when finished

        result = list(set(result)) # convert to set to remove double values (0 and 360 are the same)

        # converts all relative degress in absolute degress
        print("(scanPaths) Paths found in relative degrees:",result, "\tat x:", self.x, "y:", self.y)

        # it is nessary to use a new list, otherwise the for-loop will have problems
        new_result = []
        for path in result:
            new_result.append(self.calculate_relative_to_absolute(path))
        
        new_result.sort()
        print("(scanPaths) Paths found in absolute degress:", new_result, "\tat x:", self.x, "y:", self.y)

        # don't convert so set again, because if there are values twice in the list, then the code is wrong
        return new_result

    def turn(self, degrees):
        """
        After scanning path at intersection, this function will tell the robot to turn in a given direction.
        Turns counter clockwise - this is important.
        Counter clockwise works WAY LESS accurate.
        :param degrees: degrees to turn, 90, 180, 270 or 0
        """

        if (degrees != 0) and (degrees != 90) and (degrees != 180) and (degrees != 270):
            print(" ========= Invalid degrees at turn as input!! =========")

        self.brake()
        self.resetWheels()

        #print("Trying to turn " + str(degrees) + "degrees...")

        tolerance = 40

        if degrees == 90:
            lower_border = (520 - tolerance) 
            upper_border = (560 + tolerance)  
        elif degrees == 180:
            lower_border = (340 - tolerance) 
            upper_border = (380 + tolerance)
        elif degrees == 270:
            lower_border = (160 - tolerance) 
            upper_border = (200 + tolerance)  
        elif degrees == 0:
            lower_border = (0)  
            upper_border = (0) #(20) # turns to far with tolerance. Doesn't really need to turn anyway
        else:
            print("==== Invalid degrees at turn!! ====")

        difference = 0

        self.rightWheel.speed_sp = 130
        self.leftWheel.speed_sp = -130
        self.rightWheel.command = "run-forever"
        self.leftWheel.command = "run-forever"
        initial_position = self.rightWheel.position
        foundPath = False

        while (difference <= upper_border) and (degrees != 0) and (self.readButton() != True): #TODO
            difference = self.rightWheel.position - initial_position
            self.updateBrightness()

            if (self.brightness <= 150) and (difference >= lower_border) and (difference <= upper_border):
                foundPath = True
                # these degrees are relativ degrees!!
                # print("(turn) Took path:", "\trelative:", str(degrees), "\tabsolute:", str(self.calculate_relative_to_absolute(degrees)))
                #time.sleep(0.1)
                break


        #if degrees == 0:
        self.rightWheel.speed_sp = 200
        self.leftWheel.speed_sp = 130
        self.leftWheel.command = "run-forever"
        self.rightWheel.command = "run-forever"
        time.sleep(0.6)
        self.brake()
        
        if foundPath:
            pass
            # print("(turn) Found path")
        elif degrees != 0:
            print("(turn) Did not find path. Tried to turn " + str(degrees) + " degrees")


        new_direction = (self.direction + degrees) % 360
        self.direction = new_direction

        # print("(turn) New direction", self.direction, "(absolute degrees)") # absolute degrees
        
        self.initializeWheels() # Reset wheels after turning
        self.resetOdometry() # Reset odometry after turning







    # =========================== Odometry methods ===========================

    def setChessboard(self):
        """
        Sets the chessboard by determining if blue or red is even (and the other one is uneven).
        It will get called only once after it finds the first blue or red spot.
        Will be used to detect errors in odometry and automatically correct them.
        """

        if self.colorFound == "blue":
            if ((self.x + self.y) % 2) == 0:
                self.blue_even = True
                self.red_even = False
                print("(setChessboard) Blue is even")

            if ((self.x + self.y) % 2) != 0:
                self.blue_even = False
                self.red_even = True
                print("(setChessboard) Red is even")

        elif self.colorFound == "red":
            if ((self.x + self.y) % 2) == 0:
                self.blue_even = False
                self.red_even = True
                print("(setChessboard) Red is even")

            if ((self.x + self.y) % 2) != 0:
                self.blue_even = True
                self.red_even = False
                print("(setChessboard) Blue is even")

        else:
            print("==== No color found at setChessboard() ====")


        self.chessboardFound = True

    def updateOdometry(self):
        """
        Keeps track of changes in direction. 
        Will get called every 10th iteration in main loop. 
        Used for calculating the travelled distance. 
        """

        # calulates the distance traveled for each wheel
        self.dl = ((self.leftWheel.position-self.initialPositionLeft)/360)*self.circumference
        self.dr = ((self.rightWheel.position-self.initialPositionRight)/360)*self.circumference

        # calculates the difference between the wheels
        # if difference > 0 => left wheel went further => right turn
        # if difference < 0 => right wheel went further => left turn

        # difference = difference_leftwheel - difference_rightwheel

        # print("Distance left wheel:",difference_leftwheel )
        # print("Distance right wheel:", difference_rightwheel)
        # print("Difference", difference)


        # degrees alpha and beta in radians
        self.alpha = (self.dr - self.dl)/self.a
        self.beta = self.alpha/2

        # length s
        if self.alpha == 0:
            self.s = self.dr
        else:
            self.s = ((self.dl+self.dr)/self.alpha) * math.sin(self.beta)


        # delta x = cumulative change x-coordinate
        # delta y = cumulative change y-coordiante
        # gamma old = new direction
        gamma_new = self.gamma_old + self.alpha

        # delta_x and delta_y are raw values like 44
        self.delta_x += - math.sin(self.gamma_old + self.beta) * self.s
        self.delta_y += math.cos(self.gamma_old + self.beta) * self.s

        self.gamma_old = gamma_new

        self.initialPositionLeft = self.leftWheel.position
        self.initialPositionRight = self.rightWheel.position



    def determineDirection(self):
        """
        Determines the direction the robot traveled based on odometry-data.
        Will get called every time it reaches a blue or red spot.
        Calulates change of direction and change of position.
        After calculating the direction it will reset the variables so it can restart the tracking for the next segment.
        """

        gamma_degree = math.degrees(self.gamma_old)

        # set default values
        new_direction = self.direction


        # special case if it goes to a obstacle or comes from one, 
        # because the paths are shorter, since it stops before obstacle
        # self.length_segment is set to 42 in __init__
        if False: #self.obstacle_odometry:
            if (self.delta_x > 10) and (self.delta_y < (self.length_segment/2)):
                self.delta_x = self.length_segment
                print("(main loop) Obstacle - Corrected delta_x to", self.length_segment)
            elif (self.delta_x) > (-self.length_segment/2) and (self.delta_y < -10):
                self.delta_x = -self.length_segment
                print("(main loop) Obstacle - Corrected delta_x to -" + self.length_segment)
            elif (self.delta_y > 10) and (self.delta_x < (self.length_segment/2)):
                self.delta_y = self.length_segment
                print("(main loop) Obstacle - Corrected delta_y to", self.length_segment)
            elif (self.delta_y > (-self.length_segment/2)) and (self.delta_x < -10):
                self.delta_y = -self.length_segment
                print("(main loop) Obstacle - Corrected delta_y to -" + self.length_segment)
            else:
                print("(main loop) Obstacle - didn't correct delta_x or delta_y")


        print("(determineDirection) delta x:", round(self.delta_x,2), "delta y:", round(self.delta_y,2))



        # old position
        # print("(determineDirection) Old coords:", "\tx:", self.x, "\ty:", self.y)

        self.segments_moved_x = round(self.delta_x/self.length_segment)
        self.segments_moved_y = round(self.delta_y/self.length_segment)

        # positive degree => left-turn
        # negative degree => right-turn

        tolerance = 45 # tolerance in degrees

        if ((gamma_degree < (90 + tolerance)) and (gamma_degree > (90 - tolerance))):
            # print("(determineDirection) Took left turn")
            # calibration-values: left-turn: x-1 y+1

            if self.direction == 0: # north
                new_direction = 270
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_x, "\ty:", self.y, "+", self.segments_moved_y)
                self.x += self.segments_moved_x
                self.y += self.segments_moved_y

            elif self.direction == 270: # west 
                new_direction = 180
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_y, "\ty:", self.y, "+", self.segments_moved_x)
                self.x -= self.segments_moved_y
                self.y += self.segments_moved_x

            elif self.direction == 180: # south
                new_direction = 90
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_x, "\ty:", self.y, "-", self.segments_moved_y)
                self.x -= self.segments_moved_x
                self.y -= self.segments_moved_y
                
            elif self.direction == 90: # east
                new_direction = 0
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_y, "\ty:", self.y, "-", self.segments_moved_x)
                self.x += self.segments_moved_y
                self.y -= self.segments_moved_x

            else: 
                print(" ===== Error at determineDirection() ===== ", self.direction)

        elif ((gamma_degree < (-90 + tolerance)) and (gamma_degree > (-90 - tolerance))):
            # print("(determineDirection) Took right turn")
            # calibration-values: right-turn: x+1 y+1

            if self.direction == 0: # north
                new_direction = 90
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_x, "\ty:", self.y, "+", self.segments_moved_y)
                self.x += self.segments_moved_x
                self.y += self.segments_moved_y

            elif self.direction == 90: # east
                new_direction = 180
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_y, "\ty:", self.y, "-", self.segments_moved_x)
                self.x += self.segments_moved_y
                self.y -= self.segments_moved_x

            elif self.direction == 180: # south
                new_direction = 270
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_x, "\ty:", self.y, "-", self.segments_moved_y)
                self.x -= self.segments_moved_x
                self.y -= self.segments_moved_y

            elif self.direction == 270: # west
                new_direction = 0
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_y, "\ty:", self.y, "+", self.segments_moved_x)
                self.x -= self.segments_moved_y
                self.y += self.segments_moved_x

            else: 
                print(" ===== Error at determineDirection() ===== ", self.direction)

        elif ((gamma_degree < (-270 + tolerance)) and (gamma_degree > (-270 - tolerance))):
            # print("(determineDirection) Took right turn loop")
            # right turn loop
            if self.direction == 0:
                new_direction = 270
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_x, "\ty:", self.y, "+", self.segments_moved_y)
                self.x += self.segments_moved_x 
                self.y += self.segments_moved_y

            elif self.direction == 90:
                new_direction = 0
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_y, "\ty:", self.y, "-", self.segments_moved_x)
                self.x += self.segments_moved_y
                self.y -= self.segments_moved_x

            elif self.direction == 180:
                new_direction = 90
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_x, "\ty:", self.y, "-", self.segments_moved_y)
                self.x -= self.segments_moved_x
                self.y -= self.segments_moved_y

            elif self.direction == 270:
                new_direction = 180
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_y, "\ty:", self.y, "+", self.segments_moved_x)
                self.x -= self.segments_moved_y
                self.y += self.segments_moved_x

            else: 
                print(" ===== Error at determineDirection() ===== ", self.direction)

        elif ((gamma_degree < (270 + tolerance)) and (gamma_degree > (270 - tolerance))):
            # print("(determineDirection) Took left turn loop")
            # left turn loop
            if self.direction == 0:
                new_direction = 90
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_x, "\ty:", self.y, "+", self.segments_moved_y)
                self.x += self.segments_moved_x
                self.y += self.segments_moved_y

            elif self.direction == 90:
                new_direction = 180
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_y, "\ty:", self.y, "-", self.segments_moved_x)
                self.x += self.segments_moved_y
                self.y -= self.segments_moved_x

            elif self.direction == 180:
                new_direction = 270
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_x, "\ty:", self.y, "-", self.segments_moved_y)
                self.x -= self.segments_moved_x
                self.y -= self.segments_moved_y
            
            elif self.direction == 270:
                new_direction = 0
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_y, "\ty:", self.y, "+", self.segments_moved_x)
                self.x -= self.segments_moved_y
                self.y += self.segments_moved_x
            
            else: 
                print(" ===== Error at determineDirection() ===== ", self.direction)

        elif ((gamma_degree < (180 + tolerance)) and (gamma_degree > (180 - tolerance)))\
            or ((gamma_degree < (-180 + tolerance)) and (gamma_degree > (-180 - tolerance))):
            # print("(determineDirection) Took 180 degree turn")
            # calibration-values: u-turn left: -1 0, 163
            # calibration-values: u-turn right: +1 0 -160

            if self.direction == 0: # north
                new_direction = 180
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_x, "\ty:", self.y, "+", self.segments_moved_y)
                self.x += self.segments_moved_x
                self.y += self.segments_moved_y

            elif self.direction == 270: # west 
                new_direction = 90
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_y, "\ty:", self.y, "+", self.segments_moved_x)
                self.x -= self.segments_moved_y
                self.y += self.segments_moved_x

            elif self.direction == 180: # south
                new_direction = 0
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_x, "\ty:", self.y, "-", self.segments_moved_y)
                self.x -= self.segments_moved_x
                self.y -= self.segments_moved_y
                
            elif self.direction == 90: # east
                new_direction = 270
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_y, "\ty:", self.y, "-", self.segments_moved_x)
                self.x += self.segments_moved_y
                self.y -= self.segments_moved_x

            else: 
                print(" ===== Error at determineDirection() ===== ", self.direction)

        elif (gamma_degree < (0 + tolerance)) and (gamma_degree > (0 - tolerance)):
            # print("(determineDirection) Took straight path")
            new_direction = self.direction

            # calibration-values: straight and left = -1 x, +1 y
            # calibration-values: straight and right = +1 x, +1 y

            if self.direction == 0:
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_x, "\ty:", self.y, "+", self.segments_moved_y)
                self.x += self.segments_moved_x
                self.y += self.segments_moved_y
           
            elif self.direction == 90:
                print("(determineDirection) Updated coords:", "\tx:", self.x, "+", self.segments_moved_y, "\ty:", self.y, "-", self.segments_moved_x)
                self.x += self.segments_moved_y
                self.y -= self.segments_moved_x
            
            elif self.direction == 180:
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_x, "\ty:", self.y, "-", self.segments_moved_y)
                self.x -= self.segments_moved_x
                self.y -= self.segments_moved_y
            
            elif self.direction == 270:
                print("(determineDirection) Updated coords:", "\tx:", self.x, "-", self.segments_moved_y, "\ty:", self.y, "+", self.segments_moved_x)
                self.x -= self.segments_moved_y
                self.y += self.segments_moved_x

            else: 
                print(" ===== Error at determineDirection() ===== ", self.direction)

        else:
            print(" ===== Error at determineDirection(). Can't determine turn ===== ", gamma_degree)


        # if the new coordinates don't match the chessboard-pattern it will attempt to correct the coordiantes
        if (self.colorFound == "blue") and (self.blue_even == True) and (((self.x + self.y) % 2) != 0) and (self.chessboardFound == True):
            print("(determineDirection) found blue, blue is even, but coords don't match - call correctOdometry()")
            self.correctOdometry()

        elif (self.colorFound == "blue") and (self.blue_even == False) and (((self.x + self.y) % 2) == 0) and (self.chessboardFound == True):
            print("(determineDirection) found blue, blue is NOT even, but coords don't match - call correctOdometry()")
            self.correctOdometry()

        elif (self.colorFound == "red") and (self.red_even == True) and (((self.x + self.y) % 2) != 0) and (self.chessboardFound == True):
            print("(determineDirection) found red, red is even, but coords don't match - call correctOdometry()")
            self.correctOdometry()

        elif (self.colorFound == "red") and (self.red_even == False) and (((self.x + self.y) % 2) == 0) and (self.chessboardFound == True):
            print("(determineDirection) found red, red is NOT even, but coords don't match - call correctOdometry()")
            self.correctOdometry()
        
        else:
            #print("(determineDirection) No correction for odometry needed")
            pass
        

        # print("(determineDirection) New direction:", new_direction)
        self.direction = new_direction
        print("(determineDirection) New coords:", "\tx:", self.x, "\ty:", self.y)
    
        self.resetOdometry() # reset variables for next segment

    def correctOdometry(self):
        """
        Corrects the odometry (the coordinates) based on the chessboard-pattern.
        A correction-factor will be incremented 
        until it findes which coordinate is closest to being rounded up or down 
        (and which is therefore most likely to be the wrong coordinate).
        The result can't be 100% certain but is based on what is most likely

        Will get called from determineDirection() if it doesn't match the chessboard-pattern
        """

        print("(correctOdometry) delta_x:", self.delta_x, "\tdelta_y:", self.delta_y)
        print("(correctOdometry) ============= Error at Odomoetry!")
        print("(correctOdometry) Is using a =", self.a)

        # correctOdometry() usually doesn't work. We should rather take correction from mothership
        return
        
        correction_factor = 0.01
        correction_found = False

        while (correction_found == False) and (correction_factor < 0.5):
            if (round((self.delta_x/self.length_segment) + correction_factor)) != self.segments_moved_x:
                self.x += 1
                correction_found = True
                print("(correctOdometry) Corrected x-coordinate +1")
                break

            if (round((self.delta_x/self.length_segment) - correction_factor)) != self.segments_moved_x:
                self.x -= 1
                correction_found = True
                print("(correctOdometry) Corrected x-coordinate -1")
                break

            if (round((self.delta_y/self.length_segment) + correction_factor)) != self.segments_moved_y:
                self.y += 1
                correction_found = True
                print("(correctOdometry) Corrected y-coordinate +1")
                break

            if (round((self.delta_y/self.length_segment) - correction_factor)) != self.segments_moved_y:
                self.y -= 1
                correction_found = True
                print("(correctOdometry) Corrected y-coordinate -1")
                break       

            correction_factor += 0.01

        if correction_found == False:
            print("(correctOdometry) Did NOT find correction!")


       






# =========================== Helper methods for odometry ===========================

    def calculate_relative_to_absolute(self, relative_orientation):
        """
        Takes the relative position of the path it found in scanPaths()
        and returns the absolute direction (0, 90, 180, 270)
        """

        return ((relative_orientation + self.direction) % 360)


    def calculate_absolute_to_relative(self, absolute_orientation):
        """
        Takes the absolut position (0 = north, 90 = east, 180 = south, 270 = west) 
        and calculates based on the current position which way to turn

        Allowed Parameter: 0, 90, 180, 270

        Returns relative degrees
        """        

        return ((absolute_orientation - self.direction) % 360)


    def calculate_opposite_direction(self, direction):
        """
        Takes a direction (0, 90, 180, 270) and returns the opposite direction
        """
        return ((direction + 180) % 360)






    # =========================== Sensor Methods ===========================

    def initializeSensors(self):
        """
        Get sensors ready for use.
        Will get called only once from the constructor.
        """
        self.colorSensor = ev3.ColorSensor()
        self.colorSensor.mode = 'RGB-RAW'
        print("Color sensor initialized")

        self.touchSensor_right = ev3.TouchSensor(address="2")
        self.touchSensor_left = ev3.TouchSensor(address="4")
        print("Touch sensor initialized")

        self.ultrasonicSensor = ev3.UltrasonicSensor()
        self.ultrasonicSensor.mode = 'US-DIST-CM'
        self.ultrasonicLastReading = (time.time(), self.ultrasonicSensor.value())
        print("Ultrasonic sensor initialized")

        # initialize battery and print current voltage level
        # will ony be set to a local variable because it is not used again
        battery = ev3.PowerSupply()
        battery_max = battery.max_voltage
        battery_min = battery.min_voltage
        battery_right_now = battery.measured_voltage
        battery_percent= round((((battery_right_now*10 - battery_min) / (battery_max - battery_min)) * 100),2)
        print("Battery: " + str(battery_percent) + "%")

        self.button = ev3.Button() # for manually stopping the robot during driving
        

    def checkForObstacle(self):
        """
        Checks if the robot detects an obstacle via touch or ultrasonic sensor
        Returns True, if an obstacle is detected
        """
        if (self.readTouchSensor() == True) or (self.readUltrasonicSensor() <= 160):
            print("(checkForObstacle) Obstacle detected!", "\tTouch:", self.readTouchSensor(), "\tUltrasonic:", self.readUltrasonicSensor())
            return True
        else:
            return False


    def readUltrasonicSensor(self):
        """
        :return int: The measurement of the ultrasonic sensor in centimetres
        """

        ultrasonicMaxFrequency = 0.25 # Seconds for which readings are valid

        # Only read from the sensor if the last reading was more than ultrasonicMaxFrequency seconds ago
        # According to the RoboLab documentation, the sensor locks up if you read too often
        # This check fixes that behavior
        if (time.time() - self.ultrasonicLastReading[0]) > ultrasonicMaxFrequency:
            self.ultrasonicLastReading = (time.time(), self.ultrasonicSensor.value())
        
        # print("Ultrasonic sensor reading:", time.time()-self.ultrasonicLastReading[0], self.ultrasonicLastReading[1])

        # Return the last reading
        return self.ultrasonicLastReading[1]

    def readTouchSensor(self):
        """
        :return bool: Returns true when the sensor is touched
        """
        if self.touchSensor_left.is_pressed:
            print("(readTouchSensor) Touch sensor left pressed")
            return True
        elif self.touchSensor_right.is_pressed:
            print("(readTouchSensor) Touch sensor right pressed")
            return True
        else:
            return False

    def rawColorValue(self):
        """
        Will get called from updateBrightness() to get the raw value of the color sensor
        :return Red, green, and blue components of the detected color, in the range 0-1020.
        """
        return self.colorSensor.raw

    def readButton(self):
        """
        :return bool: Returns true when any button is pressed
        """
        if self.button.any():
            return True
        else:
            return False