
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
                  bat '''
                       echo Deploying application...

                       cd /d C:\\Users\\prana\\OneDrive\\Desktop\\Projects\\Shopease

                       docker compose pull
                       if errorlevel 1 exit /b 1

                       docker compose up -d
                      if errorlevel 1 exit /b 1
                    '''
    }
}
    }
}
