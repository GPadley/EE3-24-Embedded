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
    mag = [0,0,0]
    a = 0;
    data = {'t':0,'s':0,'m':0,'a':0,'d':0} #resets the values
    state = 0 #case statement
    start_t = utime.ticks_ms() #resets the time of start
    pre_t = 0
    return n, data, state, start_t, pre_t, mag, a

def mean_calc(n,mean,input): #creates the mean averaging tool
    if n == 0:
        n += 1
    else:
        mean = round((n*mean+input)/(n+1)) #recalculates mean
        n += 1
    return n, mean

def wifi_conn():
    ap_if = network.WLAN(network.AP_IF) #connect to wifi
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('EEERover', 'exhibition')
    print('Awaiting WiFi connection...')
    a = 0
    while(not sta_if.isconnected()): #check to see if connected before trying to connect to MQTT
        if a == 0:
            b_led = Pin(2, Pin.OUT)
            a = 1
        else:
            b_led = Pin(2, Pin.IN)
            a = 0
        utime.sleep_ms(50)
    print('Connected')
    b_led = Pin(2, Pin.OUT)

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
    return raw[2]

#constants
start_msg = b'0xFFFFFFFFFFFF' #message from app to start loop
reset_msg = b'0x111111111111' #message from app to reset all values
kill_msg = b'0xAAAAAAAAAAAA' #message from app to stop transmission and reading
broker_ip = '192.168.0.10'
device_id = 'magnospeed_v1'
sub_topic = b'esys/IoT/Rx' #message from app to stop transmission and reading
pub_topic = 'esys/IoT/Tx' #message from app to stop transmission and reading
thresh = -120 #threshold value from the sensor



i2c = I2C(scl=Pin(5),sda = Pin(4), freq = 100000) #sets up the I2C pins and clock frequency
i2c.start() #starts reading values
adr = i2c.scan() #specifies address of sensor
# i2c.writeto(adr[0],bytearray([0x70, 0xE0, 0x01])) #tells the magnetometer to start reading sensor
i2c.writeto_mem(adr[0],0x00,bytearray([0x18])) #tells the sensor to continuously read data
i2c.writeto_mem(adr[0],0x01,bytearray([0x80])) #tells the sensor to continuously read data
i2c.writeto_mem(adr[0],0x02,bytearray([0x01])) #tells the sensor to continuously read data


sensor = sensor_read(adr[0])

wifi_conn()

i2c.writeto_mem(adr[0],0x02,bytearray([0x01])) #tells the sensor to continuously read data


client = cli_conn(device_id,broker_ip,sub_topic)


circ = 1.9478 #circumference of wheel in m
while(1):
    print('Awaiting start message')
    client.wait_msg()
    n, data, state, start_t, pre_t, mag, a = reset_var()
    if rx_msg == start_msg:

        print('Connected and verified')

        while(1):

            client.check_msg() #checks whether message has been received

            if rx_msg == reset_msg:
                rx_msg = b'0x000000000000' #resets so that the values aren't contantly set to 0
                print('Reset message recieved')
                n, data, state, start_t, pre_t, mag, a = reset_var()
                pub_message(data)

            elif rx_msg == kill_msg:
                print('Kill message received')
                break

            #reads 6 bytes of data, 2 bytes per direction
            sensor = sensor_read(adr[0])
            if n == 0:
                mean = sensor

            norm = sensor-mean
            if(utime.ticks_diff(utime.ticks_diff(utime.ticks_ms(),start_t),data['t'])>2000): #if the wheel hasn't turned for 2 seconds set speed to 0
                data['s'] = 0 #reset speed
                if pre_t == 0:
                    pre_t = data['t']
                data['t'] = utime.ticks_diff(utime.ticks_ms(),start_t) #restart time
                data['a'] = 1000*data['d']/(utime.ticks_diff(utime.ticks_ms(),start_t))
                pub_message(data) #transmit

            if norm < thresh and state != 1: #looks for impulse from magnet
                state = 1 #changes state
                r_led = Pin(0, Pin.OUT)

            elif norm >= thresh and state == 1:  #looks for magnet to be moved away
                r_led = Pin(0, Pin.IN)
                state = 0 #resets state
                if pre_t != 0:
                    data['s'] = 1000*circ/(utime.ticks_diff(utime.ticks_diff(utime.ticks_ms(),start_t),pre_t))
                    pre_t = 0
                else:
                    data['s'] = 1000*circ/(utime.ticks_diff(utime.ticks_diff(utime.ticks_ms(),start_t),data['t'])) #calculates speed in m/s and inputs into circular buffer
                data['t'] = utime.ticks_diff(utime.ticks_ms(),start_t)  #restart time
                data['d'] += circ #adds on one rotation of the wheel onto the distance travelled
                data['a'] = 1000*data['d']/(utime.ticks_diff(utime.ticks_ms(),start_t)) #average speed is distance travelled divided by total time

                if data['s'] > data['m']:
                    data['m'] = data['s']
                pub_message(data)

            elif abs(norm) <= 20:
                n,mean = mean_calc(n,mean,sensor)

            i2c.writeto_mem(adr[0],0x02,bytearray([0x01])) #tells the sensor to read data

    else:
        print('Wrong verification code')
