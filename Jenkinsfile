pipeline {
    agent any

    stages {

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
                        echo Logging in to Docker Hub...
                        echo %DOCKER_PASSWORD%| docker login docker.io -u %DOCKER_USERNAME% --password-stdin

                        echo Pushing image...
                        docker push %DOCKER_USERNAME%/shopease:latest

                        echo Logging out...
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                bat '''
                    echo Deploying application...
                    docker compose pull
                    docker compose up -d
                '''
            }
        }
    }
}