# Import mqtt client

#https://github.com/vernemq/vernemq
#https://docs.vernemq.com/configuring-vernemq/the-vernemq-conf-file

# For running the mqtt broker
# $ cd $VERNEMQ/_build/default/rel/vernemq
#$ bin/vernemq start
import paho.mqtt.client as mqtt_client
import asyncio_mqtt as aiomqtt
#import aiomqtt as aiomqtt
import cell_class
import asyncio
import time
import sys
import os

#async def main():
print("Starting main")

#asyncio.get_event_loop().run_until_complete(new_cell.main())
if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    # only import if platform/os is win32/nt, otherwise "WindowsSelectorEventLoopPolicy" is not present
    from asyncio import (
        set_event_loop_policy,
        WindowsSelectorEventLoopPolicy
    )
    # set the event loop
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

new_cell = cell_class.Cell("palletcells","1")

asyncio.run(new_cell.main())