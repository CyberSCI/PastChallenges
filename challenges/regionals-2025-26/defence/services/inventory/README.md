# Inventory

**Author:** Dmitriy Beryoza (0xd13a)

**Category:** Defence

## Description

This is a vulnerable Inventory application written in BASIC, that can run on any old machine with a BASIC interpreter. It is meant to handle distribution of supplies to the public during disaster recovery. 

New users can login at a terminal and browse available supplies, print out the items they need and take the receipt to the cashier. Administrators also can log in with a secret password and distribute dangerous supplies such as guns and ammunition.

### Host

`nc 10.0.2.22 10001`

## Part 1

**CTFd name:** Inventory 1

### CTFd Description

As we are piecing our lives back together we have set up an Inventory system for distributing emergency supplies. Unfortunately some individuals started abusing it to try and get access to restricted goods. Please help us test and secure this application.

Use the Attack Portal at http://10.0.2.21 to launch exploits we have observed so far.

The Inventory application is hosted on `10.0.2.22`. SSH in with credentials `vpcadmin/vpcadmin`.

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{eval_even_sounds_like_evil}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

There is an `EVAL$()` function in the code that can be used maliciously to leak private information, like an admin password:

```diff
-     LET PROMPT$ = EVAL$("\""+USERNAME$+"> \"")
+     REM Fix: We do not want to use an EVAL$() function, it is dangerous
+     LET PROMPT$ = USERNAME$ + "> "
```

</details>

## Part 2

**CTFd name:** Inventory 2

### CTFd Description

As we are piecing our lives back together we have set up an Inventory system for distributing emergency supplies. Unfortunately some individuals started abusing it to try and get access to restricted goods. Please help us test and secure this application.

Use the Attack Portal at http://10.0.2.21 to launch exploits we have observed so far.

The Inventory application is hosted on `10.0.2.22`. SSH in with credentials `vpcadmin/vpcadmin`.

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{variable_shadowing_spoiled_us}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

`MODE` variable is used in two places in the code: to specify the type of logged in user (regular vs. admin) and to specify the direction in which to scroll the inventory list (forwad vs. back). The problem is that in BASIC when you are creating a local variable it will point to a global variable with the same name (if one exists). As a  result, by scrolling backward through the inventory, the current user type is changed into "adminsitrator":  

```diff
' Process browsing of the inventory
SUB PROCESS_INVENTORY(NAMES$(), PRICES(), AMOUNTS(), PREFIX$)

+     REM Fix: We should either rename the MODE variable or declare it local
+     LOCAL MODE
+
    LET MOVE = false
    LET START = 0
```

</details>

## Part 3

**CTFd name:** Inventory 3

### CTFd Description

As we are piecing our lives back together we have set up an Inventory system for distributing emergency supplies. Unfortunately some individuals started abusing it to try and get access to restricted goods. Please help us test and secure this application.

Use the Attack Portal at http://10.0.2.21 to launch exploits we have observed so far.

The Inventory application is hosted on `10.0.2.22`. SSH in with credentials `vpcadmin/vpcadmin`.

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{guns_for_everyone!}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

There are no checks for the type of item that can be ordered. As a result, a regular user can order a restricted item if they know its ID:

```diff
' Process inventory item selection
SUB PROCESS_ITEM(ID$)
    LET ERROR_MSG$ = "*** Incorrect item ID!"

    LET ITEM$ = TRIM$(ID$)
    IF LEN(ITEM$) < 1 THEN
        PRINT ERROR_MSG$
        RETURN
    END IF

    LET ADMIN = false
    IF UPPER$(MID$(ITEM$,1,1)) = "R" THEN
        ADMIN = true
        ITEM$ = MID$(ITEM$,2)
    END IF

+     REM Fix: if you are not and administrator and a restricted item is selected - return an error
+     IF MODE <> 0 AND ADMIN THEN
+         PRINT "*** You have to be an administrator to request a restricted item!"
+         RETURN
+     END IF
```

</details>


## Setup instructions

### On the build machine

* Pack up the files for the container 

```
tar zcf inventory.tar.gz Dockerfile docker-compose.yaml inventory.bas regular_inventory.csv restricted_inventory.csv
```

* Copy the package to the host machine:

```
scp ./inventory.tar.gz vpcadmin@10.0.2.22:~
```

### On the host machine

* Install Docker:

```
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-compose
```

* Unpack the files

```
tar xzf inventory.tar.gz
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

