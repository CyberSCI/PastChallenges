FROM jenkins/jenkins:2.555.2-lts

USER root
# Install Docker CLI so Jenkins pipelines can run docker commands
ARG DOCKER_GID=999
RUN apt-get update \
  && apt-get install -y docker.io awscli jq \
  && rm -rf /var/lib/apt/lists/*

USER jenkins

ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false -Dpermissive-script-security.enabled=true"
ENV CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs

COPY jenkins/plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --latest false --plugin-file /usr/share/jenkins/ref/plugins.txt 

# COPY jenkins/casc/ /var/jenkins_home/casc_configs/

COPY --chown=jenkins:jenkins apps/ /var/jenkins_home/apps/
