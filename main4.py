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
    mag = [0,0,0,0,0]
    a = 0;
    data = {'t':0,'s':0,'m':0,'a':0,'d':0} #resets the values
    state = 0 #case statement
    starttime = utime.ticks_ms() #resets the time of start
    return n,data,state,starttime,mag,a

def mean_calc(n,mean,input): #creates the mean averaging tool
    if n == 0:
        n += 1
    else:
        mean = [round((n*mean[0]+input[0])/(n+1)),round((n*mean[1]+input[1])/(n+1)),round((n*mean[2]+input[2])/(n+1))] #recalculates mean
        n += 1
    return n, mean



#constants
start_msg = b'0xFFFFFFFFFFFF' #message from app to start loop
reset_msg = b'0x111111111111' #message from app to reset all values
kill_msg = b'0xAAAAAAAAAAAA' #message from app to stop transmission and reading
broker_ip = '192.168.0.10'
device_id = 'magnospeed_v1'
sub_topic = b'esys/IoT/Rx' #message from app to stop transmission and reading
pub_topic = 'esys/IoT/Tx' #message from app to stop transmission and reading
thresh = 20000000 #threshold value from the sensor



i2c = I2C(scl=Pin(5),sda = Pin(4), freq = 100000) #sets up the I2C pins and clock frequency
i2c.start() #starts reading values
adr = i2c.scan() #specifies address of sensor
# i2c.writeto(adr[0],bytearray([0x70, 0xE0, 0x01])) #tells the magnetometer to start reading sensor
i2c.writeto_mem(adr[0],0x00,bytearray([0x70])) #tells the sensor to continuously read data
i2c.writeto_mem(adr[0],0x01,bytearray([0xA0])) #tells the sensor to continuously read data
i2c.writeto_mem(adr[0],0x02,bytearray([0x01])) #tells the sensor to continuously read data

def sensor_read(adr):
    raw = unpack('>hhh', i2c.readfrom(adr,6)) #unpacks data into a tuple
    sensor = [raw[0],raw[1],raw[2]] #converts to list for manipulation
    return sensor

sensor = sensor_read(adr[0])

i2c.writeto_mem(adr[0],0x02,bytearray([0x01])) #tells the sensor to continuously read data

ap_if = network.WLAN(network.AP_IF) #connect to wifi
ap_if.active(False)
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('EEERover', 'exhibition')

while(not sta_if.isconnected()): #check to see if connected before trying to connect to MQTT
    pass

client = MQTTClient(device_id,broker_ip)  #device ID and the broker IP
client.connect() #connect to MQTT
client.set_callback(sub_cb) #function which is called when message is received
client.subscribe(sub_topic) #where messages from app are recieved from

def pub_message(data):
    out = dumps(data) #transmits dictionary of speed and time between samples
    client.publish(pub_topic,bytes(out,'utf-8')) #submits to the receiver

circ = 1.9478 #circumference of wheel in m
# client.wait_msg()
while(1):
    client.wait_msg()
    n, data, state, starttime, mag, a = reset_var()
    if rx_msg == start_msg:

        print('Connected and verified')

        while(1):

            client.check_msg() #checks whether message has been received

            if rx_msg == reset_msg:
                rx_msg = b'0x000000000000' #resets so that the values aren't contantly set to 0
                print('Reset message recieved')
                n, data, state, starttime, mag, a = reset_var()

            elif rx_msg == kill_msg:
                print('Kill message received')
                break

            utime.sleep_ms(10) #break time
            #reads 6 bytes of data, 2 bytes per direction
            sensor = sensor_read(adr[0])

            print(sensor)
            if n == 0:
                mean = sensor #allows bias averaging
            diff = [sensor[0]-mean[0],sensor[1]-mean[1],sensor[2]-mean[2]] #normalises data

            #calculates magnitude of the sensor values
            mag[a] = (pow(diff[0],2)+pow(diff[1],2)+pow(diff[2],2)) #sees how far away from the norm the data is
            a = (a+1)%len(mag)
            mag_avg = (mag[0]+mag[1]+mag[2]+mag[3]+mag[4])/5
            if(utime.ticks_diff(utime.ticks_diff(utime.ticks_ms(),starttime),data['t'])>2000): #if the wheel hasn't turned for 2 seconds set speed to 0
                data['s'] = 0 #reset speed
                data['t'] = utime.ticks_diff(utime.ticks_ms(),starttime) #restart time
                pub_message(data) #transmit

            if mag_avg >= thresh and state != 1: #looks for impulse from magnet
                state = 1 #changes state

            elif mag_avg < thresh and state == 1:  #looks for magnet to be moved away
                state = 0 #resets state
                data['s'] = 1000*circ/(utime.ticks_diff(utime.ticks_diff(utime.ticks_ms(),starttime),data['t'])) #calculates speed in m/s and inputs into circular buffer
                data['t'] = utime.ticks_diff(utime.ticks_ms(),starttime)  #restart time
                data['d'] += circ #adds on one rotation of the wheel onto the distance travelled
                data['a'] = 1000*data['d']/(utime.ticks_diff(utime.ticks_ms(),starttime)) #average speed is distance travelled divided by total time

                if data['s'] > data['m']:
                    data['m'] = data['s']

                pub_message(data)

            elif mag_avg <= 10000: #if larger than 400 then recalculate the mean
                n, mean = mean_calc(n,mean,sensor)

            i2c.writeto_mem(adr[0],0x02,bytearray([0x01])) #tells the sensor to read data

    else:
        print('Wrong verification code')
