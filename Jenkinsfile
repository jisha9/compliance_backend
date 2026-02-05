pipeline {
    agent any

    environment {
        AWS_REGION = "us-west-1"
        ECR_REPO = "666696661271.dkr.ecr.us-west-1.amazonaws.com/compliance-backend"
        IMAGE_TAG = "${BUILD_NUMBER}"
        CONTAINER_NAME = "backend"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t compliance-backend .'
            }
        }

        stage('Tag Image') {
            steps {
                sh 'docker tag compliance-backend:latest $ECR_REPO:$IMAGE_TAG'
            }
        }

        stage('Login to AWS ECR') {
            steps {
                sh '''
                aws ecr get-login-password --region $AWS_REGION | \
                docker login --username AWS --password-stdin 666696661271.dkr.ecr.us-west-1.amazonaws.com
                '''
            }
        }

        stage('Push Image to ECR') {
            steps {
                sh 'docker push $ECR_REPO:$IMAGE_TAG'
            }
        }

        stage('Deploy New Container') {
            steps {
                sh '''
                docker stop $CONTAINER_NAME || true
                docker rm $CONTAINER_NAME || true
                
                docker run -d \
                -p 5000:5000 \
                --restart unless-stopped \
                --name $CONTAINER_NAME \
                $ECR_REPO:$IMAGE_TAG
                '''
            }
        }
    }
}
