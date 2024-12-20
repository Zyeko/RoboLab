#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
from asyncio.log import logger
import json
import ssl
import logging
import paho.mqtt.client as mqtt
import time


class Communication:
    """
    Class to hold the MQTT client communication
    Feel free to add functions and update the constructor to satisfy your requirements and
    thereby solve the task according to the specifications
    """

    # DO NOT EDIT THE METHOD SIGNATURE
    def __init__(self, mqtt_client, logger, planet_object):
        """
        Initializes communication module, connect to server, subscribe, etc.
        :param mqtt_client: paho.mqtt.client.Client
        :param logger: logging.Logger
        """
        # DO NOT CHANGE THE SETUP HERE
        self.client = mqtt_client
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        self.client.on_message = self.safe_on_message_handler
        # Add your client setup here
        self.logger = logger
        self.client.username_pw_set('209',
                           password='Txc5idlg4N')

        self.client.connect('mothership.inf.tu-dresden.de', port=8883)
        self.client.subscribe('explorer/209', qos=2)
        self.client.loop_start()

        self.planet = None
        self.pos_x = None
        self.pos_y = None
        self.direction = None
        self.path_select = None

        self.pos_old_x = None
        self.pos_old_y = None
        self.old_direction = None
        self.path_status = None
        self.path_weight = None 
        self.planet_object = planet_object

        self.got_target_x = None
        self.got_target_y = None
        self.done = False



    # DO NOT EDIT THE METHOD SIGNATURE
    def on_message(self, client, data, message):
        """
        Handles the callback if any message arrived
        :param client: paho.mqtt.client.Client
        :param data: Object
        :param message: Object
        :return: void
        """
        payload = json.loads(message.payload.decode('utf-8'))
        self.logger.debug(json.dumps(payload, indent=2))

        # print("(on message) Message from server:")
        # print(json.dumps(payload, indent=2))



        # ====================== From us ======================
        if payload.get("from") == "client":
            print("(on message) Message from us:", payload.get("type"), payload.get("payload"))





        # ====================== From server ======================
        if payload.get("from") == "server":

            # ====================== Planet ======================
            if payload.get("type") == "planet":
                print("(on message) Got planet from Server:", payload.get("payload"))
                self.planet = payload.get("payload").get("planetName")
                print("(on message) Planet:", self.planet)

                self.pos_x = payload.get("payload").get("startX")
                self.pos_y = payload.get("payload").get("startY")
                #print("(on message) Start coords:", (self.start_x, self.start_y))

                self.direction = payload.get("payload").get("startOrientation")
                #print("(on message) Start direction:", self.start_direction)

                self.client.subscribe("planet/" + self.planet + "/209", qos=2)


            



            # ====================== pathUnveiled ======================
            elif payload.get("type") == "pathUnveiled":
                print("(on message) Got pathUnveiled from Server:", payload.get("payload"))

                # send to planet.add_path()
                path_start_x = payload.get("payload").get("startX")
                path_start_y = payload.get("payload").get("startY")
                path_start_direction = payload.get("payload").get("startDirection")
                path_end_x = payload.get("payload").get("endX")
                path_end_y = payload.get("payload").get("endY")
                path_end_direction = payload.get("payload").get("endDirection")
                path_weight = payload.get("payload").get("pathWeight")

                self.planet_object.add_path(((path_start_x, path_start_y), path_start_direction), ((path_end_x, path_end_y), path_end_direction), path_weight)







            # ====================== target ======================
            elif payload.get("type") == "target":
                print("(on message) Got target from Server:", payload.get("payload"))

                # there will only ever be one target!
                # if there is a new target, overwrite the old one!

                self.got_target_x = payload.get("payload").get("targetX")
                self.got_target_y = payload.get("payload").get("targetY")





            # ====================== path select ======================
            elif payload.get("type") == "pathSelect":
                print("(on message) Got pathSelect from Server:", payload.get("payload"))
                self.path_select = payload.get("payload").get("startDirection")



            # ====================== Answer for our path ======================
            elif payload.get("type") == "path":
                print("(on message) Got path from Server:", payload.get("payload"))
                self.pos_old_x = payload.get("payload").get("startX")
                self.pos_old_y = payload.get("payload").get("startY")
                self.old_direction = payload.get("payload").get("startDirection")
                self.pos_x = payload.get("payload").get("endX")
                self.pos_y = payload.get("payload").get("endY")
                self.direction = payload.get("payload").get("endDirection")
                self.path_status = payload.get("payload").get("pathStatus")
                self.path_weight = payload.get("payload").get("pathWeight")



            # ====================== done ======================
            elif payload.get("type") == "done":
                print("(on message) Got done from Server:", payload.get("payload"))
                self.done = True

            #elif payload.get("type") == "syntax":
                #print("(on message) Got syntax from Server:", message.get("payload"))


            # ====================== debug ======================
            elif payload.get("from") == "debug":
                print("(on message) Got debug from Server:", payload.get("payload"))

            else:
                print("(on message) Got unknown message from Server: " + payload.get("type") + " from " + payload.get("from") +": "+ payload.get("payload"))






    def send_ready(self):
        self.send_message("explorer/209", {"type": "ready", "from":"client"})


        # DO NOT EDIT THE METHOD SIGNATURE
        #
        # In order to keep the logging working you must provide a topic string and
        # an already encoded JSON-Object as message.



    def send_path_taken(self, start_x, start_y, start_direction, target_x, target_y, target_direction, pathStatus):
        if (pathStatus != "free") and (pathStatus != "blocked"):
            print("(send_path_taken) Error: pathStatus must be free or blocked")
        self.send_message("planet/"+self.planet+"/209", {"type": "path", "from":"client", "payload": {"startX": start_x, "startY": start_y, "startDirection": start_direction, "endX": target_x, "endY": target_y, "endDirection": target_direction, "pathStatus": pathStatus}})


    def send_path_select(self, start_x, start_y, start_direction):
        self.send_message("planet/"+self.planet+"/209", {"type": "pathSelect", "from":"client", "payload": {"startX": start_x, "startY": start_y, "startDirection": start_direction}})


    def send_target_reached(self):
        self.client.subscribe("explorer/209", qos=2)
        self.send_message("explorer/209", {"type": "targetReached", "from":"client", "payload": {"message": "Finished!"}})

    def send_exploration_completed(self):
        self.client.subscribe("explorer/209", qos=2)
        self.send_message("explorer/209", {"type": "explorationCompleted", "from":"client", "payload": {"message": "Finished!"}})





    def send_message(self, topic, message):
        """
        Sends given message to specified channel
        :param topic: String
        :param message: Object
        :return: void
        """
        self.logger.debug('Send to: ' + topic)
        self.logger.debug(json.dumps(message, indent=2))

        self.client.publish(topic, json.dumps(message), qos=2)


    # DO NOT EDIT THE METHOD SIGNATURE OR BODY
    #
    # This helper method encapsulated the original "on_message" method and handles
    # exceptions thrown by threads spawned by "paho-mqtt"
    def safe_on_message_handler(self, client, data, message):
        """
        Handle exceptions thrown by the paho library
        :param client: paho.mqtt.client.Client
        :param data: Object
        :param message: Object
        :return: void
        """
        try:
            self.on_message(client, data, message)
        except:
            import traceback
            traceback.print_exc()
            raise
