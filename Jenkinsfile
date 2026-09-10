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
                bat 'docker build -t shopease:latest .'
            }
        }

        stage('Test') {
            steps {
                bat 'docker images shopease:latest'
            }
        }
    }
}