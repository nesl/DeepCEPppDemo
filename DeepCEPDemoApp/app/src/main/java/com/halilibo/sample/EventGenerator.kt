package com.halilibo.sample

import android.content.SharedPreferences
import android.os.Bundle
import com.google.android.material.snackbar.Snackbar
import android.text.TextUtils
import android.util.Log
import android.view.View
import android.widget.Toast
import androidx.fragment.app.FragmentActivity
import com.google.android.gms.common.ConnectionResult
import com.google.android.gms.common.api.GoogleApiClient
import com.google.android.gms.common.api.ResultCallback
import com.google.android.gms.common.api.Status
import com.google.android.gms.nearby.Nearby
import com.google.android.gms.nearby.messages.*
import com.google.android.gms.nearby.messages.samples.nearbydevices.DeviceMessage

import java.util.*

class EventGenerator : FragmentActivity(), GoogleApiClient.ConnectionCallbacks, GoogleApiClient.OnConnectionFailedListener  {

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

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_event_generator)
        findViewById<View>(R.id.cam1_convoy_button).setOnClickListener {

            // If GoogleApiClient is connected, perform sub actions in response to user action.
            // If it isn't connected, do nothing, and perform sub actions when it connects (see
            // onConnected()).
            Log.i(TAG, "Attempting to publish cam1")
            if (mGoogleApiClient != null && mGoogleApiClient!!.isConnected()) {
                    publish(CAM1_START_MESSAGE)

            }else{
                if(mGoogleApiClient == null) {
                    Log.i(TAG, "Client was null")
                }else{
                    Log.i(TAG, "Client wasn't connected")
                }
            }

        }
        findViewById<View>(R.id.cam2_convoy_button).setOnClickListener {

            // If GoogleApiClient is connected, perform sub actions in response to user action.
            // If it isn't connected, do nothing, and perform sub actions when it connects (see
            // onConnected()).
            Log.i(TAG, "Attempting to publish cam1")
            if (mGoogleApiClient != null && mGoogleApiClient!!.isConnected()) {
                publish(CAM2_START_MESSAGE)

            }else{
                if(mGoogleApiClient == null) {
                    Log.i(TAG, "Client was null")
                }else{
                    Log.i(TAG, "Client wasn't connected")
                }
            }

        }
        findViewById<View>(R.id.audio_gunshot_button).setOnClickListener {

            // If GoogleApiClient is connected, perform sub actions in response to user action.
            // If it isn't connected, do nothing, and perform sub actions when it connects (see
            // onConnected()).
            Log.i(TAG, "Attempting to publish cam1")
            if (mGoogleApiClient != null && mGoogleApiClient!!.isConnected()) {
                publish(AUDIO_START_MESSAGE)

            }else{
                if(mGoogleApiClient == null) {
                    Log.i(TAG, "Client was null")
                }else{
                    Log.i(TAG, "Client wasn't connected")
                }
            }

        }


        mMessageListener = object : MessageListener() {

            override fun onFound(message: Message) {
                var t = Toast.makeText(this@EventGenerator, "GOTEM: " + DeviceMessage.fromNearbyMessage(message).getMBody(), Toast.LENGTH_LONG)
                t.show()

                if(DeviceMessage.fromNearbyMessage(message).getMBody().equals(CAM1_FINISH_MESSAGE) || DeviceMessage.fromNearbyMessage(message).getMBody().equals(CAM2_FINISH_MESSAGE) || DeviceMessage.fromNearbyMessage(message).getMBody().equals(AUDIO_FINISH_MESSAGE)){
                    Log.i(FullscreenActivity.TAG,"Got finish message")
                    unpublish()
                }
                // Called when a new message is found.

                /* mNearbyDevicesArrayAdapter!!.add(
                         DeviceMessage.fromNearbyMessage(message).getMBody())

                 */
            }
        }
        buildGoogleApiClient()


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

    /**
     * @TODO: also make this a shared class; it's copy and pasted elsewhere
     */
    enum class SENSOR_ID {
        CAM1,
        CAM2,
        AUDIO
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
    private fun publish(messageString: String) {
        mPubMessage = DeviceMessage.newNearbyMessage(messageString)
        Log.i(TAG, "Publishing: "+ DeviceMessage.fromNearbyMessage(mPubMessage!!).getMBody())
        val options = PublishOptions.Builder()
                .setStrategy(PUB_SUB_STRATEGY)
                .setCallback(object : PublishCallback() {

                    override fun onExpired() {
                        super.onExpired()
                        Log.i(TAG, "No longer publishing")
                    }
                }).build()

        Nearby.Messages.publish(mGoogleApiClient, mPubMessage, options)
                .setResultCallback(object : ResultCallback<Status> {

                    override fun onResult( status: Status) {
                        if (status.isSuccess()) {
                            Log.i(TAG, "Published successfully.")
                        } else {
                            logAndShowSnackbar("Could not publish, status = $status")
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

        public const val TAG = "EventGenerator"

        private val TTL_IN_SECONDS = 3 * 60 // Three minutes.

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


    override fun onConnected(bundle: Bundle?) {

        Log.i(TAG, "GoogleApiClient connected")
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
    }

}
