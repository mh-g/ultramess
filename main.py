from machine import UART, Pin
import time
import binascii

# === mbus_checksum ===============================================================================
def mbus_checksum(data, skip):
    sum=0
    for i in range(0, len(data)):
        if i >= skip:
            sum = sum + int(data[i])
    return bytearray([sum & 255])

# === check_result ================================================================================
def check_result(where, ser):
    result = ser.read(1)
    if result == b'\xe5':
        return True
    else:
        if result is None:
            return True
        else:
            print(f'{where}: bad answer: {binascii.hexlify(bytearray(result), ' ')}')
            return False
        
# === get_data ====================================================================================
def get_data(ser):
    # 2.5: at 2400, 8N1 to send 2.2s of alternating bits
    ser.write(b'\x55' * 528)
    
    # time.sleep(2.0) # 2.0s sleep -> 0.8s break -> 1.2s until the buffer is empty ...
    time.sleep(1.2 + 170.0 / 2400.0)

    # 2.3: change parity
    ser.init(parity=0)  # 0=even

    # 2.7.1: do selection, use jokers for serial, manufacturer, ID, medium
    # 17 chars, 0.08s outgoing
    selection = b'\x68\x0B\x0B\x68\x53\xFD\x52\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
    ser.write(selection)
    ser.write(mbus_checksum(selection, 4))
    ser.write(b'\x16')
    # result arrives after 0.19s - 0.30s
    check_result('Selection', ser)

    # 3.1: do application reset 0x50 (to read instant values)
    # 10 chars, 0.05s outgoing
    app_reset = b'\x68\x04\x04\x68\x53\xFD\x50\x50'
    ser.write(app_reset)
    ser.write(mbus_checksum(app_reset, 4))
    ser.write(b'\x16')
    # result arrives after 0.08s
    check_result('Application reset', ser)

    # 3.2: do read data
    # 5 chars, 0.02s
    read_data = b'\x10\x7B\xFD'
    ser.write(read_data)
    ser.write(mbus_checksum(read_data, 1))
    ser.write(b'\x16')
    # result arrives after 0.07s, is 0.71s long (ca. 173 bytes)
    result = ser.read(200)  # 173 bytes plus some reserves
    if result is None:
        print('No data received')
    else:
        # debug output (hex dump) of received data
        print(f'user data bytes: {binascii.hexlify(bytearray(result), ' ')}')

    # 2.7.2: do deselection
    # 5 chars, 0.02s
    deselection = b'\x10\x40\xfd'
    ser.write(deselection)
    ser.write(mbus_checksum(deselection, 0))
    ser.write(b'\x16')
    check_result('Deselection', ser)

    # return bytes received
    return result


# === main ========================================================================================
print('Starting up ...\n')
# 2.5: 2400, 8N1 to send 2.2s of alternating bits, long timeout due to slow response by Ultramess
ser = UART(0, baudrate=2400, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1), timeout=500)

while True:
    print('Reading #0')
    result = get_data(ser)

    # change from pins 0/1 to 12/13, disable old pins by setting them to input
    ser.init(0, tx=Pin(12), rx=Pin(13))
    tx_unused = Pin(0, Pin.IN)
    rx_unused = Pin (1, Pin.IN)

    print('Reading #1')
    result = get_data(ser)

    # change from pins 12/13 to 0/1, disable old pins by setting them to input
    ser.init(0, tx=Pin(0), rx=Pin(1))
    tx_unused = Pin(12, Pin.IN)
    rx_unused = Pin (13, Pin.IN)

    time.sleep(5.0)