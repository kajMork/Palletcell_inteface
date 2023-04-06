import json
import paho.mqtt.client as mqtt_client
import asyncio_mqtt as aiomqtt

import asyncio
import time

import json_telegrams
# class that represents the pallet cell

class Cell:
    def __init__(self, id):
        # Cell specific variables
        self.cell_id = id
        self.cell_prefix = "palletcells"
        self.client = None
        
        # MQTT topics
        self.HCl_prefix = "HCL"
        self.HCL_id = "1"
        self.HCL_start_layer_topic = self.HCl_prefix + "/" + self.HCL_id + "/palletize/start-layer"
        self.HCL_state_request_topic = self.HCl_prefix + "/" + self.HCL_id + "/state/request"
        self.HCL_state_feedback_topic = self.cell_prefix + "/" + self.cell_id + "/system/state"
        
        
        # System state variables
        self.old_state = "Offline"
        self.state = "Idle"
        self.system_state = json_telegrams.system_state(self.cell_prefix, self.cell_id, self.client, self.state)
        self.HCL_state_request = False
       
    # 5.5.1 Start Palletizing Single Layer (HLC -> PLC)
    async def start_layer(self):
        async with self.client.messages() as messages:
            async for message in messages:
                if message.topic.matches(self.HCL_start_layer_topic):
                    obj = json.loads(message.payload) # get the json string and convert it to a python dictionary
                    print("Starting layer with layer-pattern id : " + str(obj["layer-pattern-id"]))
                    print("Starting layer with height-offset : " + str(obj["height-offset"]))
                    print("Sent at : " + str(obj["timestamp"]))
                    self.state = "Starting"
                    await asyncio.sleep(5)
                    print("Layer started. state = " + self.state)
                    self.state = "Execute"
                    await asyncio.sleep(15)
                    self.state = "Complete"
                    print("Layer done. state = " + self.state)

    async def state_update(self):
        while True:
            if self.state != self.old_state or self.HCL_state_request == True:
                print("old state: " + self.old_state)
                self.old_state = self.state
                print("new state: " + self.old_state)
                #self.system_state.state = self.state
                temp_state = json_telegrams.system_state(self.cell_prefix, self.cell_id, self.client, self.state)
                print("Sending status", self.system_state.state)
                #await self.system_state.send_telegram()
                await temp_state.send_telegram()
                self.HCL_state_request = False
            await asyncio.sleep(0.5)

    
    async def test_listen(self):
        async with self.client.messages() as messages:
            async for message in messages:
                if message.topic.matches("palletcell2"):
                    print("got message " + message.payload.decode())
    
    async def subcribe_handler(self):
        await self.client.subscribe(self.HCL_start_layer_topic)
        await self.client.subscribe("palletcell2")
        
    async def main(self):
        loop = asyncio.get_event_loop()
        async with aiomqtt.Client("localhost") as self.client:
            subscribe_handler_task = loop.create_task(self.subcribe_handler())
            start_layer_task = loop.create_task(self.start_layer())
            listen_task = loop.create_task(self.test_listen())
            #state_update_task = loop.create_task(self.state_update())
            state_update_task = asyncio.ensure_future(self.state_update())
            await listen_task
            await start_layer_task
            await subscribe_handler_task
            #await state_update_task
        
    
    