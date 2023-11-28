from machine import UART, Pin
import time
import binascii
import network
from simple import MQTTClient

# contains the local WIFI credentials
import credentials


# === get_topic_name ==============================================================================
def get_topic_name(which):
    return 'heat/in' if which == 0 else 'heat/out'


# === get_pins ====================================================================================
def get_pins(which):
    return {"tx": Pin(0), "rx": Pin(1)} if which == 0 else {"tx": Pin(12), "rx": Pin(13)}


# === mbus_checksum ===============================================================================
def mbus_checksum(data, skip):
    checksum = 0
    for i in range(0, len(data)):
        if i >= skip:
            checksum = checksum + int(data[i])
    return bytearray([checksum & 255])


# === check_result ================================================================================
def check_result(which, ser):
    result_char = ser.read(1)
    if result_char == b'\xe5':
        # print(f'!!!!! {which} got e5')
        return True
    else:
        if result_char is None:
            # print(f'!!!!! {which} got None')
            return True
        else:
            print(f'{get_topic_name(which)}: bad answer: {binascii.hexlify(bytearray(result_char), " ")}')
            return False


# === get_data_ultramess ==========================================================================
def get_data_ultramess(which):
    # 2.5: 2400, 8N1 to send 2.2s of alternating bits, long timeout due to slow response by Ultramess
    ser = UART(0, baudrate=2400, bits=8, parity=None, stop=1, tx=get_pins(which)['tx'], rx=get_pins(which)['rx'], timeout=500)
    tx_unused = Pin(get_pins(1 - which)['tx'], Pin.IN)
    rx_unused = Pin(get_pins(1 - which)['rx'], Pin.IN)

    # print(ser)

    # 2.5: at 2400, 8N1 to send 2.2s of alternating bits
    ser.write(b'\x55' * 528)
    ser.flush()

    # 2.5: wait 11-330 bit times (here: 170 chosen)
    # time.sleep(2.0) # 2.0s sleep -> 0.8s break -> 1.2s until the buffer is empty ...
    time.sleep(1.2 + 170.0 / 2400.0)
    # time.sleep(170.0 / 2400.0)

    # 2.3: change parity
    ser.init(parity=0)  # 0=even
    # print(ser)

    # 2.7.1: do selection, use jokers for serial, manufacturer, ID, medium
    # 17 chars, 0.08s outgoing
    selection = b'\x68\x0B\x0B\x68\x53\xFD\x52\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
    ser.write(selection)
    ser.write(mbus_checksum(selection, 4))
    ser.write(b'\x16')
    ser.flush()
    # result arrives after 0.19s - 0.30s
    check_result('Selection', ser)

    # 3.1: do application reset 0x50 (to read instant values)
    # 10 chars, 0.05s outgoing
    app_reset = b'\x68\x04\x04\x68\x53\xFD\x50\x50'
    ser.write(app_reset)
    ser.write(mbus_checksum(app_reset, 4))
    ser.write(b'\x16')
    ser.flush()
    # result arrives after 0.08s
    check_result('Application reset', ser)

    # 3.2: do read data
    # 5 chars, 0.02s
    read_data = b'\x10\x7B\xFD'
    ser.write(read_data)
    ser.write(mbus_checksum(read_data, 1))
    ser.write(b'\x16')
    ser.flush()
    # result arrives after 0.07s, is 0.71s long (ca. 173 bytes)
    answer = ser.read(200)  # 173 bytes plus some reserves
    if answer is None:
        print('No data received')
        mqtt_publish(get_topic_name(which), 'No data.')
    else:
        # debug output (hex dump) of received data
        print(f'user data bytes: {binascii.hexlify(bytearray(answer), " ")}')
        mqtt_publish(get_topic_name(which), answer)

    # 2.7.2: do deselection
    # 5 chars, 0.02s
    deselection = b'\x10\x40\xfd'
    ser.write(deselection)
    ser.write(mbus_checksum(deselection, 0))
    ser.write(b'\x16')
    ser.flush()
    check_result('Deselection', ser)

    # disable old pins
    ser.deinit()

    # return bytes received
    return answer


# === get_data_logarex ============================================================================
def get_data_logarex(ser, which):
    result = ser.read()
    if result is None:
        print('No data received')
        mqtt_publish(which, 'No data.')
    else:
        # debug output (hex dump) of received data
        print(f'user data bytes: {binascii.hexlify(bytearray(result), " ")}')
        mqtt_publish(which, result)

    # return bytes received
    return result


# === wlan_connect ================================================================================
def wlan_connect():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print(f'Establishing WLAN connection to: {wlanSSID}')
        wlan.active(True)
        wlan.connect(wlanSSID, wlanPW)
        for i in range(10):
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            time.sleep(1)
    if wlan.isconnected():
        print(f'Success, status: {wlan.status()}')
    else:
        print(f'Failure, status: {wlan.status()}')


# === mqtt_connect ================================================================================
def mqtt_connect():
    if mqttUser != '' and mqttPW != '':
        print(f'Connect to MQTT broker {mqttBroker} as client {mqttClient} with user {mqttUser}.')
        client = MQTTClient(mqttClient, mqttBroker, user=mqttUser, password=mqttPW)
    else:
        print(f'Connect to MQTT broker {mqttBroker} as client {mqttClient}.')
        client = MQTTClient(mqttClient, mqttBroker)
    client.connect()
    print('Success.')
    return client


# === mqtt_publish ================================================================================
def mqtt_publish(which, data):
    try:
        client = mqtt_connect()
        print(f'{mqttTopic}{which}')
        client.publish(f'{mqttTopic}{which}', data)
        client.disconnect()
        print('Published and closed MQTT connection.')
    except OSError:
        print()
        print('Error: No MQTT connection.')


# === main ========================================================================================
print('Starting up ...\n')

# WLAN configuration
wlanSSID = credentials.getSSID()
wlanPW = credentials.getPassword()
network.country('DE')

# MQTT configuration
mqttBroker = credentials.getBroker()
mqttClient = credentials.getClient()
mqttUser = 'mqttuser'
mqttPW = ''
mqttTopic = '/utilities/'

# Establish connection
wlan_connect()

# 9600, 7E1 for Logarex LK13B
ser_logarex = UART(1, baudrate=9600, bits=7, parity=1, stop=1, tx=Pin(4), rx=Pin(5), rxbuf=6144, timeout_char=500)

while True:
    print('\nReading #0')
    result = get_data_ultramess(0)

    print('\nReading #1')
    result = get_data_ultramess(1)

    # electric power is on a different UART
    print('Reading Logarex')
    result = get_data_logarex(ser_logarex, 'electricity')

    print('Pausing ...')
    time.sleep(0.25)
