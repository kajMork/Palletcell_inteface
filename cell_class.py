import json
#import aiomqtt as aiomqtt
import asyncio_mqtt as aiomqtt
from asyncua import ua, Server
from asyncua.common.methods import uamethod
import asyncio
import logging
# JSON telegram template classes
import cell_json_telegrams as json_telegrams
import sys
sys.path.insert(0, "..")
# TODO:
# 1. Implement suspend and aborted states and how to handle these requests from HCL.
# 

# class that represents the pallet cell

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
        
        
        # System alarms
        self.system_alarm = None # Will be defined in main
        
        
        # System state variables
        self.old_state = "Offline"
        self.state = "Idle"
        self.system_state = json_telegrams.system_state(self.cell_prefix, self.cell_id, self.client, self.state)
        self.HCL_state_request = False
       
    # 5.5.1 Start Palletizing Single Layer (HLC -> PLC)
    async def start_layer(self):
        async with self.client.messages() as messages:
            async for message in messages:
                if message.topic.matches(self.start_layer_topic):
                    obj = json.loads(message.payload) # get the json string and convert it to a python dictionary
                    print("Starting layer with layer-pattern id : " + str(obj["layer-pattern-id"]))
                    print("Starting layer with height-offset : " + str(obj["height-offset"]))
                    print("Sent at : " + str(obj["timestamp"]))
                    self.state = "Starting"
                    await asyncio.sleep(5)
                    print("Layer started. state = " + self.state)
                    self.state = "Execute"
                    print ("Layer executing. state = " + self.state)
                    ret = await self.palletize_layer_dummy(obj)
                    if ret == False:
                        print("Error palletizing layer")
                        self.state = "Error"
                        print("Layer error. state = " + self.state)
                    else:
                        self.state = "Complete"
                        print("Layer done. state = " + self.state)

    async def palletize_layer_dummy(self, obj):
        layer_pattern_id = obj["layer-pattern-id"]
        # load layer pattern from database
        layer_pattern_filename = "layer_patterns/" + str(layer_pattern_id) + ".json"
        try :
            with open(layer_pattern_filename) as json_file:
                layer_pattern = json.load(json_file)
        except:
            print("Error loading layer pattern")
            return False
        # Extraxt info from the received json object
        start_index = obj["start-index"]
        num_containers = obj["num-containers"]
        height_offset = obj["height-offset"]
        pallet_location_id = obj["pallet-location-id"]
        
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


    #async def update_variable(self, my_obj, value):
    #    my_obj.index = value   
        
    
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
                        print("Got active-alarms request")
                        await self.system_alarm.send_telegram()
                    elif msg["request"] == "layer-patterns":
                        print("Got layer-patterns request")
                        prefix = self.cell_prefix + "/"
                        cell_id = self.cell_id + "/"
                        send_layer_pattern_class = json_telegrams.send_layer_pattern(prefix, cell_id, self.client)
                        await send_layer_pattern_class.send_telegram()
                        del send_layer_pattern_class
                        
    
    async def subcribe_handler(self):
        await self.client.subscribe(self.start_layer_topic)
        await self.client.subscribe(self.state_request_topic)
        
    async def pattern_handler(self):
        pattern_handler = json_telegrams.add_update_layer_pattern( self.cell_prefix, self.cell_id, self.client,)
        await pattern_handler.receive_telegram()
        
    async def opc_ua_handler(self):

        @uamethod
        def func(parent, value):
            return value * 2
        _logger = logging.getLogger('asyncua')
        # setup our server
        server = Server()
        await server.init()
        #server.set_endpoint('opc.tcp://192.168.12.246:4840/server/')
        server.set_endpoint('opc.tcp://localhost:4840/server/') 
        # setup our own namespace, not really necessary but should as spec
        uri = 'http://examples.freeopcua1.github.io'
        idx = await server.register_namespace(uri)

        # populating our address space
        # server.nodes, contains links to very common nodes like objects and root
        myobj = await server.nodes.objects.add_object(idx, 'MyObject')
        myvar = await myobj.add_variable(idx, 'MyVariable', str(1))
        
        await myvar.set_writable()
        
        await server.nodes.objects.add_method(ua.NodeId('ServerMethod', 2), ua.QualifiedName('ServerMethod', 2), func, [ua.VariantType.Int64], [ua.VariantType.Int64])
        _logger.info('Starting server!')
        async with server:
            while True:
                await asyncio.sleep(1)
                if self.state == "Execute":
                    _logger.info('Set value of %s to %.s', myvar, self.state)
                    await myvar.write_value(self.state)
                elif self.state == "Complete":
                    _logger.info('Set value of %s to %.s', myvar, self.state)
                    await myvar.write_value(self.state)
                
    
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
        port = 8883
        client_id = "palletizing_cell"
        
        async with aiomqtt.Client(hostname, tls_params=tls_params, port=port, client_id=client_id) as self.client:
            # Define classes:
            self.system_alarm = json_telegrams.active_alarms(self.cell_prefix, self.cell_id, self.client)
            
            # Define tasks:
            subscribe_handler_task = loop.create_task(self.subcribe_handler())
            start_layer_task = loop.create_task(self.start_layer())
            request_handler_task = loop.create_task(self.request_handler())
            #state_update_task = loop.create_task(self.state_update())
            state_updater_task = asyncio.ensure_future(self.state_updater())
            opc_ua_task = asyncio.create_task(self.opc_ua_handler())
            pattern_handler_task = asyncio.create_task(self.pattern_handler())
            
            await pattern_handler_task
            await opc_ua_task
            await request_handler_task
            await start_layer_task
            await subscribe_handler_task
            await state_updater_task
        
    
    