import json
import paho.mqtt.client as mqtt_client
import asyncio_mqtt as aiomqtt

import asyncio
import time
# class that represents the pallet cell

class Cell:
    def __init__(self, name):
        self.name = name
        self.status = "Idle"
        self.client = None
        #self.loop = asyncio.get_event_loop()
        
    async def start_layer(self):
        async with self.client.messages() as messages:
            async for message in messages:
                if message.topic.matches("palletcell"):
                    obj = json.loads(message.payload) # get the json string and convert it to a python dictionary
                    print("Starting layer with layer-pattern id : " + str(obj["layer-pattern-id"]))
                    #print("got message " + message.payload.decode())
                    await self.client.publish("HCL_feedback", "Starting layer")
                    self.status = "Working"
                    await asyncio.sleep(15)
                    await self.client.publish("HCL_feedback", "Layer done")
                    self.status = "Idle"
                    print("Layer done")
    
    async def subcribe_handler(self):
        await self.client.subscribe("palletcell")
        
    async def main(self):
        loop = asyncio.get_event_loop()
        async with aiomqtt.Client("localhost") as self.client:
            subscribe_handler_task = loop.create_task(self.subcribe_handler())
            start_layer_task = loop.create_task(self.start_layer())
            
            await start_layer_task
        
    
    