# Import mqtt client

#https://github.com/vernemq/vernemq
#https://docs.vernemq.com/configuring-vernemq/the-vernemq-conf-file

# For running the mqtt broker
# $ cd $VERNEMQ/_build/default/rel/vernemq
#$ bin/vernemq start
import paho.mqtt.client as mqtt_client
import asyncio_mqtt as aiomqtt
import cell_class
import asyncio
import time

status = "Idle"

async def do_work(client):
    print("Doing work")
    
    t1 = time.time()
    await client.publish("HCL_feedback", "Began work at")
    status = "Working"
    await asyncio.sleep(15)
    t2 = time.time()
    await client.publish("HCL_feedback", "Work done at " + str(t2- t1))
    print("Work done")
    status = "Idle"

async def listen(client):
    temp_task = None
    async with client.messages() as messages:
        async for message in messages:
            feedback = message.payload.decode()
            print(feedback)
            if feedback == "start":
                print("Starting work")
                temp_task = asyncio.create_task(do_work(client)) # This allows for multiple tasks to be created
                print("Ending work, feedback sent")
            elif feedback == "status":
                print("Sending status")
                await client.publish("Cell_status", "test")
                print("Status sent")
            if temp_task != None:
                if temp_task.done():
                    print("Work done")
                    await client.publish("HCL_feedback", "Work done")
                    status = "Idle"
                    temp_task = None
                else:
                    print("Work not done")
                    await client.publish("HCL_feedback", "Work not done")
                    status = "Working"
            else:
                print("No task")
                await client.publish("HCL_feedback", "No task started")
                status = "Idle"
            
                
            


async def setup(client):
    print('Connected to mqtt broker')

    # Subscribe to topics
    await client.subscribe("palletcell2")
    await client.subscribe("palletcell")



async def main():
    # Wait for messages in (unawaited) asyncio task
    loop = asyncio.get_event_loop()
    async with aiomqtt.Client("localhost") as client:
        task0 = loop.create_task(setup(client))
        task = loop.create_task(listen(client))
        # This will still run!
        print("Magic!")
        
        
        # If you don't await the task here the program will simply finish.
        # However, if you're using an async web framework you usually don't have to await
        # the task, as the framework runs in an endless loop.
        await task
        await task0

new_cell = cell_class.Cell("palletcell2")
asyncio.run(new_cell.main())