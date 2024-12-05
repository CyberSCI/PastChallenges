--[ Description

We are collecting polling data for the upcoming election.

Connect to the polling station with:

  nc 10.0.2.32 1337

The server will respond to a port for client connections. Clients can
connect to the same IP on this port. Polling data will be received at the
polling station.

--[ Setup

Players should be provided the following files:

- hosted/challenge.sh
- hosted/Dockerfile
- hosted/polling_station
- hosted/xinetd.conf
