# Local rehearsal (test flags only)

Performed on 2026-10-27 using WSL Docker Engine 28.5.2 and Compose 2.40.3.
This is a local container check, not the assigned competition VM or HTTPS proxy.

- One Compose service built and reported healthy. The host binding was `127.0.0.1:18027->8000/tcp`; `ss` showed only a loopback listener. `docker compose top` showed one non-root Uvicorn worker under `docker-init`.
- `/healthz` returned `{"status":"ok"}`. Starting the image without flags exited with `DAMWATCH_FLAG_1 is required`.
- The image file list contained only the four application modules, pinned runtime requirements, and HTML/CSS/JS assets. It did not contain tests, the solver, a runtime env file, or source maps.
- From a separate Windows client, the reference solver completed all three parts in **10 of 10 fresh sessions** with two parallel redemption requests per attempt. Each run took 0.84–1.38 seconds. A later container restart was followed by another successful three-part solve.
- The Python suite passed **45 tests**. Ruff check and format check, plus JavaScript syntax check, passed.

The first ten-run attempt failed with connection refusals because WSL's Docker listener was not held open for the Windows client between shell calls. Keeping a WSL log-follow session active made the listener reachable; the repeated 10/10 run above measures the challenge while the service was available. This does not substitute for the assigned VM reliability test.

**Pending on the organizer's VM:** final HTTPS/WSS proxy and cookie check; Burp and Wireshark traffic review; ten remote fresh-session solves and Burp parallel-send check; two-browser isolation; capacity measurements; full VM reboot recovery; CTFd configuration/submissions; independent human playtest. Actual flag values, flag format, URL, points, and the final repository destination also await organizer confirmation.
