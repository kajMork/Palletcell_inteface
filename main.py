import logging
import asyncio
import sys
sys.path.insert(0, "..")

from asyncua import ua, Server
from asyncua.common.methods import uamethod
from pymodbus.client import ModbusTcpClient


UR_Status_ID = 1001
UR_status_register_val = 0

Reg2_ID = 1003
Reg2_val = 0


Reg3_ID = 1005
Reg3_val = 0

Reg4_ID = 1007
Reg4_val = 0

Reg5_ID = 1009
Reg5_val = 0

@uamethod
def func(parent, value):
    return value * 2


async def main():
    #MODBUS set what server to connect to
    client = ModbusTcpClient('192.168.12.20')

    _logger = logging.getLogger('asyncua')
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint('opc.tcp://192.168.12.254:4840/server/')

    # setup our own namespace, not really necessary but should as spec
    uri = 'http://examples.freeopcua1.github.io'
    idx = await server.register_namespace(uri)

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    myobj = await server.nodes.objects.add_object(idx, 'MyObject')
    myvar = await myobj.add_variable(idx, 'MyVariable', 6.7)


    UR_status_register_val = client.read_holding_registers(UR_Status_ID, 1)
    UR_status = await myobj.add_variable(idx, 'UR_status', float(UR_status_register_val.registers[0]))

    Reg2_val = client.read_holding_registers(Reg2_ID, 1)
    Reg2 = await myobj.add_variable(idx, 'Reg2', float(Reg2_val.registers[0]))

    Reg3_val = client.read_holding_registers(Reg3_ID, 1)
    Reg3 = await myobj.add_variable(idx, 'Reg3', float(Reg3_val.registers[0]))

    Reg4_val = client.read_holding_registers(Reg4_ID, 1)
    Reg4 = await myobj.add_variable(idx, 'Reg4', float(Reg4_val.registers[0]))

    Reg5_val = client.read_holding_registers(Reg5_ID, 1)
    Reg5 = await myobj.add_variable(idx, 'Reg5', float(Reg5_val.registers[0]))

    # Set MyVariable to be writable by clients
    await myvar.set_writable()
    await UR_status.set_writable()
    await Reg2.set_writable()
    await Reg3.set_writable()
    await Reg4.set_writable()


    await server.nodes.objects.add_method(ua.NodeId('ServerMethod', 2), ua.QualifiedName('ServerMethod', 2), func, [ua.VariantType.Int64], [ua.VariantType.Int64])
    _logger.info('Starting server!')
    async with server:
        while True:
            await asyncio.sleep(1)
            UR_status_register_val = await UR_status.get_value()
            client.write_register(UR_Status_ID, int(UR_status_register_val))
            #UR_status_register_val = client.read_holding_registers(UR_Status_ID, 1)
            #await UR_status.write_value(float(UR_status_register_val.registers[0]))

            Reg2_val = client.read_holding_registers(Reg2_ID, 1)
            await Reg2.write_value(float(Reg2_val.registers[0]))

            Reg3_val = client.read_holding_registers(Reg3_ID, 1)
            await Reg3.write_value(float(Reg3_val.registers[0]))

            Reg4_val = client.read_holding_registers(Reg4_ID, 1)
            await Reg4.write_value(float(Reg4_val.registers[0]))

            Reg5_val = client.read_holding_registers(Reg5_ID, 1)
            await Reg5.write_value(float(Reg5_val.registers[0]))

            new_val = await myvar.get_value() + 0.1
            _logger.info('Set value of %s to %.1f', myvar, new_val)
            await myvar.write_value(new_val)
        client.close()


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    asyncio.run(main(), debug=True)
    """client = ModbusTcpClient('192.168.12.20')
    result = client.read_holding_registers(1007, 1)
    print(result.registers[0])
    client.write_register(1007, 333)
    client.close()"""
