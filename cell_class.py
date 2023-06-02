import json
#import aiomqtt as aiomqtt
import asyncio_mqtt as aiomqtt
from asyncua import ua, Server, Client
from asyncua.common.methods import uamethod
import asyncio
import logging
# JSON telegram template classes
import cell_json_telegrams as json_telegrams
import sys
import aioconsole
sys.path.insert(0, "..")
# TODO:
# 1. Move all simulation / dummy functions to a separate file.
# 2. Error handling should be done in start state, before actually executing.
# 3. Implement start state before we can start the palletizing job
# 4. Add un-suspending state.


"""
This is the class for the palletizing cell. It contains all the functions and variables needed to run the cell.
The cell is controlled by the HLC and communicates with it using MQTT.
The cell also communicates with the ER system using OPC UA.
The cell class and all related functions use the async/await syntax to allow for asynchronous programming.
Meaning that the cell can do multiple things at once, such as listening for MQTT messages and communicating with the ER system.
A normal state machine is therefore not used, but instead the state of the cell is updated according to the state of the task.
The flow of the program therefore still follows the state machine approach, but can still do other things while waiting for a state change.

As an example, this will allow the cell to handle background task, such as handling requests from the HLC, while also handling the palletizing process.


The Cell class contains the following functions:
- start_layer() - This is the primary function after the main function, and is used to handle the entire palletizing process.
- palletize_layer_dummy() - This is a dummy function that simulates the palletizing process.
- state_updater() - This function monitors the state of the cell and sends a telegram to the HLC when the state changes or when the HLC requests it.
- request_handler() - This function handles the request telegrams from the HLC.
- subcribe_handler() - This function handles the subscribe telegrams from the HLC that the main function need.
- pattern_handler() - This function handles the pattern telegrams sent from the HLC.
- opc_ua_handler() - This function handles the OPC UA communication with the ER system.
- wait_for_user_input() - This function is used for debugging and is not used in the final version.
- main() - This is the main function of the cell, and is used to set up all async functions and start the cell.
"""



class Cell:
    def __init__(self, prefix, id):
        # Cell specific variables
        self.cell_id = id
        self.cell_prefix = prefix
        self.client = None
        
        # MQTT topics
        self.start_layer_topic = self.cell_prefix + "/" + self.cell_id + "/palletize/start-layer"
        self.state_request_topic = self.cell_prefix + "/" + self.cell_id + "/requests"
        self.state_change_request_topic = self.cell_prefix + "/" + self.cell_id + "/requests/state-change"
        self.state_feedback_topic = self.cell_prefix + "/" + self.cell_id + "/system/state"
        self.transport_request_topic = self.cell_prefix + "/" + self.cell_id + "/request/transport"
        
        # System alarms
        self.system_alarm = None # Will be defined in main
        
        
        # System state variables
        self.old_state = "Offline"
        self.state = "Idle"
        
        self.task_id = "0"
        self.pallet_place_id = "0"
        self.pallet_error_code_id = "0"
        self.pallet_status_id = "0"
        self.ur_response = "0"
        self.reset_opcua_vars = False
        self.system_state = json_telegrams.system_state(self.cell_prefix, self.cell_id, self.client, self.state)
        self.HCL_state_request = False
        
        # Pick and place variables
        self.from_location_id = None
        self.to_location_id = None
        self.item_id = None
        
        #self.opc_ua_server, self.opc_ua_idx, self.opc_ua_logger = 
        
    
    """async def start_OPC_UA_server(self):
        # Start OPC UA server
        _logger = logging.getLogger('asyncua')
        # setup our server
        server = Server()
        await server.init()
        server.set_endpoint('opc.tcp://192.168.12.103:4840/server/')
        #server.set_endpoint('opc.tcp://localhost:4840/server/') 
        # setup our own namespace, not really necessary but should as spec
        uri = 'http://examples.freeopcua1.github.io'
        idx = await server.register_namespace(uri)
        
        myobj = await server.nodes.objects.add_object(idx, 'palletizing_object')
        pallet_place = await myobj.add_variable(idx, 'pallet_place', str(0)) # initialized as 0, can be 1 to 3 
        task = await myobj.add_variable(idx, 'task', str(0)) # initialized as 0, can be 1 to 4
        pallet_status = await myobj.add_variable(idx, 'pallet_status', str(0)) # initialized as 0, can be 1 to 4
        pallet_error_code = await myobj.add_variable(idx, 'pallet_error_code', str(0)) # initialized as 0, can be 1 to 4
    
        await pallet_place.set_writable()
        async with server:
            while True:
        return server, idx, _logger"""
        
    
    # 5.5.1 Start Palletizing Single Layer (HLC -> PLC)
    async def start_layer(self):
        """This is the primary function of the cell and handles the entire palletizing process.
           It listens for start layer telegrams from the HLC and starts the palletizing process.
           It also updates the state according to the state of the task, and handles if the HLC requests a state change.
           OPC UA variables are also updated according to the state of the cell.
           
           NOTE: As of now, the palletizing process is simulated.
        """   
        async with self.client.messages() as messages:
            async for message in messages:
                if message.topic.matches(self.start_layer_topic):
                    if self.state == "Idle":
                        obj = json.loads(message.payload) # get the json string and convert it to a python dictionary
                        print("Starting layer with layer_pattern id : " + str(obj["layer_pattern_id"]))
                        self.pallet_place_id = str(int(obj["start_index"])+1) # Set palletizing place id for OPC UA
                        print("Starting layer with height_offset : " + str(obj["height_offset"]))
                        print("Sent at : " + str(obj["timestamp"]))
                        self.state = "Starting"
                        await asyncio.sleep(3)
                        ret = await self.palletize_layer_demo2(obj)
                        if ret == False:
                            print("Error palletizing layer")
                            self.state = "Error"
                            print("Layer error. state = " + self.state)
                    else:
                        print("Error: Received start layer telegram while not in Idle state")
                        await json_telegrams.send_error_message(self.state_feedback_topic, self.client, "ERR_INVALID_STATE")
                     
    async def pick_place (self):
        async def reset_values():
            self.from_location_id = None
            #self.to_location_id = None
            #self.item_id = None
        while True:
            if (self.from_location_id == None):
                await asyncio.sleep(1)
            else:
                self.state = "Starting"
                await asyncio.sleep(1)
                print("Moving", self.item_id, "from", self.from_location_id, "to", self.to_location_id)
                if self.from_location_id == "container_tray" and self.to_location_id == "left_spot":
                    await reset_values()
                    print("Picking from container tray and placing left spot")
                    await self.run_ur_program("1")
                elif self.from_location_id == "technicon_cell" and self.to_location_id == "right_spot":
                    print("Picking from technicon_cell and placing on right spot")
                    await reset_values()
                    await self.run_ur_program("2")
                elif (self.from_location_id == "left_spot" and self.to_location_id == "technicon_cell"):
                    print("Picking from left spot to technicon cell")
                    await reset_values()
                    await self.run_ur_program("3")
                else:
                    print("Invalid pick and place")
                    await reset_values()
                await asyncio.sleep(1)
                #running_task = False
    
    async def run_ur_program(self, task_id, container_palletized_handler = None):
        self.state = "Execute"
        self.task_id = task_id
        await self.opc_ua_update_items()
        while(self.ur_response != "1"):
            await asyncio.sleep(1)
        print("received ur response")
        self.task_id = "0"
        while(self.pallet_status_id != "1"):
            await asyncio.sleep(1)
        if task_id != "4":
            await json_telegrams.container_at_location(self.cell_prefix, self.cell_id, self.client, self.to_location_id, self.item_id)
        if container_palletized_handler != None:
            print("Container placed on pallet")
            await container_palletized_handler.send_telegram()
        self.state = "Complete"
        await asyncio.sleep(1)
        self.state = "Resetting"
        self.reset_opcua_vars = True
        self.state = "Idle"
    
    async def palletize_layer_demo2(self, obj):
        layer_pattern_id = obj["layer_pattern_id"]
        # load layer pattern from database
        layer_pattern_filename = "layer_patterns/" + str(layer_pattern_id) + ".json"
        try :
            with open(layer_pattern_filename) as json_file:
                layer_pattern = json.load(json_file)
        except:
            print("Error loading layer pattern")
            alarm_id = "52"
            alarm_text = "Error: Layer pattern with ID: " + str(layer_pattern_id)+ " not found"
            active = True
            print("Setting alarm", alarm_id, "to", active)
            await json_telegrams.add_alarm_state(self.cell_prefix, self.cell_id, self.client, alarm_id, alarm_text, active, self.system_alarm) # Set alarm and send telegram 
            return False
        # Extraxt info from the received json object
        start_index = obj["start_index"]
        num_containers = obj["num_containers"]
        height_offset = obj["height_offset"]
        pallet_location_id = obj["pallet_location_id"]
        
        # Extract the container pattern from the layer pattern
        container_pattern= layer_pattern["containers"]
        
        # Validate that the layer pattern and the start index and num containers are valid
        if start_index + num_containers > len(container_pattern):
            print("Error: start index and num containers are invalid")
            alarm_id = "51"
            alarm_text = "Error: start index and num containers are invalid"
            active = True
            print("Setting alarm", alarm_id, "to", active)
            await json_telegrams.add_alarm_state(self.cell_prefix, self.cell_id, self.client, alarm_id, alarm_text, active, self.system_alarm) # Set alarm and send telegram  
            return False
        print("Started palletizing ", num_containers, " containers")
        
        container_arrival_handler = json_telegrams.container_ID_point(
            self.cell_prefix, 
            self.cell_id, 
            self.client,)
        
        container_palletized_handler = json_telegrams.container_palletized(
            self.cell_prefix,
            self.cell_id, 
            self.client, 
            pallet_location_id, 
            layer_pattern_id,
            height_offset,)
        for i in range(start_index, start_index + num_containers): 
            await asyncio.sleep(3)
            print("Container arrived at ID point : ", layer_pattern_id)
            container_arrival_handler.position_id = layer_pattern_id
            await container_arrival_handler.send_telegram()
            await asyncio.sleep(1)
            # Wait UR robot to update pallet_status_id to 1
            container_palletized_handler.index = layer_pattern_id
            await self.run_ur_program("4", container_palletized_handler)
        return True
        
    
    async def palletize_layer_dummy(self, obj):
        layer_pattern_id = obj["layer_pattern_id"]
        # load layer pattern from database
        layer_pattern_filename = "layer_patterns/" + str(layer_pattern_id) + ".json"
        try :
            with open(layer_pattern_filename) as json_file:
                layer_pattern = json.load(json_file)
        except:
            print("Error loading layer pattern")
            return False
        # Extraxt info from the received json object
        start_index = obj["start_index"]
        num_containers = obj["num_containers"]
        height_offset = obj["height_offset"]
        pallet_location_id = obj["pallet_location_id"]
        
        # Extract the container pattern from the layer pattern
        container_pattern= layer_pattern["containers"]
        
        # Validate that the layer pattern and the start index and num containers are valid
        if start_index + num_containers > len(container_pattern):
            print("Error: start index and num containers are invalid")
            return False
        print("Started palletizing ", num_containers, " containers")
        
        container_arrival_handler = json_telegrams.container_ID_point(
            self.cell_prefix, 
            self.cell_id, 
            self.client,)
        
        container_palletized_handler = json_telegrams.container_palletized(
            self.cell_prefix,
            self.cell_id, 
            self.client, 
            pallet_location_id, 
            layer_pattern_id,
            height_offset,)
        
        for i in range(start_index, start_index + num_containers):
            await asyncio.sleep(3)
            print("Container arrived at ID point : ", i)
            container_arrival_handler.position_id = i
            await container_arrival_handler.send_telegram()
            await asyncio.sleep(3)
            print("Container placed on pallet")
            container_palletized_handler.index = i
            #tmp_task = asyncio.create_task(self.update_variable(container_palletized_handler, i))   
            #await tmp_task
            await container_palletized_handler.send_telegram()
            
        return True

    
    async def state_updater(self):
        while True:
            if self.state != self.old_state or self.HCL_state_request == True:
                self.old_state = self.state
                #self.system_state.state = self.state
                temp_state = json_telegrams.system_state(self.cell_prefix, self.cell_id, self.client, self.state)
                print("Sending new state", temp_state.state)
                #await self.system_state.send_telegram()
                await temp_state.send_telegram()
                self.HCL_state_request = False
            await asyncio.sleep(0.5)
    
    # 5.1 Request telegram (HLC -> Cell) Telegram transmitted by the HLC.
    # The palletizing cell should send a corresponding telegram on the relevant topic.
    async def request_handler(self): # TODO change name to something more appropriate
        async with self.client.messages() as messages:
            async for message in messages:
                if message.topic.matches(self.state_request_topic): # TODO: change to HCL state request topic
                    print("got message " + message.payload.decode()) # TODO: Should act according to the message
                    # Convert the message to a python dictionary
                    msg = json.loads(message.payload)
                    if msg["request"] == "state":
                        self.HCL_state_request = True
                        print("Got state request")
                    elif msg["request"] == "active-alarms":
                        print("Got active_alarms request")
                        await self.system_alarm.send_telegram()
                    elif msg["request"] == "layer-patterns":
                        print("Got layer_patterns request")
                        prefix = self.cell_prefix + "/"
                        cell_id = self.cell_id + "/"
                        send_layer_pattern_class = json_telegrams.send_layer_pattern(prefix, cell_id, self.client)
                        await send_layer_pattern_class.send_telegram()
                        del send_layer_pattern_class
                elif message.topic.matches(self.transport_request_topic):
                    #print("got message " + message.payload.decode())
                    msg = json.loads(message.payload)
                    self.from_location_id = msg["from_location_id"]
                    self.to_location_id = msg["to_location_id"]
                    self.item_id = msg["item_id"]
                    print("Got transport for moving", self.item_id, "from", self.from_location_id, "to", self.to_location_id)
                    await json_telegrams.container_transport_reply(self.cell_prefix, self.cell_id, self.client, msg["request_id"])
                    
                    
                       
                       
    async def subcribe_handler(self):
        await self.client.subscribe(self.start_layer_topic)
        await self.client.subscribe(self.state_request_topic)
        await self.client.subscribe(self.state_change_request_topic)
        await self.client.subscribe(self.transport_request_topic)
        
    async def pattern_handler(self):
        pattern_handler = json_telegrams.add_update_layer_pattern( self.cell_prefix, self.cell_id, self.client,)
        await pattern_handler.receive_telegram()
    
    
    async def opc_ua_update_items(self):
        client = Client('opc.tcp://192.168.100.212:4840/server/')
        await client.connect()
        print("Client connected")
        # Start loop to read from OPCUA server
        
        task = await client.nodes.root.get_child(["0:Objects", f"2:palletizing_object", f"2:task"])
        pallet_status = await client.nodes.root.get_child(["0:Objects", f"2:palletizing_object", f"2:pallet_status"])
        pallet_place = await client.nodes.root.get_child(["0:Objects", f"2:palletizing_object", f"2:pallet_place"])
        pallet_error_code = await client.nodes.root.get_child(["0:Objects", f"2:palletizing_object", f"2:pallet_error_code"])
        ur_response = await client.nodes.root.get_child(["0:Objects", f"2:palletizing_object", f"2:ur_response"])
        
        
        await pallet_place.write_value(str(self.pallet_place_id))
        await task.write_value(str(self.task_id))
        
        # Clode the connection
        await client.disconnect()
        
            
            
    async def opc_ua_handler(self):

        _logger = logging.getLogger('asyncua')
        # setup our opcua client
        client = Client('opc.tcp://192.168.100.212:4840/server/')
        await client.connect()
        print("Client connected")
        # Start loop to read from OPCUA server
        
        task = await client.nodes.root.get_child(["0:Objects", f"2:palletizing_object", f"2:task"])
        pallet_status = await client.nodes.root.get_child(["0:Objects", f"2:palletizing_object", f"2:pallet_status"])
        pallet_place = await client.nodes.root.get_child(["0:Objects", f"2:palletizing_object", f"2:pallet_place"])
        pallet_error_code = await client.nodes.root.get_child(["0:Objects", f"2:palletizing_object", f"2:pallet_error_code"])
        ur_response = await client.nodes.root.get_child(["0:Objects", f"2:palletizing_object", f"2:ur_response"])
        
        #await server.nodes.objects.add_method(ua.NodeId('ServerMethod', 2), ua.QualifiedName('ServerMethod', 2), func, [ua.VariantType.Int64], [ua.VariantType.Int64])
        _logger.info('Starting server!')
        while True:
            await asyncio.sleep(1)
            # Read pallet_place_status
            if self.reset_opcua_vars == True:
                await ur_response.write_value("0")
                await pallet_status.write_value("0")
                self.reset_opcua_vars = False
            
            self.pallet_status_id = await pallet_status.read_value()
            # Read pallet_error_code
            self.pallet_error_code = await pallet_error_code.read_value()
            
            self.ur_response = await ur_response.read_value()
            # Now we update pallet_task and place if we got a new task
            """if self.pallet_place_id != await pallet_place.read_value():
                await pallet_place.write_value(str(self.pallet_place_id))
            if self.task_id != await task.read_value():
                await task.write_value(str(self.task_id))"""
                

    async def wait_for_user_input(self):
        while True:
            user_input = await aioconsole.ainput() # Allows for async input
            user_input = str(user_input)
            # Check if user input can be separated into two words
            if len(user_input.split()) > 1:
                user_input = user_input.split()
                if user_input[0] == "setalarm":
                    if len(user_input) != 3: # Handle if the user input is not valid
                        print("Invalid input, please use setalarm <alarm_id> <True/False>")
                    else:
                        alarm_id = int(user_input[1])
                        alarm_text = "Alarm : " + str(alarm_id)
                        if user_input[2] == "True" or user_input[2] == "true" or user_input[2] == "1" or user_input[2] == "on" or user_input[2] == "On" or user_input[2] == "ON":
                            active = True
                            print("Setting alarm", alarm_id, "to", active)
                            await json_telegrams.add_alarm_state(self.cell_prefix, self.cell_id, self.client, alarm_id, alarm_text, active, self.system_alarm) # Set alarm and send telegram
                        elif user_input[2] == "False" or user_input[2] == "false" or user_input[2] == "0" or user_input[2] == "off" or user_input[2] == "Off" or user_input[2] == "OFF":
                            active = False
                            print("Setting alarm", alarm_id, "to", active)
                            await json_telegrams.add_alarm_state(self.cell_prefix, self.cell_id, self.client, alarm_id, alarm_text, active, self.system_alarm) # Set alarm and send telegram
                        else:
                            print("Invalid input, please use True or False")        
                else:
                    print("Invalid command, type help for list of commands") 
            elif user_input == "sendalarms":
                await self.system_alarm.send_telegram()
                     
            elif user_input == "help":
                print("Commands: setalarm, sendalarms")
            else:
                print("Invalid command, type help for list of commands")
    
    async def main(self):
        loop = asyncio.get_event_loop()
        
        # Load the certificates:
        tls_params = aiomqtt.TLSParameters(
            ca_certs="cert\mqtt.crt",
            certfile=None,
            keyfile=None,
            cert_reqs=None,
            tls_version=None,
            ciphers=None,
        )
        hostname = "broker.intelligentsystems.mqtt"
        #hostname = "localhost"
        port = 8883 #16372
        client_id = "palletizing_cell"
        #tls_params=tls_params
        async with aiomqtt.Client(hostname, tls_params=tls_params, port=port, client_id=client_id) as self.client:
            # Define classes:
            self.system_alarm = json_telegrams.active_alarms(self.cell_prefix, self.cell_id, self.client)
            
            #self.opc_ua_server, self.opc_ua_idx, self.opc_ua_logger = await self.start_OPC_UA_server()
            
            # Define tasks:
            subscribe_handler_task = loop.create_task(self.subcribe_handler())
            start_layer_task = loop.create_task(self.start_layer())
            request_handler_task = loop.create_task(self.request_handler())
            #state_update_task = loop.create_task(self.state_update())
            state_updater_task = asyncio.ensure_future(self.state_updater())
            opc_ua_task = asyncio.create_task(self.opc_ua_handler())
            pattern_handler_task = asyncio.create_task(self.pattern_handler())
            cmd_handler = asyncio.create_task(self.wait_for_user_input())
            pick_place_handler = asyncio.create_task(self.pick_place())
            
            await pick_place_handler
            await cmd_handler
            await pattern_handler_task
            await opc_ua_task
            await request_handler_task
            await start_layer_task
            await subscribe_handler_task
            await state_updater_task
        
    
    