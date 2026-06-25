# Shell Injection via Parameterized `upload-docker.groovy`

## Summary

Modify existing `build-and-upload-canary` pipeline to accept `APP_NAME` as a user-supplied string parameter instead of hardcoded env var. Groovy double-quoted string interpolation into `sh` commands = classic shell injection (CWE-78).

## Changes

### 1. `server_files/jenkins/casc/jenkins.yaml`

Replace the `build-and-upload-canary` job block. Change `environmentVariables(APP_NAME: '${appName}')` to a `parameters` block with `stringParam`.

**Before:**
```yaml
['canary'].each { appName ->
  pipelineJob("build-and-upload-${appName}") {
    environmentVariables(APP_NAME: '${appName}')
    definition {
      cps {
        script(
          readFileFromWorkspace(
            "/var/jenkins_home/pipelines/upload-docker.groovy"
          )
        )
      }
    }
    triggers {
      cron('0/2 * * * *')
    }
  }
}
```

**After:**
```yaml
pipelineJob("build-and-upload-canary") {
  parameters {
    stringParam('APP_NAME', 'canary', 'Application name to build')
  }
  definition {
    cps {
      script(
        readFileFromWorkspace(
          "/var/jenkins_home/pipelines/upload-docker.groovy"
        )
      )
    }
  }
  triggers {
    cron('0/2 * * * *')
  }
}
```

### 2. `server_files/jenkins/pipelines/upload-docker.groovy`

Change `${APP_NAME}` (env var) references to `${params.APP_NAME}` (Groovy param interpolation). Keep them in **double-quoted** Groovy strings so Groovy interpolates before shell execution (this IS the vulnerability).

Also fix the missing `steps { }` wrapper in "Load Credentials" stage.

**Full replacement file:**
```groovy
pipeline {
  agent any
  stages {
    stage("Load Credentials") {
      steps {
        script {
          def creds = readFile('/shared/garage-creds.env').trim().split('\n').collectEntries {
            def parts = it.split('=', 2)
            [(parts[0]): parts[1]]
          }
          env.AWS_ACCESS_KEY_ID = creds['AWS_ACCESS_KEY_ID']
          env.AWS_SECRET_ACCESS_KEY = creds['AWS_SECRET_ACCESS_KEY']
          env.AWS_ENDPOINT_URL = creds['AWS_ENDPOINT_URL']
          env.AWS_DEFAULT_REGION = creds['AWS_DEFAULT_REGION']
        }
      }
    }
    stage('Build') {
      steps {
        sh "docker build -t ${params.APP_NAME}:latest /var/jenkins_home/apps/${params.APP_NAME}"
      }
    }
    stage('Save & Upload') {
      steps {
        sh """
          docker save ${params.APP_NAME}:latest -o /tmp/${params.APP_NAME}.tar
          aws s3 cp /tmp/${params.APP_NAME}.tar s3://docker-images/${params.APP_NAME}.tar \
            --endpoint-url \$AWS_ENDPOINT_URL
          rm -f /tmp/${params.APP_NAME}.tar
        """
      }
    }
  }
}
```

## Attack Flow

1. Attacker signs up on Jenkins (signup enabled per CasC config)
2. Logged-in users have full access (`loggedInUsersCanDoAnything`)
3. Trigger `build-and-upload-canary` with `APP_NAME` = `canary; cat /flag #`
4. Groovy interpolates → shell receives: `docker build -t canary; cat /flag #:latest ...`
5. Shell executes injected command; rest is commented out

## Why This Works

- Groovy `"..."` strings interpolate variables **before** passing to shell
- `params.APP_NAME` is fully user-controlled
- No sanitization or validation on the parameter
- Single-quoted strings (`'...'`) would be safe; double-quoted are not
