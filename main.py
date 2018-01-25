from machine import Pin, I2C
from ustruct import unpack
import time
i2c = I2C(scl=Pin(5),sda = Pin(4), freq = 100000)
i2c.start()
adr = i2c.scan()
i2c.writeto(adr[0],bytearray([0x70, 0xA0, 0x01]))
xyz = [0,0,0]
while(1):
    time.sleep(0.1)
    prev_xyz = xyz
    data = i2c.readfrom(adr[0],6)
    temp = unpack('>hhh', data)
    xyz = [temp[0],temp[1],temp[2]]
    diff = [xyz[0]-prev_xyz[0],xyz[1]-prev_xyz[1],xyz[2]-prev_xyz[2]]
    print(diff)
    # i2c.writeto(adr[0],bytearray([0x03]))
    i2c.writeto_mem(adr[0],0x02,bytearray([0x01]))
