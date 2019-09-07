package com.halilibo.sample

import android.annotation.SuppressLint
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import com.halilibo.bvpkotlin.BetterVideoPlayer
import android.util.Log
import com.halilibo.bvpkotlin.VideoCallback
import android.content.SharedPreferences
import android.text.TextUtils
import android.widget.Toast
import com.google.android.gms.common.ConnectionResult
import com.google.android.gms.common.api.GoogleApiClient
import com.google.android.gms.common.api.ResultCallback
import com.google.android.gms.common.api.Status
import com.google.android.gms.nearby.Nearby
import com.google.android.gms.nearby.messages.*
import com.google.android.gms.nearby.messages.samples.nearbydevices.DeviceMessage
import java.util.*


/**
 * An example full-screen activity that shows and hides the system UI (i.e.
 * status bar and navigation/system bar) with user interaction.
 */
class FullscreenActivity : AppCompatActivity(),GoogleApiClient.ConnectionCallbacks, GoogleApiClient.OnConnectionFailedListener {
    /**
     * BetterVideoPlayer variables:
     */
    private val mHideHandler = Handler()
    lateinit var mBetterVideoPlayer: BetterVideoPlayer

    /**
     * Global variables to store which resources we are using (i.e., if we're using audio, cams, etc.)
     */
    private  var eventVideoResource : Array<Int> ?= null
    private var normalVideoResource : Array<Int> ?= null

    /**
     * Global variables to indicate current status of app
     */
    private var eventPlaying : Boolean = false
    private var startEvent : Boolean = false
    private var reset : Boolean = false

    /**
     * Resource arrays (all the videos of the demo)
     */
    private var cam1NormalResources : Array<Int> = arrayOf(com.halilibo.sample.R.raw.normal_cam1_part1,com.halilibo.sample.R.raw.normal_cam1_part2,com.halilibo.sample.R.raw.normal_cam1_part3, com.halilibo.sample.R.raw.normal_cam1_part4, com.halilibo.sample.R.raw.normal_cam1_part5 )
    private var cam1EventResources : Array<Int> = arrayOf(com.halilibo.sample.R.raw.convoy_cam1_slow)
    private var cam2NormalResources : Array<Int> = arrayOf(com.halilibo.sample.R.raw.normal_cam2_part1, com.halilibo.sample.R.raw.normal_cam2_part2)
    private var cam2EventResources : Array<Int> = arrayOf(com.halilibo.sample.R.raw.convoy_cam2_slow)
    private var audioNormalResources : Array<Int> = arrayOf(com.halilibo.sample.R.raw.audio_normal_1,com.halilibo.sample.R.raw.audio_normal_2,com.halilibo.sample.R.raw.audio_normal_3,com.halilibo.sample.R.raw.audio_normal_4, com.halilibo.sample.R.raw.audio_normal_5)
    private var audioEventResources : Array<Int> = arrayOf(com.halilibo.sample.R.raw.audio_gunshot1, com.halilibo.sample.R.raw.audio_gunshot2)

    /**
     * Current Sensor type
     */
    private var sensorID : SENSOR_ID ?= null

    /**
     * Pub/Sub Messages; @TODO: move this to an enum class to be shared across classes
     */
    public val CAM1_START_MESSAGE = "Cam1Start"
    public val CAM2_START_MESSAGE = "Cam2Start"
    public val CAM1_FINISH_MESSAGE = "Cam1Finished"
    public val CAM2_FINISH_MESSAGE = "Cam2Finished"
    public val AUDIO_START_MESSAGE = "AudioStart"
    public val AUDIO_FINISH_MESSAGE = "AudioFinish"
    public val RESET_MESSAGE = "Reset"

    /**
     * The [Message] object used to broadcast information about the device to nearby devices.
     */
    private var mPubMessage: Message ?= null


    /**
     * A [MessageListener] for processing messages from nearby devices.
     */
    private var mMessageListener: MessageListener? = null



    /**
     * The entry point to Google Play Services.
     */
    private var mGoogleApiClient: GoogleApiClient? = null

    private val mHidePart2Runnable = Runnable {
        // Delayed removal of status and navigation bar

        // Note that some of these constants are new as of API 16 (Jelly Bean)
        // and API 19 (KitKat). It is safe to use them, as they are inlined
        // at compile-time and do nothing on earlier devices.
        mBetterVideoPlayer.systemUiVisibility = (View.SYSTEM_UI_FLAG_LOW_PROFILE
                or View.SYSTEM_UI_FLAG_FULLSCREEN
                or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                or View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION)
    }

    private val mShowPart2Runnable = Runnable {
        // Delayed display of UI elements
        val actionBar = supportActionBar
        actionBar?.show()
    }

    private var mVisible: Boolean = false
    private val mHideRunnable = Runnable { hide() }
    /**
     * Touch listener to use for in-layout UI controls to delay hiding the
     * system UI. This is to prevent the jarring behavior of controls going away
     * while interacting with activity UI.
     */
    private val mDelayHideTouchListener = View.OnTouchListener { view, motionEvent ->
        if (AUTO_HIDE) {
            delayedHide(AUTO_HIDE_DELAY_MILLIS)
        }
        false
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        buildGoogleApiClient()
        setContentView(R.layout.activity_fullscreen)
        val myIntent = intent // gets the previously created intent
        val resChoice = myIntent.getStringExtra("resource") // will return "FirstKeyValue"
        if (resChoice == "Cam1")
        {
            eventVideoResource = cam1EventResources
            normalVideoResource = cam1NormalResources//"android.resource://" + packageName + "/" + cam1NormalResources[randomInteger]
            sensorID = SENSOR_ID.CAM1
        }else if(resChoice == "Cam2")
        {
            eventVideoResource =  cam2EventResources
            normalVideoResource = cam2NormalResources//"android.resource://" + packageName + "/" + cam1NormalResources[randomInteger]
            sensorID = SENSOR_ID.CAM2
        }else if(resChoice == "Audio")
        {
            eventVideoResource = audioEventResources
            normalVideoResource = audioNormalResources
            sensorID = SENSOR_ID.AUDIO
        }


        mVisible = false
        mBetterVideoPlayer = findViewById(R.id.bvp)!!
        mBetterVideoPlayer.setSource(Uri.parse("android.resource://" + packageName + "/" + normalVideoResource?.get((1..normalVideoResource?.size!!).shuffled().first()-1)))
        mBetterVideoPlayer.setLoop(true)
        mBetterVideoPlayer
        mBetterVideoPlayer.getToolbar().title = resChoice + " Feed"
        mBetterVideoPlayer.getToolbar()
                .setNavigationIcon(androidx.appcompat.R.drawable.abc_ic_ab_back_material)
        mBetterVideoPlayer.getToolbar().setNavigationOnClickListener { onBackPressed() }


        mBetterVideoPlayer.setCallback(object : VideoCallback {
            override fun onStarted(player: BetterVideoPlayer) {
                Log.i(TAG, "Started")
            }

            override fun onPaused(player: BetterVideoPlayer) {
                Log.i(TAG, "Paused")
            }

            override fun onPreparing(player: BetterVideoPlayer) {
                Log.i(TAG, "Preparing")
            }

            override fun onPrepared(player: BetterVideoPlayer) {
                Log.i(TAG, "Prepared")
            }

            override fun onBuffering(percent: Int) {
                Log.i(TAG, "Buffering $percent")
            }

            override fun onError(player: BetterVideoPlayer, e: Exception) {
                Log.i(TAG, "Error " +e.message)
            }

            override fun onCompletion(player: BetterVideoPlayer) {
                Log.i(TAG, "Completed")

                if(startEvent) {
                    mBetterVideoPlayer.reset()
                    mBetterVideoPlayer.setSource(Uri.parse("android.resource://" + packageName + "/" + eventVideoResource?.get((1..eventVideoResource?.size!!).shuffled().first()-1)))
                    mBetterVideoPlayer.setAutoPlay(true)
                    startEvent = false
                    eventPlaying = true
                }
                else if(eventPlaying)
                {
                    mBetterVideoPlayer.reset()
                    mBetterVideoPlayer.setSource(Uri.parse("android.resource://" + packageName + "/" + normalVideoResource?.get((1..normalVideoResource?.size!!).shuffled().first()-1)))
                    mBetterVideoPlayer.setAutoPlay(true)
                    mBetterVideoPlayer.setLoop(true)
                    eventPlaying = false

                }else
                {
                    mBetterVideoPlayer.reset()

                    mBetterVideoPlayer.setSource(Uri.parse("android.resource://" + packageName + "/" +normalVideoResource?.get((1..normalVideoResource?.size!!).shuffled().first()-1)))
                    mBetterVideoPlayer.setAutoPlay(true)
                    mBetterVideoPlayer.setLoop(true)
                }
                //bvp.setLoop(true)
            }

            override fun onToggleControls(player: BetterVideoPlayer, isShowing: Boolean) {

            }
        })

        mMessageListener = object : MessageListener() {

            override fun onFound(message: Message) {
                var t = Toast.makeText(this@FullscreenActivity,  "GOTEM: " + DeviceMessage.fromNearbyMessage(message).getMBody(), Toast.LENGTH_LONG)
                t. show()
                Log.i(TAG, "Message: "+DeviceMessage.fromNearbyMessage(message).getMBody())
                if(DeviceMessage.fromNearbyMessage(message).getMBody().equals(CAM1_START_MESSAGE) && sensorID == SENSOR_ID.CAM1){
                    Log.i(TAG,"Setting Event to TRUE")
                    startEvent = true
                }else if (DeviceMessage.fromNearbyMessage(message).getMBody().equals(CAM2_START_MESSAGE) && sensorID == SENSOR_ID.CAM2){
                    startEvent = true
                }else if (DeviceMessage.fromNearbyMessage(message).getMBody().equals(AUDIO_START_MESSAGE) && sensorID == SENSOR_ID.AUDIO){
                    startEvent = true
                }else if (DeviceMessage.fromNearbyMessage(message).getMBody().equals(RESET_MESSAGE) && sensorID == SENSOR_ID.CAM2){
                    reset = true
                }

                if(startEvent){
                    if(mGoogleApiClient != null && mGoogleApiClient!!.isConnected()) {
                        publish()
                    }
                }

                // Called when a new message is found.

                /* mNearbyDevicesArrayAdapter!!.add(
                         DeviceMessage.fromNearbyMessage(message).getMBody())

                 */
            }


            override fun onLost(message: Message) {
                // Called when a message is no longer detectable nearby.
                /*
                mNearbyDevicesArrayAdapter!!.remove(
                        DeviceMessage.fromNearbyMessage(message).getMBody())
                        *
                 */
            }
        }
    }

    override fun onPostCreate(savedInstanceState: Bundle?) {
        super.onPostCreate(savedInstanceState)

        // Trigger the initial hide() shortly after the activity has been
        // created, to briefly hint to the user that UI controls
        // are available.
        delayedHide(100)
    }

    private fun toggle() {
        if (mVisible) {
            hide()
        } else {
            show()
        }
    }

    private fun hide() {
        // Hide UI first
        val actionBar = supportActionBar
        actionBar?.hide()
        mVisible = false

        // Schedule a runnable to remove the status and navigation bar after a delay
        mHideHandler.removeCallbacks(mShowPart2Runnable)
        mHideHandler.postDelayed(mHidePart2Runnable, UI_ANIMATION_DELAY.toLong())
    }

    @SuppressLint("InlinedApi")
    private fun show() {
        // Show the system bar
        mBetterVideoPlayer.systemUiVisibility = View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
        mVisible = true

        // Schedule a runnable to display UI elements after a delay
        mHideHandler.removeCallbacks(mHidePart2Runnable)
        mHideHandler.postDelayed(mShowPart2Runnable, UI_ANIMATION_DELAY.toLong())
    }

    /**
     * Schedules a call to hide() in [delay] milliseconds, canceling any
     * previously scheduled calls.
     */
    private fun delayedHide(delayMillis: Int) {
        mHideHandler.removeCallbacks(mHideRunnable)
        mHideHandler.postDelayed(mHideRunnable, delayMillis.toLong())
    }

    companion object {
        /**
         * Whether or not the system UI should be auto-hidden after
         * [.AUTO_HIDE_DELAY_MILLIS] milliseconds.
         */
        private val AUTO_HIDE = true

        /**
         * If [.AUTO_HIDE] is set, the number of milliseconds to wait after
         * user interaction before hiding the system UI.
         */
        private val AUTO_HIDE_DELAY_MILLIS = 3000

        /**
         * Some older devices needs a small delay between UI widget updates
         * and a change of the status and navigation bar.
         */
        private val UI_ANIMATION_DELAY = 300

        public const val TAG = "FullScreenActivity"

        private val TTL_IN_SECONDS = 24 * 60 * 60 // One day.

        // Key used in writing to and reading from SharedPreferences.
        private val KEY_UUID = "key_uuid"

        /**
         * Sets the time in seconds for a published message or a subscription to live. Set to three
         * minutes in this sample.
         */
        private val PUB_SUB_STRATEGY = Strategy.Builder()
                .setTtlSeconds(TTL_IN_SECONDS).build()

        /**
         * Creates a UUID and saves it to [SharedPreferences]. The UUID is added to the published
         * message to avoid it being undelivered due to de-duplication. See [DeviceMessage] for
         * details.
         */
        private fun getUUID(sharedPreferences: SharedPreferences): String {
            var uuid = sharedPreferences.getString(KEY_UUID, "")
            if (TextUtils.isEmpty(uuid)) {
                uuid = UUID.randomUUID().toString()
                sharedPreferences.edit().putString(KEY_UUID, uuid).apply()
            }
            return uuid
        }

    }
    /**
     * Builds [GoogleApiClient], enabling automatic lifecycle management using
     * [GoogleApiClient.Builder.enableAutoManage]. I.e., GoogleApiClient connects in
     * [AppCompatActivity.onStart], or if onStart() has already happened, it connects
     * immediately, and disconnects automatically in [AppCompatActivity.onStop].
     */
    private fun buildGoogleApiClient() {
        if (mGoogleApiClient != null) {
            return
        }
        mGoogleApiClient = GoogleApiClient.Builder(this)
                .addApi(Nearby.MESSAGES_API)
                .addConnectionCallbacks(this)
                .enableAutoManage(this, this)
                .build()
    }

    public override fun onPause() {
        mBetterVideoPlayer.pause()
        super.onPause()
    }

    override fun onConnected(bundle: Bundle?) {

        Log.i(TAG, "GoogleApiClient connected")
        // We use the Switch buttons in the UI to track whether we were previously doing pub/sub (
        // switch buttons retain state on orientation change). Since the GoogleApiClient disconnects
        // when the activity is destroyed, foreground pubs/subs do not survive device rotation. Once
        // this activity is re-created and GoogleApiClient connects, we check the UI and pub/sub
        // again if necessary.
        /*
        if (mPublishSwitch!!.isChecked()) {
            publish()
        }*/

        subscribe()

    }
    override fun onConnectionFailed( connectionResult: ConnectionResult) {
        //mPublishSwitch!!.setEnabled(false)
        //mSubscribeSwitch!!.setEnabled(false)
        logAndShowSnackbar("Exception while connecting to Google Play services: " + connectionResult.getErrorMessage())
    }


    override fun onConnectionSuspended(i: Int) {
        logAndShowSnackbar("Connection suspended. Error code: $i")
    }

    /**
     * Logs a message and shows a [Snackbar] using `text`;
     *
     * @param text The text used in the Log message and the SnackBar.
     */
    private fun logAndShowSnackbar(text: String) {
        Log.w(TAG, text)
        /*
        val container = findViewById(R.id.activity_main_container)
        if (container != null) {
            Snackbar.make(container, text, Snackbar.LENGTH_LONG).show()
        }

         */
    }

    /**
     * Subscribes to messages from nearby devices and updates the UI if the subscription either
     * fails or TTLs.
     */
    private fun subscribe() {
        Log.i(TAG, "Subscribing")
        //mNearbyDevicesArrayAdapter!!.clear()
        val options = SubscribeOptions.Builder()
                .setStrategy(PUB_SUB_STRATEGY)
                .setCallback(object : SubscribeCallback() {

                    override fun onExpired() {
                        super.onExpired()
                        Log.i(TAG, "No longer subscribing")

                        /*
                        runOnUiThread(object : Runnable() {

                            override fun run() {
                                mSubscribeSwitch!!.setChecked(false)
                            }
                        })

                         */
                    }
                }).build()

        Nearby.Messages.subscribe(mGoogleApiClient, mMessageListener, options)
                .setResultCallback(object : ResultCallback<Status> {

                    override fun onResult( status: Status) {
                        if (status.isSuccess()) {
                            Log.i(TAG, "Subscribed successfully.")
                        } else {
                            logAndShowSnackbar("Could not subscribe, status = $status")
                            //mSubscribeSwitch!!.setChecked(false)
                        }
                    }
                })
    }

     enum class SENSOR_ID {
    CAM1,
    CAM2,
    AUDIO
    }

    /**
     * Stops subscribing to messages from nearby devices.
     */
    private fun unsubscribe() {
        Log.i(TAG, "Unsubscribing.")
        Nearby.Messages.unsubscribe(mGoogleApiClient, mMessageListener)
    }

    /**
     * Publishes a message to nearby devices and updates the UI if the publication either fails or
     * TTLs.
     */
    private fun publish() {

        when(sensorID){
            SENSOR_ID.CAM1 -> mPubMessage = DeviceMessage.newNearbyMessage(CAM1_FINISH_MESSAGE)
            SENSOR_ID.CAM2 -> mPubMessage = DeviceMessage.newNearbyMessage(CAM2_FINISH_MESSAGE)
            SENSOR_ID.AUDIO -> mPubMessage = DeviceMessage.newNearbyMessage(AUDIO_FINISH_MESSAGE)
        }

        Log.i(TAG, "Publishing: "+DeviceMessage.fromNearbyMessage(mPubMessage!!).getMBody())
        val options = PublishOptions.Builder()
                .setStrategy(PUB_SUB_STRATEGY)
                .setCallback(object : PublishCallback() {

                    override fun onExpired() {
                        super.onExpired()
                        Log.i(TAG, "No longer publishing")
                        /*
                        runOnUiThread(object : Runnable() {

                            override fun run() {
                                mPublishSwitch!!.setChecked(false)
                            }
                        })

                         */
                    }
                }).build()

        Nearby.Messages.publish(mGoogleApiClient, mPubMessage, options)
                .setResultCallback(object : ResultCallback<Status> {

                    override fun onResult( status: Status) {
                        if (status.isSuccess()) {
                            Log.i(TAG, "Published successfully.")
                        } else {
                            logAndShowSnackbar("Could not publish, status = $status")
                            //mPublishSwitch!!.setChecked(false)
                        }
                    }
                })
    }

    /**
     * Stops publishing message to nearby devices.
     */
    private fun unpublish() {
        Log.i(TAG, "Unpublishing.")
        Nearby.Messages.unpublish(mGoogleApiClient, mPubMessage)
    }







}

