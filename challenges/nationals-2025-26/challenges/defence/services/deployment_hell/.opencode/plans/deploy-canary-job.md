# Plan: Deploy Canary Job

## Goal
Fill the empty `deploy-canary` job in `jenkins.yaml` so it downloads the canary Docker image from Garage S3 and runs it, triggered automatically after `build-and-upload-canary` succeeds.

## Changes

### 1. Create `server_files/jenkins/pipelines/deploy-docker.groovy`

New file. Pipeline that:
- Loads Garage S3 creds from `/shared/garage-creds.env` (same pattern as `upload-docker.groovy`)
- Downloads `s3://docker-images/canary.tar` via `aws s3 cp`
- `docker load` the tar
- Removes existing `canary` container if any (`docker rm -f canary || true`)
- Runs `docker run -d --name canary -p 9000:9000 canary:latest`

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
    stage('Download Image') {
      steps {
        sh '''
          aws s3 cp s3://docker-images/canary.tar /tmp/canary.tar \
            --endpoint-url $AWS_ENDPOINT_URL
        '''
      }
    }
    stage('Load & Deploy') {
      steps {
        sh '''
          docker load -i /tmp/canary.tar
          rm -f /tmp/canary.tar
          docker rm -f canary || true
          docker run -d --name canary -p 9000:9000 canary:latest
        '''
      }
    }
  }
}
```

### 2. Edit `server_files/jenkins/casc/jenkins.yaml` (lines 44-52)

Replace the empty `deploy-canary` job block with:

```yaml
  - script: |
      pipelineJob("deploy-canary") {
        definition {
          cps {
            script(
              readFileFromWorkspace(
                "/var/jenkins_home/pipelines/deploy-docker.groovy"
              )
            )
          }
        }
        triggers {
          upstream('build-and-upload-canary', 'SUCCESS')
        }
      }
```

This references the new groovy file and adds an upstream trigger so it runs after `build-and-upload-canary` succeeds.
