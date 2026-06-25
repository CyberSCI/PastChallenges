
pipeline {
  agent any
  parameters {
    string(
      name: 'projectName', 
      defaultValue: 'canary', 
      description: 'name of the project to deploy'
    )                  
  }
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
          env.PROJECT_NAME = params.projectName
        }
      }
    }
    stage('Download Image') {
      steps {
        sh '''
          aws s3 cp s3://docker-images/${PROJECT_NAME}.tar /tmp/${PROJECT_NAME}.tar \
            --endpoint-url $AWS_ENDPOINT_URL
        '''
      }
    }
    stage('Load & Deploy') {
      steps {
        sh '''
          docker load -i /tmp/${PROJECT_NAME}.tar
          rm -f /tmp/${PROJECT_NAME}.tar
          docker rm -f ${PROJECT_NAME} || true
          docker run -d --name ${PROJECT_NAME} -p 9000:9000 ${PROJECT_NAME}:latest
        '''
      }
    }
  }
}
