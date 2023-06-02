        

import logging
import asyncio
import sys
sys.path.insert(0, "..")

from asyncua import ua, Server, Client
from asyncua.common.methods import uamethod

async def main():        
    _logger = logging.getLogger('asyncua')
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://192.168.100.212:4840/server/')
    #server.set_endpoint('opc.tcp://localhost:4840/server/') 
    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua1.github.io'
    idx = await server.register_namespace(uri)
    
    myobj = await server.nodes.objects.add_object(idx, 'palletizing_object')
    pallet_place = await myobj.add_variable(idx, 'pallet_place', str(0)) # initialized as 0, can be 1 to 3 
    task = await myobj.add_variable(idx, 'task', str(0)) # initialized as 0, can be 1 to 4
    pallet_status = await myobj.add_variable(idx, 'pallet_status', str(0)) # initialized as 0, can be 1 to 4
    pallet_error_code = await myobj.add_variable(idx, 'pallet_error_code', str(0)) # initialized as 0, can be 1 to 4
    ur_response = await myobj.add_variable(idx, 'ur_response', str(0)) # initialized as 0, can be 1 to 4
    
    await pallet_place.set_writable()
    await task.set_writable()
    await pallet_status.set_writable()
    await pallet_error_code.set_writable()
    await ur_response.set_writable()
    #await server.nodes.objects.add_method(ua.NodeId('ServerMethod', 2), ua.QualifiedName('ServerMethod', 2), func, [ua.VariantType.Int64], [ua.VariantType.Int64])
    _logger.info('Starting server!')
    async with server:
        while True:
            await asyncio.sleep(1)
            
            
if __name__ == '__main__':
    asyncio.run(main())