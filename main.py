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
    time.sleep(0.1)
    data = i2c.readfrom(adr[0],6)
    temp = unpack('>hhh', data)
    xyz = [temp[0],temp[1],temp[2]]
    if n == 0:
        mean = xyz
    diff = [xyz[0]-mean[0],xyz[1]-mean[1],xyz[2]-mean[2]]
    r = (diff[0]*diff[0]+diff[1]*diff[1]+diff[2]*diff[2])
    if r <= 20:
        if n == 0:
            mean = xyz
            n += 1
        else:
            mean = [round((n*mean[0]+xyz[0])/(n+1)),round((n*mean[1]+xyz[1])/(n+1)),round((n*mean[2]+xyz[2])/(n+1))]
            n += 1
    print(diff)
    # i2c.writeto(adr[0],bytearray([0x03]))
    i2c.writeto_mem(adr[0],0x02,bytearray([0x01]))
