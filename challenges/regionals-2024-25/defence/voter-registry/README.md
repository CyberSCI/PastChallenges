# Voter Registry Challenge

## Description

This is a vulnerable Voter Registry website written in Python. Voters can log in and make sure their information is correct, and update their mailing addresses. Administrators can see and edit everyone's information, and register new voters.

## CTFd Descriptions

Central Electoral Commission hosts a Voter Registration website that they asked us to test. The attacks that we tried have yielded a number of vulnerabilities that you need to help us fix. 

Please use the Attack Portal at http://10.0.2.50 to launch attacks.

Voter Registration website is hosted at https://10.0.2.52

## Flags

<details>
<summary>Attack 1</summary>

> **Flag:** `MDkBkW8S`

</details>

<details>
<summary>Attack 2</summary>

> **Flag:** `pP6IihKm`

</details>

<details>
<summary>Attack 3</summary>

> **Flag:** `VdoIRKRP`

</details>

## Vulnerabilities

There are 3 vulnerabilities in this application:

- Currently the signature verification is primitive and does not reject anything but the simple forgeries:

```diff
-    # This is a good enough verification for now
-    if len(signature) != 64:
-        return None
+    # Fix: verify signature on the badge
+    key = ECC.import_key(open("public_ed25519.pem").read())
+    verifier = eddsa.new(key, 'rfc8032')
+    try:
+        verifier.verify(payload["id"].encode(), signature)
+    except ValueError:
+        return None
```

- Signature verification on the JWT token is accidentally made optional, which allows attacker to submit forgeries and impersonate administrators. 

```diff
...
- sig_verify = True
...
-            decoded_data = jwt.decode(jwt=token, key=jwt_key, algorithms=["HS256"], options={"verify_signature": sig_verify})
+            # Fix: do not make verification optional
+            decoded_data = jwt.decode(jwt=token, key=jwt_key, algorithms=["HS256"], options={"verify_signature": True})
...
-def init():
-    """ Init globals """
-    global voters, admins, sig_verify
-    voters = {}
-    admins = {}
-    sig_verify = None
...
-    init()
```

- Currently any voter can see any other voter's record. Additional check must be implemented to only allow voters to see their own records (admins must be able to see everything)

```diff
@app.route("/voter/<id>", methods=['GET', 'POST'])
def voter(id):
    """ Display voter record and make allow voter to make changes. Only the admin and voter themselves are alowed to do this.  """
    user = get_user(request)
    if user == None:
        return redirect("/")
    
+    # Fix: make sure only the voter can edit their own record, or an admin
+    if not user.is_admin() and user.get_id() != id:
+        return redirect("/")
```

## Setup

### On the build machine

* Pack up the files for the container 

```
tar zcf voter-registry.tar.gz Dockerfile docker-compose.yaml voter_registry.py add_template.html admin_template.html login_template.html voter_template.html voter-list.db private_ed25519.pem public_ed25519.pem static/*
```

* Copy the package to the host machine:

```
scp ./voter-registry.tar.gz cfp:~
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
tar xzf voter-registry.tar.gz
```

* Run the container

```
sudo docker compose up -d
```

* Reboot the machine to make sure container will still run
