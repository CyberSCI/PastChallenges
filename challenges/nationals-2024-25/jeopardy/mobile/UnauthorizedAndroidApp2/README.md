# Unauthorized App 2

**Author:** Ch0ufleur

**Category:** Mobile

## Description

The challenge is about intercepting communications with Flutter.
Based on Dart, Flutter ignore the system proxy on Android.
Players must find an alternative solution that involves reversing a Rust binary to obtain the domain used for communication. They also must manipulate an Android Emulator to a rooted state and make specific changes to upload their own certificate.

### Files

ARM64 build APK file

X86_64 build APK file

### Host

N/A

## Part 1 


**CTFd name:** Unauthorized App 2

### CTFd Description

* The story follows Unauthorized App 1, but the challenge infrastructure is separated - don't assume communications are identical.
* __Fuzzing remote services you may find is prohibited for this challenge__.

---

Regarding that Android Application...

We are wondering if you'd be able to analyze its communications? Since it's a copy of ours, and not an official app, we would like to know if it leaks any kind of information to malicious third parties...

We are specifically wondering, what happens under the hood when a citizen sends a vote?

By the way, it seems it was made with Flutter! Although, that might not be the only interesting binary in there.

Here is some information about our head IT specialist, Jeanine Lopez, that you can use to login and validate within the app. Although, we already validated her account for you.

user: `jeanine_lopez`

password:`password`

date of birth:`2000`

social insurance:`TT1214512131`

postal code:`AUT2111`

---

* Flag format starts with FLAG-

---

#### CTFD Hint (0 points)
It is strongly suggested to research which Android version is best to install and analyze the .apk.
This challenge was tested with an emulator running Android API 30.

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>


FLAG-41237469ca5b5c4c2

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The following describes a way to solve the challenge.
There might be other ways, like using instrumentation or completely reversing the flutter code and the rust code. That said, reFlutter is less and less compatible with recent implementations, so that might be very hard.

Very useful links to understand better the differents steps are below.

[Adding Certs to trust store with rooted phone](https://docs.mitmproxy.org/stable/howto/install-system-trusted-ca-android/)

[Flutter and Dart issue for App proxying](https://github.com/flutter/flutter/issues/26359)

[mkcert tool](https://github.com/FiloSottile/mkcert)

1. Players must configure an Android Environment where they have root and console access. I did it by using Android Studio's emulator with a Default Android System Image of Android API30. It's important not to select an image with Google APIs enabled, because that could prevent the player from having easy root access. Furthermore, the latest API versions (31-36) might not work later in the challenge. All in all, this challenge's difficulty lies in the know-how needed to properly setup the environment amongst other things.
2. The application is made with Flutter. According to an active issue, Flutter will always bypass the Android system proxy because of a Dart limitation. This means that classic interception techniques will not work (i.e. using Burp Suite's proxy and certificate and then configuring a manual proxy in Android so that the App communicates to Burp Suite and request can be seen). We have to find a way around that.
3. Since we have root access to the Android Emulator, we can use `emulator` commands to disable secure boot verifications and allow for remounting (with `adb`) read-only partitions where trusted CA certificates are stored. Throughout the challenge, it is important that the emulator is always started via the command line utility `emulator` and the `-writable-system` flag, otherwise filesystem modifications will not be considered. This is explained in the mitm proxy doc in reference above.
4. We will have to "reverse engineer" the Rust library `lib_ssl_internal` that is packaged inside the APK to find the domain the app communicates with. It is fairly easy with "strings" to get most of the domain (archives.valverd), and players that have solved Unauthorized App 1 can deduce the rest of the domain. That is, "archives.valverde.vote". Players could also try and load the binary in Ghidra to dive deeper in the code, but I made it convoluted with pointless parameters to increase such difficulty because I wanted to point the players through the dynamic analysis angle, the goal not being the challenge to be a RE one.
5. Once that is done, we can use a tool like `mkcert` to create a custom CA and create a custom certificate for archives.valverde.vote, signed by our own CA.
6. Since we have root access to the emulator, we can also remount the partition (This is explained in the mitm proxy doc in reference above) so we can write to `/etc/hosts` and point archives.valverde.vote to 10.0.2.2, which is Android Studio's Emulator way of reaching localhost on the host device (as per the official documentation).
7. The app will then DNS resolve to our localhost on port 443. For it to trust the certificate, we have to add it to the trusted ca-certs store with `adb push` and rename it according to an hash derived from a specific openssl command (This is explained in the mitm proxy doc in reference above).
8. The only thing missing is a small python server that players can code with ChatGPT so that it uses the custom certificate for archives.valverde.vote, logs the content of the requests, and listens on localhost:443. Administrator privileges might be needed to listen on that port depending on the host OS.
9. The challenge description hints that we want to know what happens when someone votes, so either the players have made their Python server a middle-man with the real server and can see the response containing the Flag from there, or they intercepted the original POST request and replayed it with Postman or Insomnia to obtain the flag, because that flag is in the response to the /votar request.
10. A rust function is used to provide a specific token that must appear in the POST request for it to have the flag in the response. The way I planned this challenge to be solved, it's not necessary to reverse engineer that function, since the token is visible in plain text in the intercepted request content.

</details>


## Setup instructions

The server_files can be used with the Dockerfile provided to rebuild an image and redeploy.

However, this is externally hosted. A SSH key-based access could be provided to restart the container during the competition. [REDACTED]
