# Import mqtt client
import paho.mqtt.client as mqtt_client
import asyncio_mqtt as aiomqtt
import aioconsole
import asyncio
import json
import json_telegrams

async def wait_for_user_input(client, firsrun):
    while True:
        start_layer_command = {
        "version": "v1.0",
        "layer-pattern-id": 1,
        "height-offset": 0,
        "start-index": 0,
        "num-containers": 7,
        "input-buffer-id": 15,
        "pallet-location-id": 15,
        "timestaamp": 0
        }
        user_input = await aioconsole.ainput() # Allows for async input
        user_input = str(user_input)
        
        #user_input = str(input("Enter command:"))
        #    print("You entered: " + user_input)
        #    firsrun = False
        if user_input == "execute":
            # Convert python dictionary to json string and send to mqtt broker
            start_layer_obj = json_telegrams.palletize_start_layer("HCL", "1", client, 1, 0, 0, 7, 15, 15)
            await start_layer_obj.send_telegram()
        elif user_input == "suspend":
            print("Sending status")
            await client.publish("palletcell", "stop")
        elif user_input == "get status":
            print("Sending status")
            await client.publish("palletcell2", "status")
        elif user_input == "help":
            print("Commands: execute, suspend, get status")
        else:
            print("Invalid command, type help for list of commands")

async def listen(client):
    async with client.messages() as messages:
        async for message in messages:
            feedback = message.payload.decode()
            print(feedback)
            if feedback == "Began work":
                print("Starting work")
                await client.publish("palletcell", "Status")
            if feedback == "Work done":
                print("Ending work, feedback received")
            if message.topic.matches("Cell_status"):
                print("Received status request:" + feedback)
                
            


async def setup(client):
    print('Connected to mqtt broker')

    # Subscribe to topics
    await client.subscribe("HCL_feedback")
    await client.subscribe("palletcells/1/system/state")
    await client.publish("palletcell", "Start")


async def main():
    # Wait for messages in (unawaited) asyncio task
    loop = asyncio.get_event_loop()
    async with aiomqtt.Client("localhost") as client:
        firstrun = True
        task0 = loop.create_task(setup(client))
        task = loop.create_task(listen(client))
        task1 = loop.create_task(wait_for_user_input(client, firstrun))
        # This will still run!
        print("Magic!")
        
        
        # If you don't await the task here the program will simply finish.
        # However, if you're using an async web framework you usually don't have to await
        # the task, as the framework runs in an endless loop.
        await task
        await task0
        await task1

asyncio.run(main())