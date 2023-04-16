import utils
import json
import glob
import asyncio
# 4.3 Error Message
async def send_error_message(topic, client, error_id):
    """Send error message to HLC, based on error_id.

    Args:
        topic (string): 
        client (_type_): 
        error_id (string): Supports: ERR_UNSUPPORTED, ERR_INVALID_MESSAGE, ERR_INVALID_STATE
    """
    description = None
    
    if error_id == "ERR_UNSUPPORTED":
        description = "Received request cannot be processed as it is not supported by the palletizing cell (e.g.responding with System Capabilities)"
    elif error_id == "ERR_INVALID_MESSAGE":
        description = "Request could not be parsed"
    elif error_id == "ERR_INVALID_STATE":
        description = "Palletizing cell is not in a state to execute the request (e.g. stopping an on-goingpalletizing if the cell is in an idle state)"
        
    error_message = {
        "version": "v1.0",
        "error": error_id,
        "reason": description
    }
    await client.publish(topic, json.dumps(error_message)) # Send telegram

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

# 5.2.3 Alarm States (Cell -> HLC) Telegram transmitted by the palletizing cell when the alarm status alters.
#The alarms are configured on the palletizing cell and HLC and are not part of this specification.

async def add_alarm_state(prefix, cell_id, client, alarm_id, alarm_text, active, alarm_system):
    """Adds alarm to alarm system and sends telegram to HLC. Alarms types are not yet defined.

    Args:
        prefix (String): Prefic for the topic
        cell_id (String): ID of the cell
        client (Class): client class
        alarm_id (Int): ID of the alarm
        alarm_text (String): Text associated with the alarm.
        active (Boolean): Indicates if the alarm is active (true) or inactive (false).
        alarm_system (Class): Class for where the alarm should be stored.
    """
    
    # Topic specific variables
    topic_name = prefix + "/" + cell_id + "/system/alarms"
    
    # Telegram specific variables
    version = "v1.0"
    # Create the telegram
    alarm_state_telegram = {
        "version": version,
        "timestamp": utils.get_datetime(),
        "alarm_id": alarm_id,
        "alarm_text": alarm_text,
        "active": active
    }
    # Add alarm to alarm system
    await alarm_system.add_alarm(alarm_id, alarm_text, active)
    
    # Send telegram
    await client.publish(topic_name, json.dumps(alarm_state_telegram))

# 5.2.4 Active Alarms (Cell -> HLC)
# Telegram transmitted by the palletizing cell when a corresponding request telegram is sent.
# The telegram contains an array of all active alarms.
# The alarms are configured on the palletizing cell and HLC and are not part of this specification.

class active_alarms:
    def __init__(self, prefix, cell_id, client):
        # Topic specific variables
        self.prefix = prefix + "/"
        self.cell_id = cell_id + "/"
        self.topic_name = self.prefix + self.cell_id + "system/active-alarms"
        self.client = client
        
        self.telegram_template = {
            "version": "v1.0",
            "timestamp": utils.get_datetime(),
            "alarms": []
        }
        
    async def send_telegram(self):
        # update timestamp
        self.telegram_template["timestamp"] = utils.get_datetime()
        # Send telegram
        await self.client.publish(self.topic_name, json.dumps(self.telegram_template))
        
    async def add_alarm(self, alarm_id, alarm_text, active):
        alarm = {
            "alarm-id": alarm_id,
            "alarm-text": alarm_text,
            "active": active
        }
        # If alarm is is not active, remove it from the list
        if not active:
            for alarm in self.telegram_template["alarms"]:
                if alarm["alarm-id"] == alarm_id:
                    self.telegram_template["alarms"].remove(alarm)
        else:
            # Only add alarm if it is not already in the list
            if alarm not in self.telegram_template["alarms"]:
                self.telegram_template["alarms"].append(alarm)
                

#5.3.1 Get Layer Pattern (Cell -> HLC)
#Sent by the palletizing cell when a layer pattern has changed or when requested by the HLC.
class send_layer_pattern:
    def __init__(self, prefix, cell_id, client):
        # Topic specific variables
        self.prefix = prefix
        self.cell_id = cell_id
        self.topic_name = self.prefix + self.cell_id + "layer-pattern"
        
        # MQTT specific variables
        self.client = client
        
        self.obj = None
        self.container_pattern = None
        
        self.telegram_template = {
            "version": "v1.0",
            "patterns": [],
            "timestamp": utils.get_datetime()
        }
        
        
    async def send_telegram(self):
        pattern_files = glob.glob("layer_patterns/*.json")
        telegram = self.telegram_template.copy()
        for pattern_file in pattern_files:
            pattern_json = json.load(open(pattern_file))
            # Remove the version from the pattern
            pattern_json.pop("version")
            telegram["patterns"].append(pattern_json)
        print(json.dumps(telegram))
        print("Sending layer pattern on topic: "+self.topic_name)
        await self.client.publish(self.topic_name, json.dumps(telegram)) # Send telegram
        
            
        


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
                    # Validate the message as a JSON object
                    try:
                        obj = json.loads(message.payload)
                        id = str(obj["id"])
                        pattern_file_name = "layer_patterns/"+id+".json"
                        # Add or update the layer pattern file in the layer_patterns folder
                        with open(pattern_file_name, "w+") as file:
                            json.dump(obj, file)
                        print("Layer pattern file updated: "+pattern_file_name)
                        # Close the file
                        file.close()
                        # Send  the layer pattern back to the HLC to confirm that it was received
                        send_layer_pattern_class = send_layer_pattern(self.prefix, self.cell_id, self.client)
                        await send_layer_pattern_class.send_telegram()
                    except:
                        print("Invalid layer pattern telegram received")
                        topic = self.prefix + self.cell_id + "layer-pattern"
                        await send_error_message(topic, self.client, "ERR_INVALID_MESSAGE")
                    
                        
                    


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