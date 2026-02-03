pipeline {
  agent any

  environment {
    IMAGE_NAME = "compliance-backend"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build Docker Image') {
      steps {
        sh 'docker build -t $IMAGE_NAME .'
      }
    }

    stage('Run Backend') {
      steps {
        sh '''
          docker rm -f backend || true
          docker run -d -p 5000:5000 --name backend $IMAGE_NAME
        '''
      }
    }
  }
}
