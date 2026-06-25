# Jenkins Client Composition Refactor

**File**: `server_files/attacker/attacker.py`

## Goal

Extract Jenkins-interfacing methods from `Client` into `JenkinsClient` ABC, implement in `JenkinsHttpClient` (using python-jenkins lib) and `JenkinsSshClient` (stubs). `Client` uses composition to delegate.

## Steps

### 1. Expand `JenkinsClient` ABC

Replace existing `JenkinsClient` (lines 79-85) with full abstract interface:

```python
class JenkinsClient(ABC):
    @abstractmethod
    def login(self, username: str | None = None, password: str | None = None) -> bool:
        pass

    @abstractmethod
    def list_jobs(self) -> list | None:
        pass

    @abstractmethod
    def get_job_config(self, name: str) -> str | None:
        pass

    @abstractmethod
    def get_queue_item(self, queue_id: int) -> dict | None:
        pass

    @abstractmethod
    def get_build_info(self, name: str, build_number: int) -> dict | None:
        pass

    @abstractmethod
    def trigger_build(
        self,
        name: str,
        parameters: Mapping[str, Incomplete] | Sequence[tuple[str, Incomplete]] | None,
    ) -> int | None:
        pass

    @abstractmethod
    def create_pipeline(self, name: str, groovy_script: str) -> None:
        pass
```

Remove `creds` field — not all clients need stored creds at this level.

### 2. Implement `JenkinsHttpClient`

```python
class JenkinsHttpClient(JenkinsClient):
    jenkins_server: Jenkins | None = None

    def __init__(self, jenkins_url: str):
        self.jenkins_url = jenkins_url

    @override
    def login(self, username: str | None = None, password: str | None = None) -> bool:
        server = Jenkins(self.jenkins_url, username, password)
        user_details = server.get_whoami()
        if user_details.get("fullName") is None:
            return False
        self.jenkins_server = server
        return True

    @override
    def list_jobs(self) -> list | None:
        if self.jenkins_server is None:
            return None
        return self.jenkins_server.get_all_jobs()

    @override
    def get_job_config(self, name: str) -> str | None:
        if self.jenkins_server is None:
            return None
        return self.jenkins_server.get_job_config(name)

    @override
    def get_queue_item(self, queue_id: int) -> dict | None:
        if self.jenkins_server is None:
            return None
        return self.jenkins_server.get_queue_item(queue_id)

    @override
    def get_build_info(self, name: str, build_number: int) -> dict | None:
        if self.jenkins_server is None:
            return None
        return self.jenkins_server.get_build_info(name, build_number)

    @override
    def trigger_build(
        self,
        name: str,
        parameters: Mapping[str, Incomplete] | Sequence[tuple[str, Incomplete]] | None,
    ) -> int | None:
        if self.jenkins_server is None:
            return None
        return self.jenkins_server.build_job(name, parameters=parameters)

    @override
    def create_pipeline(self, name: str, groovy_script: str) -> None:
        if self.jenkins_server is None:
            return None
        config_xml = _create_job_xml(groovy_script)
        return self.jenkins_server.create_job(name, config_xml)
```

### 3. Stub `JenkinsSshClient`

```python
class JenkinsSshClient(JenkinsClient):
    def __init__(self, host: str, port: int = 22):
        self.host = host
        self.port = port

    @override
    def login(self, username: str | None = None, password: str | None = None) -> bool:
        raise NotImplementedError("SSH login not yet implemented")

    # ... same pattern for all other methods
```

### 4. Extract `_create_job_xml` to module-level function

Move from `Client` to a standalone function since it's transport-agnostic:

```python
def _create_job_xml(groovy_script: str) -> str:
    return f"""..."""
```

### 5. Refactor `Client` to use composition

- Add `jenkins_client: JenkinsClient` field
- In `__init__`, create `JenkinsHttpClient(self.jenkins_url)` by default
- Remove all jenkins methods from `Client`
- Remove `jenkins_server` field
- Keep `jenkins_url` on `Client` for constructing `JenkinsHttpClient`
- Update `BenignClient` calls: `self.jenkins_login(...)` → `self.jenkins_client.login(...)`
- Update `self.list_jobs()` → `self.jenkins_client.list_jobs()`

### 6. Cleanup

- Remove `jenkins_server` from `Client`
- `jenkins_url` construction stays in `Client.__init__`, passed to `JenkinsHttpClient`
