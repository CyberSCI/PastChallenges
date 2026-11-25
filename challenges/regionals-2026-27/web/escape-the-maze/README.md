# Escape the Maze

**Author:** larry/@ehhthing

**Category:** Web

## Description

Escape the maze!

### Files

None.

### Host

_TBD_

## Part 1

**CTFd name:** Escape the Maze

### CTFd Description

They came. They saw. They gnawed. Find your way out before you're dammed.

NOTE: The maze is of reasonable size.

### Depends on

None.

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{j_what_cc5833}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

JWTs are used to keep state, but since the server is stateless, you can basically "rewind time" by using older JWT tokens. 

When you "die" in the game, your old JWT tokens are still valid meaning you can "try again" from your previous locations.

By storing a list of JWT tokens that have been seen, you can do an exhaustive graph search on the maze using breadth-first-search or depth-first-search to solve the maze.

</details>

## Setup instructions

Copy the `server_files` to the server, install docker `curl https://get.docker.com | sh` and then run `docker compose up --build`.