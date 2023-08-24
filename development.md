# 🛠 Development

## Programming

### How to start

Create a python app which starts with the class Addon:

```python
class Addon():
    """Addon module"""

    def __init__(self, lnxlink):
        """Setup addon"""
        self.name = "New Module"
```

### Get Sensor information

The method `getControlInfo` should return the value of the sensor you want to create. This can be one of these categories:

* String
* Integer
* Boolean
* JSON that contains keys with any of the above types

```python
    def get_info(self):
        """Gather information from the system"""
        return {
            "status": 5
        }
```

### Expose Sensors and Controls

A new method under the `Addon` class has to be created which returns a dictionary with options specific for the sensor you want:

```python
    def exposed_controls(self):
        """Exposes to home assistant"""
        return {
            "New Module": {
                "type": "sensor",
            },
        }
```

Bellow you can read more about each available option

#### type

This is required which is responsible for sending the appropriate type of command to the discovery of home assistant. These are the available types that are supported:

* sensor
* binary\_sensor
* button
* switch
* text
* number
* select
* camera
* update

#### value\_template

This is required only if the `getControlInfo` method returns a dictionary and you want to get a value from that to display. You can change the status to the dictionary key you want:

```python
  "value_template": "{{ value_json.status }}"
```

#### icon

Any icon supported by home assistant can be added. More information on their [site](https://www.home-assistant.io/docs/frontend/icons/).

```python
  "icon": "mdi:battery"
```

#### unit

This is used only for types `sensor` and `number` which defines the unit of measurement of the sensor.

```python
  "unit": "%"
```

#### device\_class

This is used for the sensors `binary_sensor`, `button`, `number`, `sensor`, `switch`, `update` and defines. Each sensor has different options, so you will have to read the documentation on each integration on [Home Assistant website](https://www.home-assistant.io/integrations/).

```python
"device_class": "battery"
```

state\_class

This is used only for the type `sensor` which is described [here](https://developers.home-assistant.io/docs/core/entity/sensor/#available-state-classes). These are the available options:

* measurement
* total
* total\_increasing

```python
  "state_class": "measurement"
```

#### entity\_category

This changes the category of the sensor to be one of these:

* diagnostic
* config

```python
  "entity_category": "diagnostic"
```

#### enabled

It tells home assistant to enable or disable the entity. By default it is `True`.

```python
  "enabled": False
```

#### entity\_picture

This is used only for the `update` sensor.

```python
  "entity_picture": "https://github.com/bkbilly/lnxlink/raw/master/logo.png?raw=true"
```

#### title

This is used only for the `update` sensor.

```python
  "title": "LNXlink"
```

### Control System

You can write the command you want to run when the topic containing the `commands` string is published to the MQTT server. The argument topic is a list separated with a slash (`/`). The argument data is a string or a json.

```python
    def start_control(self, topic, data):
        """Control system"""
        print(topic)
        print(data)
```

