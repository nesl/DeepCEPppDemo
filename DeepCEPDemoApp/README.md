## DeepCEP++ Demo Android App

This app is an Android implementation of the [Better Video Player App](https://github.com/halilozercan/BetterVideoPlayer). You visit the project's homepage for any dependencies. The minimum API level is 23 due to the usage of certain MediaPlayer API references.

The app is intended to be deployed as part of the DeepCEP++ demo at the DAIS AFM 2019. Currently, it is intended to work with 4 separate Android tablets:
* 2 tablets will be setup as a "security" cameras 1 and 2 to be used for monitoring 2 areas of a "city"
* 1 tablet (can also be a phone) will be setup as just playing audio recordings
* 1 tablet (can also be a phone) will be used as an event generator that can generate events in the other 3 tablets

The tablets communicate with each other over an [Android Nearby API pub/sub](https://developers.google.com/nearby/messages/android/pub-sub). The events generated are as follows:
* Cam1: a convoy of red trucks will pass through the area
* Cam2: a convoy of red trucks will pass through the area
* Audio: a gunshot will be played

These events will be detected by the separate DeepCEP demo components as simple events to compose a complex event with a particular confidence/uncertainty.
