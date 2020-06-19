# ebus
A Home Assistant component to communicate via ebus

## Install

### Manualy

Copy `ebus` folder in to your home-assistant `custom_components` folder.

Additionally a eBUS daemon must be installed on your Raspberry Pi or NUC.
https://ebusd.eu/

## Configure

Declare your ebus variables in the configuration. The values of the variables are automatically polled from the ebus.

### Example configuration
`configuration.yaml`
```yaml
# Define the ebus couplers available in your network
ebus:
  - ipv4_address: 192.168.178.100 #IP address of first eBUS coupler 
    port: 8888
    #hub_name: 'ebus_coupler_1' #Only needed if you use two or more eBUS couplers. Default name is 'ebusd'.
    #time_to_live_s: 5 #optional: time within the last read value is used before a new value is read from the bus. (default: 30 seconds)
#  - ipv4_address: 192.168.178.101 #IP address of second eBUS coupler
#    port: 8888
#    hub_name: 'ebus_coupler_2'
#    #time_to_live_s: 5 #optional

sensor:
  - platform: ebus
    sensors:
      - name: 'Heatpump status' #sensor.heatpump_status #define name for new sensor here
        circuit: '21576' #see column 1 of ebusd CSV file
        message: 'status.heatpump_1' #see column 2 of ebusd CSV file
        field_to_read: 'status' #see column ??(field) of ebusd CSV file and _templates.csv
        #hub_name: 'ebus_coupler_1' #Name of the ebus you want to access. Only needed if you use two or more eBUS couplers. Default name is 'ebusd'.
      - name: 'Temperature Room' #sensor.temperature_room
        circuit: '21576'
        message: 'temperature.room'
        field_to_read: 'temperature'
        icon: mdi:thermometer
        unit_of_measurement: '°C'
      - name: 'Temperature Buffer Upper Area' #sensor.temperature_buffer_upper_area
        circuit: '21576'
        message: 'temperature.buffer.tpo'
        field_to_read: 'temperature'
        icon: mdi:thermometer
        unit_of_measurement: TEMP_CELSIUS
      - name: 'Temperature Heating Manual Setpoint' #sensor.temperature_heating_manual_setpoint
        circuit: '21576'
        message: 'temperature.heating.manual.setpoint'
        field_to_read: 'temperature'
        icon: mdi:thermometer
        unit_of_measurement: TEMP_CELSIUS
```

The variable declaration above uses the definitions in the ebusd CSV file from the ebusd daemon. The CSV file is located in the /etc/ebusd/ folder. Below you will find parts of the CSV file that I use in my ebusd configuration.
```csv
# type (r[1-9];w;u),circuit,name,comment,QQ,ZZ,PBSB,ID,field,part (m;s),datatypes/templates,divider/values,unit,comment,field,part (m;s),datatypes/templates,divider/values,unit,comment,field,part (m;s),datatypes/templates,divider/values,unit,comment,field,part (m;s),datatypes/templates,divider/values,unit,comment,field,part (m;s),datatypes/templates,divider/values,unit,comment,field,part (m;s),datatypes/templates,divider/values,unit,comment,field,part (m;s),datatypes/templates,divider/values,unit,comment,field,part (m;s),datatypes/templates,divider/values,unit,comment,field,part (m;s),datatypes/templates,divider/values,unit,comment,field,part (m;s),datatypes/templates,divider/values,unit,comment,field,part (m;s),datatypes/templates,divider/values,unit,comment
#Ochsner,MF=TEM;ID=21576;SW=0373;HW=0110,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
#______________________________,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
*r,21576,,,,15,0621,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
*w,21576,,,,10,0623,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
#______________________________,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
r,,status.heatpump_1,02-053 Status heat generator control,,,,7d800002,,,param,,,,,,status,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
r,,temperature.room,00-001 Actual room temperature,,,,77830008,,,param,,,,,,tempt,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
r,,temperature.buffer.tpo,00-015 Buffer temperature (upper area),,,,7a800010,,,param,,,,,,tempt,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
r,,temperature.heating.manual.setpoint,07-009 Manual operation set temperature,,,,07890048,,,param,,,,,,tempt,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
w,,temperature.heating.manual.setpoint,07-009 Setpoint temperature manual mode,,,,07890048,,,tempt,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
```

The following example explains how to write a value to the ebus. At 11:45 a.m. the manual heating temperature is set to 28 °C.

`automations.yaml`
```yaml

- alias: 'Switch on heating'
  trigger:
    platform: time_pattern
    hours: "11"
    minutes: "45"
    seconds: "0"
  action:
    - service: ebus.ebus_write
      data:
        entity_id: sensor.temperature_heating_manual_setpoint
        value: 28
