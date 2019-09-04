package com.halilibo.sample

import android.content.Intent
import android.content.pm.ActivityInfo
import android.content.res.Configuration
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.ArrayAdapter
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.halilibo.bvpkotlin.BetterVideoPlayer
import com.halilibo.bvpkotlin.VideoCallback
import com.halilibo.bvpkotlin.captions.CaptionsView

import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.api.GoogleApiClient;
import com.google.android.gms.common.api.ResultCallback;
import com.google.android.gms.common.api.Status;
import com.google.android.gms.nearby.Nearby;

import android.content.SharedPreferences
import android.text.TextUtils
import android.widget.Toast
import androidx.appcompat.widget.SwitchCompat
import com.google.android.gms.nearby.messages.*
import com.google.android.gms.nearby.messages.samples.nearbydevices.DeviceMessage
import java.util.*


class MainActivity : AppCompatActivity(){


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_SENSOR


        findViewById<View>(R.id.cam1_button).setOnClickListener {

            var camIntent = Intent(this@MainActivity, FullscreenActivity::class.java)
            camIntent.putExtra("resource","Cam1");
            startActivity(camIntent)
        }

        findViewById<View>(R.id.audio_button).setOnClickListener {
            var audioIntent = Intent(this@MainActivity, FullscreenActivity::class.java)
            audioIntent.putExtra("resource","Audio");
            startActivity(audioIntent)
        }

        findViewById<View>(R.id.event_generator_button).setOnClickListener {
            var camIntent = Intent(this@MainActivity, EventGenerator::class.java)
            startActivity(camIntent)
        }
        findViewById<View>(R.id.cam2_button).setOnClickListener {


            var camIntent = Intent(this@MainActivity, FullscreenActivity::class.java)
            camIntent.putExtra("resource","Cam2");
            startActivity(camIntent)
        }
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        if(newConfig.orientation == Configuration.ORIENTATION_LANDSCAPE) {
            supportActionBar?.hide()
        } else if(newConfig.orientation == Configuration.ORIENTATION_PORTRAIT) {
            supportActionBar?.show()
        }
    }



    public override fun onPause() {
        //bvp.pause()
        super.onPause()
    }




    companion object {

        public val TAG = MainActivity::class.java!!.getSimpleName()

        private val TTL_IN_SECONDS = 3 * 60 // Three minutes.

        // Key used in writing to and reading from SharedPreferences.
        private val KEY_UUID = "key_uuid"

        /**
         * Sets the time in seconds for a published message or a subscription to live. Set to three
         * minutes in this sample.
         */
        private val PUB_SUB_STRATEGY = Strategy.Builder()
                .setTtlSeconds(TTL_IN_SECONDS).build()

    }
}
