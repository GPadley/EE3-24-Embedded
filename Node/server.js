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

var yData = []; // global declaration of y-axis data for graphing (Speed)
var xData = []; // gloabal declaration of x-axis data for graphing (Speed)
var target = 0; // speed target
var onindex = false; // trus if viewing the index page. Used for control of function calls
var xDistance = []; // global declaration of x-axis data for graphing (Distance)
var yDistance = []; // global declaration of y-axis data for graphing (Distance)


// --------------------------------------------------------------------------
// Settings over, here begins the actual code
// --------------------------------------------------------------------------

// Parse data and send to mongo
function passToMongo(dataIn)
{
  var data = JSON.parse(dataIn); // parse JSON data
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

// run Query for finding distance travelled
function distanceQuery()
{
  onindex = false;
  var query = dataModel.find({ 'device_id': '1' });
  query.select('real_time rel_time distance');
  query.sort({'rel_time': -1});
  query.limit(1000);
  var response = query.exec(function (err, out) {
    if (err) return handleError(err);
      let outR = out.reverse();
      xDistance = [];
      yDistance = [];
      outR.forEach(function(item){
        yDistance.push(item.distance);
        d = new Date(item.real_time);
        d8 = String(d.getUTCHours() + ':' + d.getUTCMinutes() + ':' + d.getUTCSeconds());
        xDistance.push(d8);
      })
    })
    yDistance = yDistance.slice(-1000);
    xDistance = xDistance.slice(-1000);
}


// process data and pass to webpage for graphing
function passToGraph(response)
{
  let responseR = response.reverse();
  yData = [];
  xData = [];
  responseR.forEach(function(item) {
    yData.push(item.cur_speed);
    d = new Date(item.real_time);
    d8 = String(d.getUTCHours() + ':' + d.getUTCMinutes() + ':' + d.getUTCSeconds());
    xData.push(d8);
  });
  yData = yData.slice(-200);
  xData = xData.slice(-200);
  target = Math.floor(Math.max(...yData));
  if(target > 20) target+=2;
  else if(target > 15) target+=3;
  else if(target > 10) target+=4;
  else target+=5;
  runQuery();
}

// Query Mongo for data
function runQuery()
{
  onindex = true;
  var query = dataModel.find({ 'device_id': '1' });
  query.select('real_time rel_time cur_speed');
  query.sort({'real_time': -1});
  query.limit(200);
  var response = query.exec(function (err, out) {
    if (err) return handleError(err);
      passToGraph(out);
  })
}

// Query mongo every 0.5 second

// When connected to broker, subscribe to topics and publish start command.
client.on('connect', function () {
  client.subscribe([topicTx]);
  console.log('Connected to Broker');
  client.publish(topicRx, '0xFFFFFFFFFFFF');
})

// When message recieved, print message and push to mongo
client.on('message', function (topic, message) {
  console.log(topic.toString(), message.toString())
  passToMongo(message);
})

// setup webpage
app.get("/", (req, res) => {
  res.render('index', {yList: yData, xList: xData,goal:target});
  if(!onindex)
  {
    runQuery();
  }
});

// use bodyparser to read through form submision
app.use(bodyParser.urlencoded({ extended: true }));
app.get('/distance', (req, res) => {
  distanceQuery();
  res.render('distance', {yList: yDistance, xList: xDistance});
  console.log('3 Day');
});


// log to console when webpage is running
app.listen(port, () => {
  console.log("Server listening on port " + port);
});
