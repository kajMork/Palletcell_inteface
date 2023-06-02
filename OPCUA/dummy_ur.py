
import logging
import asyncio
import sys
sys.path.insert(0, "..")

from asyncua import ua, Server, Client
from asyncua.common.methods import uamethod


task = "ns=2;i=3" # 1 = technicon cell to right spot, 2 = container tray to left spot, 3 = left spot to technicon cell, 4 = right spot to pallet
pallet_status = "ns=2;i=4" # 0 = idle, 1 = done
pallet_place = "ns=2;i=2" # 1 to 3
pallet_error_code = "ns=2;i=5" # 0 = no error, 1 = error



async def technicon_cell_to_right_spot(pallet_status, task):
    await asyncio.sleep(3)
    print("technicon cell to right spot done")
    await pallet_status.write_value("1")
    # reset task to 0
    await task.write_value("0")

async def container_tray_to_left_spot(pallet_status, task):
    await asyncio.sleep(3)
    print("container tray to left spot done")
    await pallet_status.write_value("1")
    await task.write_value("0")

async def left_spot_to_technicon_cell(pallet_status, task):
    print("left spot to technicon cell done")
    await pallet_status.write_value("1")
    await task.write_value("0")
    
async def right_spot_to_pallet(pallet_status, task, container_place_location):
    await asyncio.sleep(3)
    if container_place_location == "1":
        print("right spot to pallet place 1 done")
        await pallet_status.write_value("1")
    elif container_place_location == "2":
        print("right spot to pallet place 2 done")
        await pallet_status.write_value("1")
    elif container_place_location == "3":
        print("right spot to pallet place 3 done")
        await pallet_status.write_value("1")
    await task.write_value("0")


async def main():
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
    
    while True:
        if await task.read_value() == "1":
            await ur_response.write_value("1")
            await container_tray_to_left_spot(pallet_status, task)
        elif await task.read_value() == "2":
            await ur_response.write_value("1")
            await technicon_cell_to_right_spot(pallet_status, task )
        elif await task.read_value() == "3":
            await ur_response.write_value("1")
            await left_spot_to_technicon_cell(pallet_status, task)
        elif await task.read_value() == "4":
            await ur_response.write_value("1")
            container_place_location = await pallet_place.read_value()
            await right_spot_to_pallet(pallet_status, task, container_place_location)
        await asyncio.sleep(1)
    
if __name__ == '__main__':
    asyncio.run(main())