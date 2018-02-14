package com.magnets.magnaspeed;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.support.v7.app.AppCompatActivity;
import android.text.format.DateUtils;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.CompoundButton;
import android.widget.TextView;
import android.widget.ToggleButton;

import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.json.JSONObject;

/*To do -
    Send wheel size in mm - before start message
    Option for wheel size
    Option for units
    Make it pretty
    bigger font size



*/
public class MainActivity extends AppCompatActivity {

//    private ToggleButton toggle; //Can this get commented out????
    String startmessage;
    String resetmessage;
    String killmessage;
    String speedAppend;
    String distanceAppend;
    String unitsID;
    Double speedMultiply;
    Double distanceMultiply;
    SharedPreferences sharedPref;
    MQTTstuff mqttstuff;
    TextView timeDisplay;
    TextView maxSpeed;
    TextView currentSpeed;
    TextView avgSpeed;
    TextView distance;

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.main, menu);
        return true;
    }
    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            Intent intent = new Intent(this, SettingsActivity.class);
            startActivity(intent);
            return true;
        }

        return super.onOptionsItemSelected(item);
    }



    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
      //  ToggleButton toggle = (ToggleButton) findViewById(R.id.startToggleButton);
        timeDisplay = findViewById(R.id.time);
        distance = findViewById(R.id.Distance);
        currentSpeed = findViewById(R.id.speed);
        avgSpeed = findViewById(R.id.Avg_Speed);
        maxSpeed = findViewById(R.id.Max_speed);

        sharedPref = PreferenceManager.getDefaultSharedPreferences(this);
        startmessage = sharedPref.getString("mqtt_message_start", "DEFAULT");
        resetmessage = sharedPref.getString("mqtt_message_reset","DEFAULT");
        killmessage = sharedPref.getString("mqtt_message_kill","DEFAULT");
        unitsID = sharedPref.getString("units_list", "DEFAULT");
        unitDecoding();
        startMqtt();
    }

    private SharedPreferences.OnSharedPreferenceChangeListener listener;


    @Override
    public void onResume() {
        super.onResume();
        unitDecoding();         //Dodgy way of doing things. Couldn't get preferences change listener working
    }

    public void unitDecoding(){
        unitsID = sharedPref.getString("units_list", "DEFAULT");
        if (unitsID.equals("1")){
            speedMultiply = 1.0;
            distanceMultiply = 1.0;
            distanceAppend = " m";
            speedAppend = " m/s";

        }
        else if(unitsID.equals("2")){
            speedMultiply = 3.6;
            distanceMultiply = 0.001;
            distanceAppend = " km";
            speedAppend = " km/h";

        }
        else if(unitsID.equals("3")){
            speedMultiply = 2.2369363;
            distanceMultiply = 0.000621371192;
            distanceAppend = " miles";
            speedAppend = " mph";
        }


    }

    public void toggleclick(View view){
        if(((ToggleButton) view).isChecked()){
            //WHY CAN't I HAVE START MQTT BEFORE IT. STUPID NULL POINT EXCEPTIONS
            mqttstuff.publish(startmessage);
//            startMqtt();
        }
        else{
            mqttstuff.publish(killmessage);

        }
    }


    public void mqttReset(View view){
        mqttstuff.publish(resetmessage);
    }

    public void startMqtt() {
        mqttstuff = new MQTTstuff(getApplicationContext());
        mqttstuff.setCallback(new MqttCallbackExtended() {
            @Override
            public void connectComplete(boolean b, String s) {
//                mqttstuff.publish(startmessage);
            }

            @Override
            public void connectionLost(Throwable throwable) {

            }

            @Override
            public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
                Log.w("Debug", mqttMessage.toString());
                // String in = mqttMessage.toString();
                JSONObject dataInput = new JSONObject(mqttMessage.toString());
                String timePrint  = DateUtils.formatElapsedTime(Integer.parseInt(dataInput.getString("t"))/1000);
                String distancePrint = Double.toString(Double.parseDouble(dataInput.getString("d")) *distanceMultiply) + distanceAppend;
                String currSpeedPrint = Double.toString(Double.parseDouble(dataInput.getString("s")) *speedMultiply) + speedAppend;
                String avgSpeedPrint = Double.toString(Double.parseDouble(dataInput.getString("a")) *speedMultiply) + speedAppend;
                String maxSpeedPrint = Double.toString(Double.parseDouble(dataInput.getString("m")) *speedMultiply) + speedAppend;
                timeDisplay.setText(timePrint);
                distance.setText(distancePrint );
                currentSpeed.setText(currSpeedPrint);
                avgSpeed.setText(avgSpeedPrint);
                maxSpeed.setText(maxSpeedPrint);

            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken iMqttDeliveryToken) {

            }
        });

    }


}