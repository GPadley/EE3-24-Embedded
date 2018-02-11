var mqtt = require('mqtt')
var client  = mqtt.connect('http://192.168.0.10')
var topicRx = 'esys/IoT/Rx' //sending data to device
var topicTx = 'esys/IoT/Tx' //reading data from device

//send heartbeat to device
function heartbeat()
{
  var date = new Date()
  var time = date.getHours()+ ':' + date.getMinutes() + ':' + date.getSeconds();
  client.publish(topicRx, '0xFFFFFFFFFFFF')
  console.log('heartbeat', time);
}

//When connected subscribe to topic and publish start commmand.
client.on('connect', function () {
  client.subscribe([topicTx, topicRx]);
  heartbeat();
  console.log('Connected');
})

//When message recieved print message to console
client.on('message', function (topic, message) {
  console.log(topic.toString(), message.toString())
})

//call heartbeat() every 5 seconds
setInterval(heartbeat, 5000);
// setInterval(function() {client.publish(topicRx, '0x111111111111')}, 10000)
