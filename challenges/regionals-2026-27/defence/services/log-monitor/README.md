# Log Monitor

**Author:** Dmitriy Beryoza (0xd13a)

**Category:** Defence

## Description

This is a vulnerable ELK stack setup that is configured in a way that it accepts 3 different ways to send incorrect and malicious log records. 

The system is deisiged to track timber logging records by different beaver lumberjacks.

Attacker sends some records are incorrect (all zeros) to sabotage timber production records, and other records that contain OS command injection exploits.

### Host

`10.0.2.22`

## Part 1

**CTFd name:** Log Monitor 1

### CTFd Description

An elk contractor built a timber tracking system for the beaver community and logging crews are hard at work, cutting down trees and keeping track of their progress. 

Recently SOC admins started noticing weird activity in the system, unknown attackers were exploiting it in an attempt to derail timber production. And now we need your help to figure out the weaknesses and fix them.

Use the Attack Portal at http://10.0.2.20 to launch exploits we have observed so far.

Track timber records in a dashboard at http://10.0.2.22:5601/app/canvas#/workpad/log-of-logs/page/1

The tracking system is hosted on `10.0.2.22`. SSH in with credentials `vpcadmin/vpcadmin`.

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{do_not_quote_Dissect_on_this}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This vulnerability is enabled by a deficiency in Dissect parser that does not handle CSV fields with double quotes correctly. As a result a malicious lumberjack can inject additional CSV fields when they specify their name. As a result, records can be added that have zeros in them.

One of the ways to address  this is to make the following fixes in `pipeline.conf`:

```diff
filter {
  if [type] == "csv_dissect" {
-    dissect {
-      mapping => {
-        "message" => "%{batchid},%{timestamp},%{lastname},%{firstname},%{loglength},%{logdiameter},%{numberoflogs},%{volume},%{timbertype}"
-      }
-      convert_datatype => {
-        "loglength" => "int"
-        "logdiameter" => "int"
-        "numberoflogs" => "int"
-        "volume" => "int"
-      }
-      tag_on_failure => ["_dissectfailure"]
+    ruby {
+      init => 'require "csv"'
+
+      code => '
+        begin
+          if event.get("message").to_s.include?(",0,")
+            event.cancel
+          else
+            row = CSV.parse_line(event.get("message").to_s)
+
+            if row.nil? || row.length != 9
+              event.cancel
+            else
+              event.set("batchid", row[0])
+              event.set("timestamp", row[1])
+              event.set("lastname", row[2])
+              event.set("firstname", row[3])
+              event.set("loglength", row[4].to_i)
+              event.set("logdiameter", row[5].to_i)
+              event.set("numberoflogs", row[6].to_i)
+              event.set("volume", row[7].to_i)
+              event.set("timbertype", row[8])
+            end
+          end
+        rescue CSV::MalformedCSVError, ArgumentError, TypeError
+          event.cancel
+        end
+      '
    }
```

</details>

## Part 2

**CTFd name:** Log Monitor 2

### CTFd Description

An elk contractor built a timber tracking system for the beaver community and logging crews are hard at work, cutting down trees and keeping track of their progress. 

Recently SOC admins started noticing weird activity in the system, unknown attackers were exploiting it in an attempt to derail timber production. And now we need your help to figure out the weaknesses and fix them.

Use the Attack Portal at http://10.0.2.20 to launch exploits we have observed so far.

Track timber records in a dashboard at http://10.0.2.22:5601/app/canvas#/workpad/log-of-logs/page/1

The tracking system is hosted on `10.0.2.22`. SSH in with credentials `vpcadmin/vpcadmin`.

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{a_log_for_a_shell_is_not_a_fair_trade}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This vulnerability is enabled by Log4Shell in this version of Java and the ELK stack. Upgrade software versions to get rid of them:

In `compose.yaml` change:

```diff
-        ELASTIC_VERSION: 7.0.0
+        ELASTIC_VERSION: 7.17.29        
```

In `Dockerfile` change:

```diff
-ARG ELASTIC_VERSION=7.0.0
+ARG ELASTIC_VERSION=7.17.29
...
-    && curl -fLsS --retry 3 -o openjdk.tar.gz "https://download.java.net/java/GA/jdk11/13/GPL/openjdk-11.0.1_linux-x64_bin.tar.gz" \
-    && tar -xzf openjdk.tar.gz -C /opt/jdk --strip-components=1 \
    && for component in elasticsearch logstash kibana; do \
         case "$component" in \
-           logstash) archive="logstash-${ELASTIC_VERSION}.tar.gz" ;; \
+           logstash) archive="logstash-${ELASTIC_VERSION}-linux-x86_64.tar.gz" ;; \
```

</details>

## Part 3

**CTFd name:** Log Monitor 3

### CTFd Description

An elk contractor built a timber tracking system for the beaver community and logging crews are hard at work, cutting down trees and keeping track of their progress. 

Recently SOC admins started noticing weird activity in the system, unknown attackers were exploiting it in an attempt to derail timber production. And now we need your help to figure out the weaknesses and fix them.

Use the Attack Portal at http://10.0.2.20 to launch exploits we have observed so far.

Track timber records in a dashboard at http://10.0.2.22:5601/app/canvas#/workpad/log-of-logs/page/1

The tracking system is hosted on `10.0.2.22`. SSH in with credentials `vpcadmin/vpcadmin`.

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{a_pearl_in_a_shell_is_better_than_a_shell_in_Ruby}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

This vulnerability ie enabled by an OS command injection in the Ruby code. Make changes similar to the following in `csv_parser.rb` to remove it:

```diff
require 'csv'
+require 'digest'

def filter(event)
  hash, value = event.get("message").split(",", 2)

-  output = IO.popen("echo -n " + value + " | sha256sum", "r+") do |pipe|
-    pipe.read
-  end
-
-  calculated_hash = output.split.first
+  calculated_hash = Digest::SHA256.hexdigest(value)

-  if calculated_hash != hash.downcase
+  if calculated_hash != hash.downcase || value.count("|$<>&;`") > 0
    event.tag('_csvparsefailure')
    return [event]
  end
```

</details>


## Setup instructions

### On the build machine

* Pack up the files for the container 

```
tar zcf log-monitor.tar.gz Dockerfile compose.yaml canvas-workpad.json config/* logstash/* start.sh
```

* Copy the package to the host machine:

```
scp ./log-monitor.tar.gz vpcadmin@10.0.2.22:~
```

### On the host machine

* Disable shell history by adding command `export HISTSIZE=0` to `~/.bashrc`

* Install Docker:

```
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.dir/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
docker --version
docker compose version
sudo docker run hello-world
```

* Unpack the files

```
tar xzf log-monitor.tar.gz
```

* Run the container

```
sudo docker compose up -d
```

* Set the password for user `vpcadmin` to be also `vpcadmin`:

```
sudo passwd vpcadmin
```

* Enable password authentication by creating file `/etc/ssh/sshd_config.d/10-password-login-for-special-user.conf` with the following content:

```
Match User vpcadmin
    PasswordAuthentication yes
```

* Reboot the machine to make sure container will still run

