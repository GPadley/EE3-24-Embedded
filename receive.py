import paho.mqtt.client as mqtt
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
n = 25
x = deque(maxlen=n)
y = deque(maxlen=n)
z = deque(maxlen=n)
plt.ion()
fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)


def animate(data):
    x.append(data['x'])
    y.append(data['y'])
    z.append(data['z'])
    ax1.clear()
    ax1.plot(x)
    ax1.plot(y)
    ax1.plot(z)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))


    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe('esys/IoT')

# The callback for when a PUBLISH message is received from the server.
def  on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    ani = animation.FuncAnimation(fig, animate(data), interval=10)
    fig.canvas.draw()


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect('192.168.0.10',keepalive=10)

#
#

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
