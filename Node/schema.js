// mongo schema for data logging

let mongoose = require("mongoose"); // for mongo database manipulation

let dataSchema = new mongoose.Schema({
  device_id: String,
  real_time: String,
  rel_time: Number,
  cur_speed: Number,
  max_speed: Number,
  avg_speed: Number,
  distance: Number,
});

module.exports = dataSchema;
