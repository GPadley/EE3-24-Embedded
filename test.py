from machine import Pin, I2C
from ustruct import unpack
i2c = I2C(scl=Pin(5),sda = Pin(4), freq = 100000)
i2c.start()
adr = i2c.scan()
i2c.writeto(adr[0],bytearray([0x70, 0xA0, 0x01])
data = i2c.readfrom(adr[0],6)
xyz = unpack('>hhh', data)
print(xyz)
