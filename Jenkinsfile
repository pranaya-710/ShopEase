pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t pranaya803/shopease:latest .'
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USERNAME',
                    passwordVariable: 'DOCKER_PASSWORD'
                )]) {
                    bat '''
                        echo | set /p="%DOCKER_PASSWORD%" | docker login docker.io -u %DOCKER_USERNAME% --password-stdin
                        docker push %DOCKER_USERNAME%/shopease:latest
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                withCredentials([sshUserPrivateKey(
                    credentialsId: 'ec2-ssh',
                    keyFileVariable: 'SSH_KEY',
                    usernameVariable: 'SSH_USER'
                )]) {
                    bat '''
                        echo Deploying application to EC2...

                        ssh -o StrictHostKeyChecking=no -i "%SSH_KEY%" %SSH_USER%@54.175.151.139 "cd /root/ShopEase && docker compose pull web && docker compose up -d web"
                    '''
                }
            }
        }
    }
}