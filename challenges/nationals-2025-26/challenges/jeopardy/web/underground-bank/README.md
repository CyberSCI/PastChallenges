# underground-bank

**Author:** larry

**Category:** Web

## Description

The crypto bros never died out! They're now part of the secret society and are operating some kind of shadow banking infrastructure.

### Files

[](./release_files/underground-bank.zip)

## Part 1

**CTFd name:** underground-bank-1

### CTFd Description

> The crypto bros never died out! They're now part of the secret society and are operating some kind of shadow banking infrastructure. 
> 
> There's an admin account, but the password seems to be secure. See if you can hack it anyway.
> 
> File: [underground-bank.zip](attachment)
> Server: [http://{ip}:8080](http://{ip}:8080)

### Depends on

None

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{what_ev3n_is_a_graph_query_language}`

</details>

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>
We start by doing a GraphQL injection on the `/login` endpoint, since the GraphQL query is templated using basic string interpolation.

Specifically our payload is `username=admin` `password=x") { login: __typename u: #`, creating the following query:

```graphql
query Login($username: String! = "admin", $password: String! = "x") {login: __typename u: #") {
    login(username: $username, password: $password)
}
```

GraphQL interprets it as:

```graphql
query Login($username: String! = "admin", $password: String! = "x") {
	login: __typename 
	u: login(username: $username, password: $password)
}
```

Since the comment removes the extra `") {`, and all whitespace is considered equal.

By aliasing the real `login` call as `u:`, the `login` property in the query response will instead be the value of `__typename`, this tricks Python because `__typename` is considered a truthy since it's a non-empty string.

We get the admin token back and can decode it for the first flag.
</details>

## Part 2

**CTFd name:** underground-bank-2

### CTFd Description

> Now we need to destabilize their financial system, see if you can get really, really rich!
>
> File: [underground-bank.zip](attachment)

### Depends on

None

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{json_is_such_a_l33t_format}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The second part abuses an interesting property of JSON serialization / deserialization, which is that it isn't idempotent. This means that there are cases where `JSON.stringify(JSON.parse(x)) != x`. The specific case we're abusing is `JSON.stringify(JSON.parse("9".repeat(999)))`, which after being parsed results in `Infinity` but after stringfying results in `null`.

Since every transaction has a fee stored with the tx request, we can submit a transaction with amount = Infinity, but when it's saved in JSON it ends up at `null`. However since the transaction fee maxes out at `100`, we get a transaction where the amount coerces in to `0` but the fee is `100`. We also note that the check for whether someone has enough money for a transaction only checks if they have enough money for the amount being transferred, but it allows overdraft if they don't have enough to cover transaction + fee. 

This effectively allows the admin to give themselves unlimited money since they can create new accounts and submit `Infinity` transactions where new account requests money from themselves. By accepting the self-transfer, `100` is transferred to the admin's account.

The only thing we don't have now is a way to trigger a re-read of the ledger, since we can only get `Infinity = null = 0` if we can trigger a `JSON.parse` of the ledger again. The last piece of the puzzle is in the webhook system, where `triggerWebhook` is an `async` function with a `await fetch`, however it is called in the GraphQL mutation handler without any corresponding `await` call. In the modern V8 JS engine (which Deno and Node.js use), this causes an unhandled exception, crashing the program and forcing it to restart (docker-compose is configured to restart `unless-stopped`). This forces a re-read of the ledger, transforming our `Infinity` transactions into `null` and thus `0` transactions.

So in summary:
1. Create 14 accounts.
2. On each of the accounts, request 1e999 money from yourself.
3. Crash and restart the server by causing a Webhook exception.
4. Accept each of the 14 requests on each account.
5. Login as admin using the bug in Flag 1.
6. Request the flag using the same GraphQL injection bug.

</details>

## Setup instructions

1. Run `docker compose up` to start the service.
2. Verify: Run exploit.py in the solve_files to ensure that the service is working
3. Upload `underground-bank.tar.gz` as a CTFd attachment. Make sure port 8080 is open on the server.