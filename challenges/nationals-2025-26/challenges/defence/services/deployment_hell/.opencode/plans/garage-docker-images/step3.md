# Step 3: Jenkins Changes

## `jenkins/Dockerfile`

Remove legacy canary copy. Add awscli + jq. Copy all apps:

```dockerfile
FROM jenkins/jenkins:lts

USER root
RUN apt-get update \
  && apt-get install -y docker.io awscli jq \
  && rm -rf /var/lib/apt/lists/* \
  && usermod -aG docker jenkins

USER jenkins

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
ENV CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs

COPY jenkins/plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

COPY jenkins/casc/ /var/jenkins_home/casc_configs/

# Copy all app sources
COPY --chown=jenkins:jenkins apps/ /var/jenkins_home/apps/
```

Changes from original:

- Added `awscli jq` to apt-get
- Removed `COPY --chown=jenkins:jenkins canary/` line
- Added `COPY --chown=jenkins:jenkins apps/ /var/jenkins_home/apps/`

## `jenkins/casc/jenkins.yaml`

Replace single `deploy-canary` job with 3 jobs (or one parameterized). Using one parameterized pipeline:

```yaml
jenkins:
  securityRealm:
    legacy: {}
  authorizationStrategy:
    unsecured: {}
  crumbIssuer: "none"
  remotingSecurity:
    enabled: false
  cli: true
  numExecutors: 2

jobs:
  - script: |
      ['canary', 'experimental', 'legacy'].each { appName ->
        pipelineJob("build-and-upload-${appName}") {
          definition {
            cps {
              script("""
                pipeline {
                  agent any
                  environment {
                    APP_NAME = '${appName}'
                  }
                  stages {
                    stage('Load Credentials') {
                      steps {
                        script {
                          def creds = readFile('/shared/garage-creds.env').trim().split('\\n').collectEntries {
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
                        sh "docker build -t \${APP_NAME}:latest /var/jenkins_home/apps/\${APP_NAME}"
                      }
                    }
                    stage('Save & Upload') {
                      steps {
                        sh '''
                          docker save ${APP_NAME}:latest -o /tmp/${APP_NAME}.tar
                          aws s3 cp /tmp/${APP_NAME}.tar s3://docker-images/${APP_NAME}.tar \\
                            --endpoint-url $AWS_ENDPOINT_URL
                          rm -f /tmp/${APP_NAME}.tar
                        '''
                      }
                    }
                  }
                }
              """)
            }
          }
          triggers {
            cron('H/5 * * * *')
          }
        }
      }
```

This creates 3 jobs: `build-and-upload-canary`, `build-and-upload-experimental`, `build-and-upload-legacy`. Each builds image, saves tarball, uploads to Garage.
