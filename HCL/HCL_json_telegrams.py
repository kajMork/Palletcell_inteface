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

class HCL_send_layer_pattern:
    def __init__(self, prefix, cell_id, client):
        self.client = client
        self.prefix = prefix+"/"
        self.cell_id = cell_id+"/"
        self.topic_name = self.prefix + self.cell_id + "layer-pattern/update"
    
        self.pattern_layer = {
            "version": "v1.0",
            "id": 1,
            "layer-name": "2 boxes",
            "pallet-type": "half-EURO",
            "use-slip-sheet": "false",
            "containers": [
            {
                "index": 0,
                "position": {
                "x": 0,
                "y": 0,
                "rotation": 0
                },
                "container-dimensions": {
                "length": 360,
                "width": 280,
                "height": 100
                }
            },
            {
                "index": 1,
                "position": {
                "x": 0,
                "y": 725,
                "rotation": 270
                },
                "container-dimensions": {
                "length": 360,
                "width": 280,
                "height": 100
                }
            }
            ]
        }
    async def send_telegram(self):
        telegram = self.pattern_layer.copy()
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