# *Unauthorized App 1*

**Author:** *Ch0ufleur*

**Category:** *Mobile*

## Description

Static analysis of an IPA archive to find a leaked API url within Info.plist. That API has documentation that contains a leaked API_DEV_TOKEN.

### Files

The .ipa archive.

### Host

N/A

## Part 1 

**CTFd name:** Unauthorized App 1

### CTFd Description

We've been developing this beta version of a iOS voting mobile application.
We did not have time to test it sufficiently before this year's elections, but we did send it to a group of beta testers.

What is now concerning is that many online ads are advertising an "Official Android voting app" for the elections... We tested it, it offers all the same features, but it's not legit!

Could you statically analyze this development archive of our iOS app and follow any hints you may find as to how they could have gotten the detail of our fastapi beta server API?

---

* The flag is the API development token

* Trying to install this .ipa is pointless. No Apple device needed.

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>


gGBCZ2UmgQru0xd0Xe1Xp2eve

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

1. Rename the .ipa to .zip
2. Find the .app package within the archive
3. iOS app often leak information from their Info.plist files, which contains lots of data. It is, in some way, analogous to the Android Manifest for Android Apps. This is were players will find the API server url.
4. The description says the server is Fastapi. Looking for /docs, players will find the token in the Swagger API description. That token is the flag.

</details>


## Setup instructions

The server_files can be used with the Dockerfile provided to rebuild an image and redeploy.

However, this is externally hosted. A SSH key-based access could be provided to restart the container during the competition. [Redacted]
