from machine import Pin, I2C
from ustruct import unpack
from ujson import dumps
import network
from umqtt.simple import MQTTClient
import utime

def sub_cb(topic, msg):
    global d
    d = msg

i2c = I2C(scl=Pin(5),sda = Pin(4), freq = 100000)
i2c.start()
adr = i2c.scan()
i2c.writeto(adr[0],bytearray([0x70, 0xA0, 0x01]))
data = i2c.readfrom(adr[0],6)
temp = unpack('>hhh', data)
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
c = 1.9478 #circumference of wheel in m
N   = 3 #list size
delta = [0]*N #sets list of size N
n = 0 #mean bias
a = 0 #circular buffer
counter = 0;
state = 0 #case statement
client.subscribe(b'esys/IoT/Rx')
t = utime.ticks_ms() #takes the time in ms
starttime = utime.ticks_ms()
while(1):
    client.wait_msg()
    timeout = utime.ticks_ms()
    if d == b'0xFFFFFFFFFFFF':
        print('(Re)Connected and verified')
        while(1):

            client.check_msg() #checks whether message has been received

            if d == b'0xFFFFFFFFFFFF': #checks whether message has been received
                d = b'0x000000000000' #resets message to prove connection
                timeout = utime.ticks_ms() #resets timeout

            utime.sleep_ms(50) #break time
            #reads 6 bytes of data, 2 bytes per direction
            data = unpack('>hhh', i2c.readfrom(adr[0],6)) #unpacks data into a tuple
            xyz = [data[0],data[1],data[2]] #converts to list for manipulation

            if n == 0:
                mean = xyz #allows bias averaging
            diff = [xyz[0]-mean[0],xyz[1]-mean[1],xyz[2]-mean[2]] #normalises data

            r = (diff[0]*diff[0]+diff[1]*diff[1]+diff[2]*diff[2]) #sees how far away from the norm the data is

            if r >= 4000000 and state == 0: #looks for impulse from magnet
                state = 1 #changes state

            elif r < 4000000 and state == 1:  #looks for magnet to be moved away
                state = 0 #resets state
                delta[a] = 1000*c/(utime.ticks_diff(utime.ticks_ms(),t)) #calculates speed in m/s and inputs into circular buffer
                t = utime.ticks_ms() #restart time
                speed = (delta[0]+delta[1]+delta[2])/len(delta) #calculates average speed
                if counter == 0:
                    avg_speed = speed
                    max_speed = speed
                    distance = utime.ticks_diff(t,starttime)*avg_speed/1000
                    counter += 1
                else:
                    avg_speed = (counter*avg_speed+speed)/(counter+1)
                    counter += 1
                    distance = utime.ticks_diff(t,starttime)*avg_speed/1000
                if speed > max_speed:
                    max_speed = speed
                a = (a+1)%len(delta) #makes sure to wrap around
                out = dumps({'t':t/1000,'s':speed,'m':max_speed,'a':avg_speed,'d':distance}) #transmits dictionary of speed and time between samples
                if(utime.ticks_diff(utime.ticks_ms(),timeout)<12000):
                    client.publish('esys/IoT/Tx',bytes(out,'utf-8')) #submits to the receiver
                else:
                    print('No more signal detected')
            elif r <= 20: #if larger than 20 then recalculate the mean
                if n == 0:
                    n += 1
                else:
                    mean = [round((n*mean[0]+xyz[0])/(n+1)),round((n*mean[1]+xyz[1])/(n+1)),round((n*mean[2]+xyz[2])/(n+1))]
                    n += 1

            i2c.writeto_mem(adr[0],0x02,bytearray([0x01]))
    else:
        print('Wrong verification code')
