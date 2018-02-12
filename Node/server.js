// Require modules needed
const mqtt = require('mqtt') // for MQTT comms
const mongoose = require("mongoose"); // for mongo database manipulation
const express = require("express"); // for webpage stuff
const bodyParser = require('body-parser');

// MQTT Settings
var client  = mqtt.connect('http://192.168.0.10') // IP of MQTT Broker
const topicRx = 'esys/IoT/Rx' // sending data to device
const topicTx = 'esys/IoT/Tx' // reading data from device

// Express settings
const app = express();
app.set('view engine', 'ejs')
app.use(express.static('public'));
const port = 3000;

// Mongoose Settings
mongoose.Promise = global.Promise;
mongoose.connect("mongodb://localhost:27017/embedded")

// get schema from schema.js
var dataSchema = require('./schema.js');

// make mongo model
var dataModel = mongoose.model("hermes", dataSchema);

// Parse data and send to mongo
function passToMongo(dataIn)
{
  // if data is the start message we have sent then return without pasring JSON
  // if(dataIn == '0xFFFFFFFFFFFF')
  // {
  //   return;
  // }
  data = JSON.parse(dataIn); // parse JSON data
  // create instance of model according to dataSchema
  let dataSend = new dataModel({
    device_id: '1',
    real_time: new Date(),
    rel_time: data.t,
    cur_speed: data.s,
    max_speed: data.m,
    avg_speed: data.a,
    distance: data.d,
  });
  // save data in mongo
  dataSend.save()
  .then(item => {
    console.log('item saved to database');
  })
  .catch(err => {
    console.log('unable to save to database');
  });
}

// send heartbeat to device
function heartbeat()
{
  var date = new Date()
  var time = date.getHours() + ':' + date.getMinutes() + ':' + date.getSeconds();
  client.publish(topicRx, '0xFFFFFFFFFFFF')
  console.log('heartbeat', time);
}

// When connected to broker, subscribe to topics and publish first heartbeat.
client.on('connect', function () {
  client.subscribe([topicTx]);
  heartbeat();
  console.log('Connected');
})

// When message recieved, print message and push to mongo
client.on('message', function (topic, message) {
  console.log(topic.toString(), message.toString())
  passToMongo(message);
})

// call heartbeat() every 5 seconds, starting @ t = 5
// setInterval(heartbeat, 5000);

// send kill command every 10 seconds - Not Good Idea. Only Use For Testing
// setInterval(function() {client.publish(topicRx, '0x111111111111')}, 10000)

// setup webpage
app.get("/", (req, res) => {
  res.render('index');
});

// use bodyparser to read through form submision
app.use(bodyParser.urlencoded({ extended: true }));

// log form submission to console
app.post('/', function (req, res) {
  res.render('index');
  console.log(req.body.city);
})

// log to console when webpage is running
app.listen(port, () => {
  console.log("Server listening on port " + port);
});
