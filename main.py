from machine import Pin, I2C
from ustruct import unpack
from ujson import dumps
import network
from umqtt.simple import MQTTClient
import utime
from math import pow, pi

def sub_cb(topic, msg):
    global rx_msg #allows received message to be used externally
    rx_msg = msg

def reset_var(): #reset function
    n = 0 #mean bias
    data = {'t':0,'s':0,'m':0,'a':0,'d':0} #resets the values
    state = 0 #case statement
    start_t = utime.ticks_ms() #resets the time of start
    pre_t = 0
    return n, data, state, start_t, pre_t

def mean_calc(n,mean,input): #creates the mean averaging tool
    if n == 0:
        n += 1
    else:
        mean = round((n*mean+input)/(n+1)) #recalculates mean
        n += 1
    return n, mean

def wifi_conn(wifi_SSID, wifi_key):
    ap_if = network.WLAN(network.AP_IF) #connect to wifi
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(wifi_SSID, wifi_key)
    print('Awaiting WiFi connection...')
    a = 0
    while(not sta_if.isconnected()): #check to see if connected before trying to connect to MQTT
        if a == 0:
            b_led = Pin(2, Pin.OUT) #sets blue LED on
            a = 1 #enables the toggle
        else:
            b_led = Pin(2, Pin.IN) #sets blue LED off
            a = 0
        utime.sleep_ms(50) #wait 50 ms to see flashing LED
    print('Connected')
    b_led = Pin(2, Pin.OUT) #once connected solid blue LED

def cli_conn(device_id,broker_ip,sub_topic):
    client = MQTTClient(device_id,broker_ip)  #device ID and the broker IP
    client.connect() #connect to MQTT
    client.set_callback(sub_cb) #function which is called when message is received
    client.subscribe(sub_topic) #where messages from app are recieved from
    return client

def pub_message(data):
    out = dumps(data) #transmits dictionary of speed and time between samples
    client.publish(pub_topic,bytes(out,'utf-8')) #submits to the receiver

def sensor_read(adr):
    raw = unpack('>hhh', i2c.readfrom(adr,6)) #unpacks data into a tuple
    return raw[2] #returns the z axis data

#constants
start_msg = b'0xFFFFFFFFFFFF' #message from app to start loop
reset_msg = b'0x111111111111' #message from app to reset all values
kill_msg = b'0xAAAAAAAAAAAA' #message from app to stop transmission and reading
broker_ip = '192.168.0.10' #MQTT broker ip
device_id = 'magnospeed_v1' #device ID
sub_topic = b'esys/IoT/Rx' #message from app to stop transmission and reading
pub_topic = 'esys/IoT/Tx' #message from app to stop transmission and reading
wifi_SSID = 'EEERover'
wifi_key = 'exhibition'
thresh = -120 #threshold value from the sensor



i2c = I2C(scl=Pin(5),sda = Pin(4), freq = 100000) #sets up the I2C pins and clock frequency
i2c.start() #starts reading values
adr = i2c.scan() #specifies address of sensor
# i2c.writeto(adr[0],bytearray([0x70, 0xE0, 0x01])) #tells the magnetometer to start reading sensor
i2c.writeto_mem(adr[0],0x00,bytearray([0x18])) #tells the sensor to continuously read data
i2c.writeto_mem(adr[0],0x01,bytearray([0x80])) #tells the sensor to continuously read data
i2c.writeto_mem(adr[0],0x02,bytearray([0x01])) #tells the sensor to continuously read data


sensor = sensor_read(adr[0]) #takes inital value due to always being 0

wifi_conn(wifi_SSID,wifi_key) #connects to wifi

i2c.writeto_mem(adr[0],0x02,bytearray([0x01])) #tells the sensor to continuously read data


client = cli_conn(device_id,broker_ip,sub_topic) #connects to the MQTT broker


client.wait_msg() #waits for diameter of the wheel in mm
diam_mm = eval(rx_msg[2:len(rx_msg)-1]) #parses the wheel diam from the string andd converts into a integer
circ = pi*diam_mm/1000 #converts into circumference to work out speed and distance in m
while(1):
    print('Awaiting start message') #awaits the 0xFFFFFFFFFFFF to start the code
    client.wait_msg()
    if rx_msg == start_msg:
        n, data, state, start_t, pre_t = reset_var() #resets all of the values
        print('Connected and verified')

        while(1):

            client.check_msg() #checks whether message has been received

            if rx_msg == reset_msg:
                rx_msg = b'0x000000000000' #resets so that the values aren't contantly set to 0
                print('Reset message recieved')
                n, data, state, start_t, pre_t = reset_var() #resets all of the values
                pub_message(data) #submits the 0 values to the app

            elif rx_msg == kill_msg:
                print('Kill message received') #exits the loop
                break

            #reads 6 bytes of data, 2 bytes per direction
            sensor = sensor_read(adr[0])
            if n == 0:
                mean = sensor #first reading the mean is set as the initial reading

            norm = sensor-mean #normalises the sensor to remove bias
            if(utime.ticks_diff(utime.ticks_diff(utime.ticks_ms(),start_t),data['t'])>2000): #if the wheel hasn't turned for 2 seconds set speed to 0
                data['s'] = 0 #reset speed
                if pre_t == 0: #for calculation of speed if no rotations for t > 2 s
                    pre_t = data['t'] #save the old value
                data['t'] = utime.ticks_diff(utime.ticks_ms(),start_t) #restart time
                data['a'] = 1000*data['d']/(utime.ticks_diff(utime.ticks_ms(),start_t)) #calculated average speed
                pub_message(data) #transmit

            if norm < thresh and state != 1: #looks for impulse from magnet
                state = 1 #changes state
                r_led = Pin(0, Pin.OUT) #sets the red led on when magnet nearby

            elif norm >= thresh and state == 1:  #looks for magnet to be moved away
                r_led = Pin(0, Pin.IN) #sets the red led off when magnet away
                state = 0 #resets state
                if pre_t != 0: #if speed has been 0 for some time calculate new speed
                    data['s'] = 1000*circ/(utime.ticks_diff(utime.ticks_diff(utime.ticks_ms(),start_t),pre_t))
                    pre_t = 0
                else:
                    data['s'] = 1000*circ/(utime.ticks_diff(utime.ticks_diff(utime.ticks_ms(),start_t),data['t'])) #calculates speed in m/s and inputs into circular buffer
                data['t'] = utime.ticks_diff(utime.ticks_ms(),start_t)  #restart time
                data['d'] += circ #adds on one rotation of the wheel onto the distance travelled
                data['a'] = 1000*data['d']/(utime.ticks_diff(utime.ticks_ms(),start_t)) #average speed is distance travelled divided by total time

                if data['s'] > data['m']: #is the speed is greater than the previous maximum, replace the max value
                    data['m'] = data['s']
                pub_message(data) #submit the data to the MQTT broker

            elif abs(norm) <= 20:
                n,mean = mean_calc(n,mean,sensor) #if the sensor value is low, recalculate mean value

            i2c.writeto_mem(adr[0],0x02,bytearray([0x01])) #tells the sensor to read data

    else:
        print('Wrong verification code')
