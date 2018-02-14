from machine import Pin, I2C
from ustruct import unpack
from ujson import dumps
import network
from umqtt.simple import MQTTClient
import utime
from math import pow

def sub_cb(topic, msg):
    global rx_msg
    rx_msg = msg

def reset_var():
    global data,n,state,starttime
    n = 0 #mean bias
    data = {'t':utime.ticks_ms(),'s':0,'m':0,'a':0,'d':0}
    counter = 0;
    state = 0 #case statement
    starttime = utime.ticks_ms()

def mean_calc(n,mean,input):
    if n == 0:
        n += 1
    else:
        mean = [round((n*mean[0]+input[0])/(n+1)),round((n*mean[1]+input[1])/(n+1)),round((n*mean[2]+input[2])/(n+1))]
        n += 1
    return mean


start_msg = b'0xFFFFFFFFFFFF'
reset_msg = b'0x111111111111'
kill_msg = b'0xAAAAAAAAAAAA'

i2c = I2C(scl=Pin(5),sda = Pin(4), freq = 100000)
i2c.start()
adr = i2c.scan()
i2c.writeto(adr[0],bytearray([0x70, 0xA0, 0x01]))
sensor = i2c.readfrom(adr[0],6)
temp = unpack('>hhh', sensor)
xyz = [temp[0],temp[1],temp[2]]
i2c.writeto_mem(adr[0],0x02,bytearray([0x01]))

ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect('EEERover', 'exhibition')

while(not sta_if.isconnected()):
    pass

client = MQTTClient('OmarnG','192.168.0.10')
client.connect()
client.set_callback(sub_cb)
client.subscribe(b'esys/IoT/Rx')

def pub_message(data):
    out = dumps(data) #transmits dictionary of speed and time between samples
    client.publish('esys/IoT/Tx',bytes(out,'utf-8')) #submits to the receiver

circ = 1.9478 #circumference of wheel in m
while(1):
    client.wait_msg()
    print(rx_msg)
    reset_var()
    if rx_msg == start_msg:
        print('Connected and verified')
        while(1):

            client.check_msg() #checks whether message has been received
            if rx_msg == reset_msg:
                rx_msg = b'0x000000000000'
                print('Reset message recieved')
                reset_var()
            elif rx_msg == kill_msg:
                print('Kill message received')
                break

            utime.sleep_ms(50) #break time
            #reads 6 bytes of data, 2 bytes per direction
            sensor = unpack('>hhh', i2c.readfrom(adr[0],6)) #unpacks data into a tuple
            xyz = [sensor[0],sensor[1],sensor[2]] #converts to list for manipulation

            if n == 0:
                mean = xyz #allows bias averaging
            diff = [xyz[0]-mean[0],xyz[1]-mean[1],xyz[2]-mean[2]] #normalises data
            mag = (diff[0]*diff[0]+diff[1]*diff[1]+diff[2]*diff[2]) #(pow(diff[0],2)+pow(diff[1],2)+pow(diff[2],2)) #sees how far away from the norm the data is
            print(mag)
            print(n)
            if(utime.ticks_diff(utime.ticks_ms(),data['t'])>2000 and state != 3):
                print('Timeout')
                state = 3
                data['s'] = 0
                data['t'] = utime.ticks_diff(utime.ticks_ms(),starttime) #restart time
                pub_message(data)

            if mag >= 4000000 and state != 1: #looks for impulse from magnet
                print('Detection')
                state = 1 #changes state

            elif mag < 4000000 and state == 1:  #looks for magnet to be moved away
                print('Magnet removal')
                state = 0 #resets state
                data['s'] = 1000*circ/(utime.ticks_diff(utime.ticks_ms(),data['t'])) #calculates speed in m/s and inputs into circular buffer
                data['t'] = utime.ticks_diff(utime.ticks_ms(),starttime) #restart time
                if counter == 0:
                    data['d'] = circ
                    data['a'] = 1000*circ/(utime.ticks_diff(utime.ticks_ms(),starttime))
                    data['m'] = data['s']
                    counter += 1
                else:
                    counter += 1
                    data['d'] += circ
                    data['a'] = 1000*data['d']/(utime.ticks_diff(utime.ticks_ms(),starttime))
                if data['s'] > data['m']:
                    data['m'] = data['s']
                pub_message(data)
            elif mag <= 20: #if larger than 20 then recalculate the mean
                mean = mean_calc(n,mean,xyz)

            i2c.writeto_mem(adr[0],0x02,bytearray([0x01]))
    else:
        print('Wrong verification code')
