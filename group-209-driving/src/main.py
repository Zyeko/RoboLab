#!/usr/bin/env python3

import ev3dev.ev3 as ev3
import logging
import os
import paho.mqtt.client as mqtt
import uuid
import signal
import time
import odometry
import random
import copy
import math

from communication import Communication
from odometry import Odometry
from planet import Direction, Planet
from sound import playSound

client = None  # DO NOT EDIT


def run():
    # DO NOT CHANGE THESE VARIABLES
    #
    # The deploy-script uses the variable "client" to stop the mqtt-client after your program stops or crashes.
    # Your script isn't able to close the client after crashing.
    global client

    client_id = '209-' + str(uuid.uuid4())  # Replace YOURGROUPID with your group ID
    client = mqtt.Client(client_id=client_id,  # Unique Client-ID to recognize our program
                         clean_session=True,  # We want a clean session after disconnect or abort/crash
                         protocol=mqtt.MQTTv311  # Define MQTT protocol version
                         )
    # Setup logging directory and file
    curr_dir = os.path.abspath(os.getcwd())
    if not os.path.exists(curr_dir + '/../logs'):
        os.makedirs(curr_dir + '/../logs')
    log_file = curr_dir + '/../logs/project.log'
    logging.basicConfig(filename=log_file,  # Define log file
                        level=logging.DEBUG,  # Define default mode
                        format='%(asctime)s: %(message)s'  # Define default logging format
                        )
    logger = logging.getLogger('RoboLab')

    # THE EXECUTION OF ALL CODE SHALL BE STARTED FROM WITHIN THIS FUNCTION.
    # ADD YOUR OWN IMPLEMENTATION HEREAFTER.




    # ====================== Starting ======================

    print("Starting mission...")
    odometry = Odometry() # initialize odometry
    planet = Planet() # initialize planet
    communication = Communication(client, logger, planet) # initialize communication
    random.seed() # only needed for random exploration




    # ====================== Calibration & Testing Sensors ======================
    calibrationMode = 0 # TODO set 0 for driving

    if calibrationMode != 0:
        if calibrationMode == 1:
            calibrationModeColor(odometry)

        elif calibrationMode == 2:
            calibrationModeDegrees(odometry)

        elif calibrationMode == 3:
            printColor(odometry)

        elif calibrationMode == 4:
            printUltrasonicSensor(odometry)

        elif calibrationMode == 5:
            measureLengthLine(odometry)
        
        elif calibrationMode == 6:
            printTouchSensor(odometry)

        elif calibrationMode == 7:
            tryButtons(odometry)

        else:
            return # exit program


    # ====================== Start driving ======================
    else:


        # ====================== Set test planet ======================

        # remove for exam TODO
        test_planets = {1:"Schoko", 2:"Ferdidand", 3:"Fassaden", 4:"Mehl"}
        planet_name = test_planets.get(1)


        communication.send_message("explorer/209", {"type": "testPlanet", "from":"client", "payload": {"planetName": planet_name}})
        # communcation.send_ready() #TODO testen und raussuchen, was man genau bei Exam senden muss!!!!

        victory = False
        odometry.initializeWheels()
        iteration = 1
        firstField = True
        
        # ====================== Main Loop ======================
        while victory == False:
            odometry.updateBrightness() # nessesary every increment
            odometry.checkColor()
            odometry.checkForField()
            
            # if not at color field, keep driving
            if odometry.field == None:
                odometry.PID()
            




            # ====================== Found Field ======================
            else:
                odometry.driveABitForward() # drives to the middle of field, must be first

                if firstField:
                    communication.send_ready()
                    while (communication.planet == None) or (communication.pos_x == None) or (communication.pos_y == None) or (communication.direction == None):
                        # waits for answers from the server
                        pass
                    print("(main loop) Got starting position:", (communication.pos_x, communication.pos_y), "and direction", communication.direction)

                    # sets server values
                    odometry.x = communication.pos_x
                    odometry.y = communication.pos_y
                    odometry.direction = communication.direction

                    # sets the path from which it came to blocked
                    blocked_start = (communication.pos_x, communication.pos_y), odometry.calculate_opposite_direction(communication.direction)
                    planet.add_path(blocked_start, blocked_start, -1)


                # ====================== Set Chessboard ======================
                if odometry.chessboardFound == False:
                    odometry.setChessboard()




                # doesn't check on first/starting field on map 
                if firstField == False:
                    old_x = odometry.x
                    old_y = odometry.y
                    start = (old_x, old_y), path_taken




                # ====================== Determine direction ======================
                # only use odometry, if it doesn't come from an obstacle...or if it's not first field
                if (odometry.comes_from_obstacle == True) or (firstField == True):
                    odometry.resetOdometry()
                    if odometry.comes_from_obstacle:
                        pass
                        #print("(main loop) Comes from obstacle, resets odometry")
                    if firstField:
                        pass
                        #print("(main loop) First field, resets odometry")
                elif firstField == False:
                    odometry.determineDirection() # calculate direction traveled when standing. Don't update odometry again!!


                
                
            

                # ====================== Keep Track of Paths ======================
                entered_in = odometry.calculate_opposite_direction(odometry.direction)
                print("(main loop) entered in:", entered_in)
                # add path to planet
                if (firstField == False) and (odometry.comes_from_obstacle == False):
                    target = (odometry.x, odometry.y), entered_in
                    weight = math.inf     # ========== TODO update this!!!
                    #planet.add_path(start, target, weight)

                odometry.comes_from_obstacle = False



                # ====================== Communicate Position and Direction to Server and maybe get corrected ======================
                # send position to server (use start and target previously set)
                if firstField == False:
                    com_start_x = start[0][0]
                    com_start_y = start[0][1]
                    com_start_direction = start[1]
                    com_target_x = target[0][0]
                    com_target_y = target[0][1]
                    com_target_direction = target[1]

                    if weight == -1:
                        com_pathStatus = "blocked"

                        if (com_start_x != com_target_x) or (com_start_y != com_target_y) or (com_start_direction != com_target_direction):
                            print("(Server Communication) ====== Error: start and target must be equal at blocked paths")

                    else:
                        com_pathStatus = "free"
                    communication.send_path_taken(com_start_x, com_start_y, com_start_direction, com_target_x, com_target_y, com_target_direction, com_pathStatus)



                    # wait for correction
                    time.sleep(3) # TODO maybe improve this somehow
                    if (communication.pos_old_x != com_start_x) or\
                        (communication.pos_old_y != com_start_y) or\
                        (communication.old_direction != com_start_direction) or\
                        (communication.pos_x != com_target_x) or\
                        (communication.pos_y != com_target_y) or\
                        (communication.direction != com_target_direction) or \
                        (communication.path_status != com_pathStatus):                        
                        print("(Server Communication) ===== Our path might not be correct!")
                    
                    old_x = communication.pos_old_x
                    old_y = communication.pos_old_y
                    path_taken = communication.old_direction
                    odometry.x = communication.pos_x
                    odometry.y = communication.pos_y
                    odometry.direction = communication.direction
                    com_pathStatus = communication.path_status
                    weight = communication.path_weight

                    start = (old_x, old_y), path_taken
                    entered_in = odometry.direction
                    target = (odometry.x, odometry.y), entered_in

                    planet.add_path(start, target, weight)

                    odometry.direction = odometry.calculate_opposite_direction(communication.direction)
                    print("(Server commuication) Direction right now:", odometry.direction)


                




                # ====================== Check if field is known ======================
                #print("(main loop) Checking if", (odometry.x, odometry.y), "is known")
                #print("(main loop) planet.known_fields:", planet.known_fields)

                paths_found = []
                # field is known and scanned
                if ((odometry.x, odometry.y) in planet.fields_scanned):
                    paths_found = copy.deepcopy(planet.known_fields.get((odometry.x, odometry.y)))
                    # print("(main loop) Field already known, using paths_found:", paths_found)
                
                # field is not known and therefore not scanned
                else:
                    paths_found = odometry.scanPaths()
                    planet.fields_scanned.append((odometry.x, odometry.y))
                    planet.known_fields.update({((odometry.x, odometry.y)): (copy.deepcopy(paths_found))})
                    print("(main loop) Field not known, adding paths_found:", paths_found)

                    #print("(main loop) New Field added - Known fields:", planet.known_fields)




                # ====================== Detect Errors in paths_found ======================
                if (paths_found.count(0) > 1) or (paths_found.count(90) > 1) or (paths_found.count(180) > 1) or (paths_found.count(270) > 1):
                    # TODO take all that out
                    print("(main loop) ====== Found value twice!! ======")
                    print("Error details:")
                    print("Entered in:", entered_in)
                    print("Direction:", odometry.direction)
                    print("Found Paths:", paths_found)
                    print("Scanned fields:", planet.fields_scanned)
                    print("Paths in planet.known_fields", planet.known_fields)
                    print("Position x:", odometry.x, "y:", odometry.y, "(Might be not updated)")
                    relativ_paths = []
                    for path in paths_found:
                        relativ_paths.append(odometry.calculate_absolute_to_relative(path))
                    print("Relative Paths:", relativ_paths)
                    break






                # ====================== Smart Exploration ======================
                use_random_exploration = True
                paths = copy.deepcopy(planet.get_paths())
                known_paths = []
                # print("(smart exploration) paths:", paths)
                

                # field should always exist, except when reaching starting position/first field
                if firstField == False:
                    for direction in paths.get((odometry.x,odometry.y)):
                        known_paths.append(direction)
                    print("(smart exploration) Known paths from this field from known_paths:", known_paths,"\t", (odometry.x, odometry.y))
                    print("(smart exploration) Known paths from this field from paths_found:", paths_found,"\t", (odometry.x, odometry.y))
                    print("(smart exploration) len(paths_found):", len(paths_found), "len(known_paths):", len(known_paths))
                
                    # if there are unknown paths
                    if len(paths_found) > len((known_paths)):
                        use_random_exploration = False
                        unknown_paths = []
                        for path in paths_found:
                            if path not in known_paths:
                                unknown_paths.append(path)
                        
                        print("(smart exploration) Unknown paths:", unknown_paths, "at", (odometry.x, odometry.y))
                        pick_path = random.randint(1,len(unknown_paths))
                        
                        path_taken = unknown_paths[pick_path-1]


                # ====================== Random Exploration ======================
                # it needs to use random-exploration if all paths are known
                # therefore it only uses smart-exploration if there are unknown paths


                # if there are NO unknown paths or first field
                if use_random_exploration == True:
                    #print("(smart exploration) Use Random Exploration")
                    pick_path = random.randint(1,len(paths_found))

                    blocked_direction = []
                    # it is more important to not go to a blocked path than going backwards
                    if firstField == False:
                        for value in paths.get((odometry.x,odometry.y)).values():
                            if value[2] == -1:
                                blocked_direction.append(value[1])
                                print("(smart exploration) Blocked_directions:", blocked_direction)
                                while paths_found[pick_path-1] in blocked_direction: 
                                    pick_path = random.randint(1,len(paths_found)) # pick random path, other than 180

                    if blocked_direction == []:
                    # disable going backwards # TODO
                    # print("(main loop) Try to not go backwards by checking:", odometry.calculate_opposite_direction(entered_in))
                        if (entered_in in paths_found) and (len(paths_found) > 1):
                            while paths_found[pick_path-1] == entered_in: 
                                pick_path = random.randint(1,len(paths_found)) # pick random path, other than 180
                    
                    path_taken = paths_found[pick_path-1]


                # ====================== Send path_select ======================
                communication.path_select = None # reset path_select
                communication.send_path_select(odometry.x, odometry.y, path_taken)
                time.sleep(3) #TODO I should only need one sleep timer




                # ====================== Pick shortest path to target, if possible ======================
                # overwrite path_taken if we have a target
                if (communication.got_target_x != None) and (communication.got_target_y != None):
                    print("(Server communication) We've got a target:", (communication.got_target_x, communication.got_target_y))
                    shortest_path = planet.shortest_path((odometry.x, odometry.y), (communication.got_target_x, communication.got_target_y))
                    print("(Server communication) Shortest path to target:", shortest_path)

                    if shortest_path != None:   
                        if shortest_path == []:
                            print("(Server communication) We are done!")
                            communication.send_target_reached()
                            time.sleep(5)
                            if communication.done == True:
                                print("(Server communication) Server answered done!")
                                victory = True
                            else:
                                print(" ======== Huston, we have a problem!! We think we are done, but Server doesn't confirm! ")
                            break

                        if (shortest_path[0][0] == (odometry.x, odometry.y)):
                            path_taken = shortest_path[0][1]
                            print("(Server communication) Using shortest path is possible from current position, using this path:", path_taken)





                # ====================== Use path select if available ======================
                # path_select has the highest priority, so it will be called last to overwrite path_taken
                if communication.path_select != None:
                    path_taken = communication.path_select






                # ====================== Keep track of unknown paths ======================
                paths = copy.deepcopy(planet.get_paths())
                unknown_fields = copy.deepcopy(planet.known_fields)

                for field in paths.keys():
                    for direction in paths.get(field).keys():


                        # remove known paths
                        unknown_fields.get(field).remove(direction)

                        # get rid of field with no more unknown paths
                        if unknown_fields.get(field) == []:
                            unknown_fields.pop(field)

                print("(main loop) Unknown fields/paths", unknown_fields)

                if (len(unknown_fields.keys()) == 0) and (planet.known_fields != {}) and len(paths.keys()) > 3:
                    print("(main loop) All fields known - I think I'm done!")
                    if (shortest_path != None) or (shortest_path != []):
                        print("(Server communication) We still have a target!")
                    else:
                        communication.send_exploration_completed()
                        time.sleep(5)
                        if communication.done == True:
                            print("(Server communication) Server answered done!")
                            victory = True
                            break
                


                # ====================== Turn and Drive to next field ======================
                odometry.turn(odometry.calculate_absolute_to_relative(path_taken))
                print("(main loop) Path taken:", path_taken)
                firstField = False




            # ====================== Update Odometry ======================
            if (iteration % 10) == 0: # 10 is enough but 5 would work too
                odometry.updateOdometry() # update direction traveled
            iteration += 1




            # ====================== Found Obstacle, i.e. Blocked Path ======================
            if odometry.checkForObstacle(): 
                old_x = odometry.x
                old_y = odometry.y
                start = (old_x, old_y), path_taken
               
                odometry.comes_from_obstacle = True
                #odometry.determineDirection()
                path_taken = odometry.direction
                print("(main loop) Path_taken updated:", path_taken)

                # print("(main loop) Detected obstacle at", "x:", odometry.x, "y:", odometry.y)

                target = start
                weight = -1
                planet.add_path(start, target, weight) # -1 = blocked path

                odometry.turn(180) # turn around after finding obstacle
            


            # the robot can be manually stopped by pressing a button
            if (odometry.readButton() == True):
                break


        # ====================== end of main loop ======================

        odometry.brake()
        odometry.resetWheels()
        print("Mission completed!")
        print("="*100)

        final_paths = planet.get_paths()
        for key in final_paths.keys():
            print("All known paths from:", key, final_paths.get(key))

        paths = final_paths
        unknown_fields = copy.deepcopy(planet.known_fields)

        for field in paths.keys():
            for direction in paths.get(field).keys():
                unknown_fields.get(field).remove(direction)
                if unknown_fields.get(field) == []:
                    unknown_fields.pop(field)

        print("(main loop) Unknown fields", unknown_fields)

        if victory:
            print("VICTORY!")
            #TODO











# ====================== Testing- & Calibration-Modes ======================

def calibrationModeColor(odometry):
    """
    Can be used to calibrate the light sensor. 
    It prints RGB- and brightness-values.
    Activating the touch-sensor ends the method.  
    """

    while (odometry.checkForObstacle() != True):

        odometry.rgb = odometry.rawColorValue()
        odometry.updateBrightness()


        # for calibration color detection
        print("RGB:\t", odometry.rawColorValue())

        # for calibration black strip
        
        print("Light:\t", int(odometry.brightness))
        time.sleep(1)

def calibrationModeDegrees(odometry):
    """
    Is for the calibration of the ability to turn at an intersection.
    (0, 90, 180 or 270 degree turn) 
    It is based on the position of the wheels.
    Activating the touch-sensor ends the method.  
    """
    odometry.resetWheels()

    initial_position = odometry.leftWheel.position
    # print("initial position:", initial_position)

    odometry.updateBrightness()

    while (odometry.checkForObstacle() != True):
        odometry.rightWheel.speed_sp = -130 # try different values
        odometry.leftWheel.speed_sp = 130
        odometry.leftWheel.command = "run-forever"
        odometry.rightWheel.command = "run-forever"
        odometry.updateBrightness()
        difference = odometry.leftWheel.position - initial_position
        if odometry.brightness <= 130:
            print(difference)
            
        if difference > 770:
            odometry.resetWheels()
            break

def printColor(odometry):
    """
    Prints which color the colorsensor is seeing.
    Also prints if it recognizes a field (must see the color at least twice to reduce false positives).
    Possible colors are: red, blue, none
    Activating the touch-sensor ends the method.
    """
    blue = 0
    red = 0
    while (odometry.checkForObstacle() != True):
        odometry.updateBrightness()
        odometry.checkColor()
        print(odometry.colorFound)

        if (odometry.colorFound == "blue"):
            blue += 1
            red = 0
            if blue >= 2: # it needs to see blue twice to reduce false positives
                print("Field found: blue")

        elif (odometry.colorFound == "red"):
            red += 1
            blue = 0
            if red >= 2: # # it needs to see red twice to reduce false positives
                print("Field found: red")

        else:
            # Reset to default values to begin counting again
            red = 0
            blue = 0


def printUltrasonicSensor(odometry):
    """
    Prints the value of the ultrasonic sensor.
    Activating the touch-sensor ends the method.
    """
    while (odometry.readTouchSensor() != True):
        value = odometry.readUltrasonicSensor()
        print(value)
        if (value < 160):
            print ("Obstacle found!")
        time.sleep(0.5)

def printTouchSensor(odometry):
    """
    Prints the value of the touch sensor.
    Methods automaticly ends after a little while.
    """
    duration = 500
    for time in range (duration):
        print(time, "/", duration, odometry.readTouchSensor())


def measureLengthLine(odometry):
    """
    Measures the length of a straight line between to spots.
    This is better than just hardcoding the length of 50 cm,
    because it is more important what the robot sees than the actual length.
    Reaching a blue or red field ends the method.
    """

    odometry.initializeWheels()
    iteration = 1
    while (odometry.checkForObstacle() != True):
        odometry.updateBrightness()
        odometry.checkColor()
        odometry.checkForField()
        
        # if not at color field (usually but NOT always intersection)
        if odometry.field == "blue" or odometry.field == "red":
            odometry.updateOdometry()
            print("Distance traveled:", odometry.delta_x, odometry.delta_y)
            break
        else:
            odometry.PID()

        if (iteration % 1) == 0: 
            odometry.updateOdometry() # update direction traveled
        iteration += 1
            
    odometry.brake()
    odometry.resetWheels()
    print("Finished measuring Line!")

def tryButtons(odometry):
    """
    Tries the buttons.
    Activating the touch-sensor ends the method.
    """
    while (odometry.readTouchSensor() != True):
        if odometry.button.backspace:
            print("Backspace")
        if odometry.button.enter:
            print("Enter")
        if odometry.button.left:
            print("Left")
        if odometry.button.right:
            print("Right")
        if odometry.button.up:
            print("Up")
        if odometry.button.down:
            print("Down")
        if odometry.button.any():
            print("Any")
        






# DO NOT EDIT
def signal_handler(sig=None, frame=None, raise_interrupt=True):
    if client and client.is_connected():
        client.disconnect()
    if raise_interrupt:
        raise KeyboardInterrupt()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    try:
        run()
        signal_handler(raise_interrupt=False)
    except Exception as e:
        signal_handler(raise_interrupt=False)
        raise e
