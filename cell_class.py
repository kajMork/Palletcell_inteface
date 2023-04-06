import json
import paho.mqtt.client as mqtt_client
import asyncio_mqtt as aiomqtt

import asyncio
import time

import json_telegrams
# class that represents the pallet cell

class Cell:
    def __init__(self, name):
        self.name = name
        self.status = "Idle"
        self.client = None
        #self.loop = asyncio.get_event_loop()
        self.HCL_start_layer_topic = "HCL/1/palletize/start_layer"
       
    # 5.5.1 Start Palletizing Single Layer (HLC -> PLC)
    async def start_layer(self):
        async with self.client.messages() as messages:
            async for message in messages:
                if message.topic.matches(self.HCL_start_layer_topic):
                    obj = json.loads(message.payload) # get the json string and convert it to a python dictionary
                    print("Starting layer with layer-pattern id : " + str(obj["layer-pattern-id"]))
                    print("Starting layer with height-offset : " + str(obj["height-offset"]))
                    print("Sent at : " + str(obj["timestamp"]))
                    await self.client.publish("HCL_feedback", "Starting layer")
                    self.status = "Working"
                    await asyncio.sleep(15)
                    await self.client.publish("HCL_feedback", "Layer done")
                    self.status = "Idle"
                    print("Layer done")
    
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
            
            await listen_task
            await start_layer_task
            await subscribe_handler_task
        
    
    