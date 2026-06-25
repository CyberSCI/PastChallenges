pipeline {
  agent any
  parameters {
    string(
      name: 'projectName', 
      defaultValue: 'canary', 
      description: 'name of the project to build'
    )                  
  }
  stages {
    stage("Load Credentials") {
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
          env.PROJECT_NAME = params.projectName
        }
      }
    }
    stage('Build') {
      steps {
        sh "docker build -t ${PROJECT_NAME}:latest /var/jenkins_home/apps/${PROJECT_NAME}"
      }
    }
    stage('Save & Upload') {
      steps {
        sh '''
          docker save ${PROJECT_NAME}:latest -o /tmp/${PROJECT_NAME}.tar
          aws s3 cp /tmp/${PROJECT_NAME}.tar s3://docker-images/${PROJECT_NAME}.tar \\
            --endpoint-url $AWS_ENDPOINT_URL
          rm -f /tmp/${PROJECT_NAME}.tar
        '''
      }
    }
  }
}
