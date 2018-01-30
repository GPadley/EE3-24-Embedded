from machine import Pin, I2C
from ustruct import unpack
import time
i2c = I2C(scl=Pin(5),sda = Pin(4), freq = 100000)
i2c.start()
adr = i2c.scan()
i2c.writeto(adr[0],bytearray([0x70, 0xA0, 0x01]))
data = i2c.readfrom(adr[0],6)
temp = unpack('>hhh', data)
xyz = [temp[0],temp[1],temp[2]]
i2c.writeto_mem(adr[0],0x02,bytearray([0x01]))
n = 0
while(1):
    time.sleep_ms(10) #break time
    data = i2c.readfrom(adr[0],6) #reads 6 bytes of data, 2 bytes per direction
    temp = unpack('>hhh', data) #unpacks data into a tuple
    xyz = [temp[0],temp[1],temp[2]] #converts to list for manipulation
    if n == 0:
        mean = xyz #allows bias averaging
    diff = [xyz[0]-mean[0],xyz[1]-mean[1],xyz[2]-mean[2]] #normalises data
    r = (diff[0]*diff[0]+diff[1]*diff[1]+diff[2]*diff[2]) #sees how far away from the norm the data is
    if r <= 20: #if larger than 20 then recalculate the mean
        if n == 0:
            n += 1
        else:
            mean = [round((n*mean[0]+xyz[0])/(n+1)),round((n*mean[1]+xyz[1])/(n+1)),round((n*mean[2]+xyz[2])/(n+1))]
            n += 1
    print(str(diff[0])+','+str(diff[1])+','+str(diff[2]))
    # i2c.writeto(adr[0],bytearray([0x03]))
    i2c.writeto_mem(adr[0],0x02,bytearray([0x01]))
