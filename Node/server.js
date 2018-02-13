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
let dataSchema = require('./schema.js');
// make mongo model
let dataModel = mongoose.model("hermes", dataSchema);

var yData = []; // global declaration of y-axis data for graphing


// --------------------------------------------------------------------------
// Settings over, here begins the actual code (tm)
// --------------------------------------------------------------------------

// Parse data and send to mongo
function passToMongo(dataIn)
{
  var data = JSON.parse(dataIn); // parse JSON data
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


// process data and pass to webpage for graphing
function passToGraph(response)
{
  yData = [];
  response.forEach(function(item) {
  yData.push(item.cur_speed);
  });
  yData = yData.slice(-200);
}

// Query Mongo for data
function runQuery()
{
  var query = dataModel.find({ 'device_id': '1' });
  query.select('real_time rel_time cur_speed');
  query.sort({'real_time': 1});
  var response = query.exec(function (err, out) {
    if (err) return handleError(err);
      passToGraph(out);
  })
}

// Query mongo every 0.5 second
setInterval(runQuery, 500);

// When connected to broker, subscribe to topics and publish start command.
client.on('connect', function () {
  client.subscribe([topicTx]);
  console.log('Connected');
  client.publish(topicRx, '0xFFFFFFFFFFFF')
})

// When message recieved, print message and push to mongo
client.on('message', function (topic, message) {
  console.log(topic.toString(), message.toString())
  passToMongo(message);
})

// setup webpage
app.get("/", (req, res) => {
  res.render('index', {yList: yData});
});

// use bodyparser to read through form submision
app.use(bodyParser.urlencoded({ extended: true }));

// log form submission to console
app.post('/', function (req, res) {
  res.render('index');
})

// log to console when webpage is running
app.listen(port, () => {
  console.log("Server listening on port " + port);
});
