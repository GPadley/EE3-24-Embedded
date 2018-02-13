package com.magnets.magnaspeed;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.support.v7.app.AppCompatActivity;
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

import static java.lang.Thread.sleep;

public class MainActivity extends AppCompatActivity {

    private ToggleButton toggle;
    Context context;
    String startmessage;
    String resetmessage;
    String killmessage;
    SharedPreferences sharedPref;

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
        ToggleButton toggle = (ToggleButton) findViewById(R.id.startToggleButton);
        dataReceived = (TextView) findViewById(R.id.dataReceived);
        sharedPref = PreferenceManager.getDefaultSharedPreferences(this);
        startmessage = sharedPref.getString("mqtt_message_start", "DEFAULT");
        resetmessage = sharedPref.getString("mqtt_message_reset","DEFAULT");
        killmessage = sharedPref.getString("mqtt_message_kill","DEFAULT");
        startMqtt();
    }


    public void toggleclick(View view){
        if(((ToggleButton) view).isChecked()){
           //WHY CAN't I HAVE START MQTT BEFORE IT. STUPID NULL POINT EXCEPTIONS
            mqttstuff.publish(startmessage);
        }
        else{
            mqttstuff.publish(killmessage);

        }
    }


    MQTTstuff mqttstuff;
    TextView dataReceived;

    public void mqttReset(View view){
        mqttstuff.publish(resetmessage);
    }
    public void startMqtt() {
        mqttstuff = new MQTTstuff(getApplicationContext());
        mqttstuff.setCallback(new MqttCallbackExtended() {
            @Override
            public void connectComplete(boolean b, String s) {

            }

            @Override
            public void connectionLost(Throwable throwable) {

            }

            @Override
            public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
                Log.w("Debug", mqttMessage.toString());

                dataReceived.setText(mqttMessage.toString());
            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken iMqttDeliveryToken) {

            }
        });

    }


}