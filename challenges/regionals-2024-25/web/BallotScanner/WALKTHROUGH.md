# Ballot-Scanner Challenge Walkthrough

## Challenge 1: Test Ballot

This challenge is fairly introductory: It is solvable merely by screenshotting the provided PDF sample ballot barcode and submitting that as a ballot image. 

Doing so will return text to the user like:

```
TEST BALLOT FUNCTIONING AND SCANNED.
PRECINCT CODE: 65916
THIS TEST BALLOT VOTED FOR: [NO VOTE DETECTED]
FLAG: TESTING-<a flag string here>
```


**Title**: Cover the basics.

**Description**

> We need to make sure this machine is working properly.
> 
> Flag: **TESTING-???**



## Challenge 2: Ballot Count

The next step uses an administrative barcode function (code 000002) to retrieve the total number of scanned ballots, and returns a signature code. Submitting a barcode formatting like PRECINCT-000002, (65916-000002) will return the flag to the user:

```
CURRENT NUMBER OF CAST BALLOTS: 435
SIGNATURE CODE: BALLOTCOUNT-<a flag string here>
```

**Title**: Ballot counts

**Description**

> Now let's validate the count of ballots.
> 
> Flag: **BALLOTCOUNT-???**


## Challenge 3: Diagnostics

The final step is to take the barcode generation in step 2 and fuzz the codes. Code 99 is an administrative code, which will forward the user to the secret administrative endpoint.

This page features a **Ballot machine ID** serial number, which is the flag.

**Title**: Diagnostics

**Description**

> Find out what other diagnostics you have access to.
> 
> Flag: The Ballot machine ID.

