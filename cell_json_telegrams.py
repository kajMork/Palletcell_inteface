import utils
import json
import glob
# TODO: add a class for each telegram type
alarm_telegram = {
    "version": "v1.0",
    "timestamp": utils.get_datetime(),
    "alarm-id": None,
    "alarm-text": None,
    "active": None
}

#5.2.1 System State (Cell -> HLC)
#Sent by the palletizing cell when state has changed or when requested by the HLC.
#The states follow the PackML state model [1] in addition to an “Offline” state (typically part of the Last Will and Testament).
#When a system connects to the broker, it should send an initial status message.
#Status messages should be sent with retention enabled.
class system_state:
    def __init__(self, prefix, cell_id, client, state):
        # Topic specific variables
        self.prefix = prefix+"/"
        self.cell_id = cell_id+"/"
        self.topic_name = self.prefix + self.cell_id + "system/state"
        
        # MQTT specific variables
        self.client = client
        
        # Telegram specific variables
        self.version = "v1.0"
        self.state = state
        
        # Create the telegram
        self.system_state_telegram = {
            "version": self.version,
            "state": self.state,
            "timestamp": utils.get_datetime()
        }
        
    async def send_telegram(self):
        telegram = self.system_state_telegram.copy()
        # Update timestamp
        if self.state != "Offline":
            telegram["timestamp"] = utils.get_datetime()
        else:
            telegram["timestamp"] = None
        await self.client.publish(self.topic_name, json.dumps(telegram)) # Send telegram
        del telegram # Delete the telegram to save memory

#5.3.1 Get Layer Pattern (Cell -> HLC)
#Sent by the palletizing cell when a layer pattern has changed or when requested by the HLC.
class send_layer_pattern:
    def __init__(self, prefix, cell_id, client):
        # Topic specific variables
        self.prefix = prefix+"/"
        self.cell_id = cell_id+"/"
        self.topic_name = self.prefix + self.cell_id + "layer-pattern"
        
        # MQTT specific variables
        self.client = client
        
        self.obj = None
        self.container_pattern = None
        
    async def get_telegram(self):
        await self.client.subscribe(self.topic_name)
        async with self.client.messages() as messages:
            async for message in messages:
                if message.topic.matches(self.topic_name):
                    obj = json.loads(message.payload)
                    container_pattern = obj["containers"]


#5.3.2 Add/Update Layer Pattern (HLC -> Cell)
#Telegram transmitted by the HLC. Sent when a new layer pattern should be stored on the
#palletizing cell. If the ID of the pattern is already stored on the palletizing cell, it is replaced
#with the data from the telegram.
class add_update_layer_pattern:
    def __init__(self, prefix, cell_id, client):
        self.client = client
        self.prefix = prefix+"/"
        self.cell_id = cell_id+"/"
        self.topic_name = self.prefix + self.cell_id + "layer-pattern/update"
        
    async def receive_telegram(self):
        await self.client.subscribe(self.topic_name)
        async with self.client.messages() as messages:
            async for message in messages:
                if message.topic.matches(self.topic_name):
                    obj = json.loads(message.payload)
                    id = str(obj["id"])
                    pattern_file_name = "layer_patterns/"+id+".json"
                    # Add or update the layer pattern file in the layer_patterns folder
                    with open(pattern_file_name, "w+") as file:
                        json.dump(obj, file)
                    print("Layer pattern file updated: "+pattern_file_name)


# 5.4.1 Container at ID Point (Cell -> HCL)
#Telegram transmitted by the cell when a container ID is scanned used e.g. a barcode
#scanner or RFID reader.
class container_ID_point:
    def __init__(self, prefix, cell_id, client):
        # Topic specific variables
        self.prefix = prefix+"/"
        self.cell_id = cell_id+"/"
        self.topic_name = self.prefix + self.cell_id + "container/id-point"
        
        # MQTT specific variables
        self.client = client
        
        # Telegram specific variables
        self.version = "v1.0"
        self.position_id = None
        self.scan = None

        self.container_ID_point_telegram = {
            "version": self.version,
            "position-id": self.position_id,
            "scan": self.scan,
            "timestamp": utils.get_datetime()
        }

    async def send_telegram(self):
        telegram = self.container_ID_point_telegram.copy()
        telegram["timestamp"] = utils.get_datetime() # Update timestamp
        telegram["position-id"] = self.position_id
        telegram["scan"] = self.scan
        await self.client.publish(self.topic_name, json.dumps(telegram)) # Send telegram
        del telegram # Delete the telegram to save memory

# 5.4.2 Container PLaced on Pallet (Cell -> HCL)
#Telegram transmitted by the cell when each container is placed on a pallet.

class container_palletized:
    def __init__(self, prefix, cell_id, client, pallet_location_id, layer_pattern_id, height_offset):
        # Topic specific variables
        self.prefix = prefix+"/"
        self.cell_id = cell_id+"/"
        self.topic_name = self.prefix + self.cell_id + "container/palletized"
        
        # MQTT specific variables
        self.client = client
        
        # Telegram specific variables
        self.version = "v1.0"
        self.pallet_location_id = pallet_location_id
        self.layer_pattern_id = layer_pattern_id
        self.index = None
        self.height_offset = height_offset
        
        # Create the telegram
        self.container_palletized_telegram = {
            "version": self.version,
            "pallet-location-id": self.pallet_location_id,
            "layer-pattern-id": self.layer_pattern_id,
            "index": self.index,
            "height-offset": self.height_offset,
            "timestamp": utils.get_datetime()
        }
        
    async def send_telegram(self):
        telegram = self.container_palletized_telegram.copy()
        telegram["timestamp"] = utils.get_datetime() # Update timestamp
        telegram["index"] = self.index
        await self.client.publish(self.topic_name, json.dumps(telegram)) # Send telegram
        del telegram # Delete the telegram to save memory
        
    async def set_index(self, index):
        self.index = index


if __name__ == "__main__":
    # For testing purposes
    pass # Do nothing