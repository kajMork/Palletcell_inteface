import utils
import json

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


# 5.4.1 Container at ID Point (Cell -> HCL)
#Telegram transmitted by the cell when a container ID is scanned used e.g. a barcode
#scanner or RFID reader.
class container_ID_point:
    def __init__(self, prefix, cell_id, client, position_id, scan):
        # Topic specific variables
        self.prefix = prefix+"/"
        self.cell_id = cell_id+"/"
        self.topic_name = self.prefix + self.cell_id + "container/id-point"
        
        # MQTT specific variables
        self.client = client
        
        # Telegram specific variables
        self.version = "v1.0"
        self.position_id = position_id
        self.scan = scan

        self.container_ID_point_telegram = {
            "version": self.version,
            "position-id": self.position_id,
            "scan": self.scan,
            "timestamp": utils.get_datetime()
        }
        
    async def send_telegram(self):
        telegram = self.container_ID_point_telegram.copy()
        telegram["timestamp"] = utils.get_datetime() # Update timestamp
        await self.client.publish(self.topic_name, json.dumps(telegram)) # Send telegram
        del telegram # Delete the telegram to save memory

# 5.4.2 Container PLaced on Pallet (Cell -> HCL)
#Telegram transmitted by the cell when each container is placed on a pallet.

class container_palletized:
    def __init__(self, prefix, cell_id, client, pallet_location_id, layer_pattern_id, index, height_offset):
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
        self.index = index
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
        await self.client.publish(self.topic_name, json.dumps(telegram)) # Send telegram
        del telegram # Delete the telegram to save memory

# 5.5.1 Start Palletizing Single Layer (HLC -> Cell)
#Request from the HLC to start palletizing. The request is sent on a per-layer basis, where
#the palletizer will continue to palletize containers until num-containers have been processed.
class palletize_start_layer:
    def __init__(self, prefix, cell_id, client, layer_pattern_id, height_offset, start_index, num_containers, input_buffer_id, pallet_location_id):
        # Topic specific variables
        self.prefix = prefix+"/"
        self.cell_id = cell_id+"/"
        self.topic_name = self.prefix + self.cell_id + "palletize/start-layer"
        
        # MQTT specific variables
        self.client = client
        
        # Telegram specific variables
        self.version = "v1.0"
        self.layer_pattern_id = layer_pattern_id
        self.height_offset = height_offset
        self.start_index = start_index
        self.num_containers = num_containers
        self.input_buffer_id = input_buffer_id
        self.pallet_location_id = pallet_location_id
        
        # Create the telegram
        self.palletize_start_layer_telegram = {
            "version": self.version,
            "layer-pattern-id": self.layer_pattern_id,
            "height-offset": self.height_offset,
            "start-index": self.start_index,
            "num-containers": self.num_containers,
            "input-buffer-id": self.input_buffer_id,
            "pallet-location-id": self.pallet_location_id,
            "timestamp": utils.get_datetime()
        }
    async def send_telegram(self):
        telegram = self.palletize_start_layer_telegram.copy()
        telegram["timestamp"] = utils.get_datetime() # Update timestamp
        await self.client.publish(self.topic_name, json.dumps(telegram)) # Send telegram
        del telegram # Delete the telegram to save memory



if __name__ == "__main__":
    # For testing purposes
    pass # Do nothing