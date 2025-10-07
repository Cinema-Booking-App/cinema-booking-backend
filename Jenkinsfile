pipeline {
    agent any
    stages {
        stage('Pull Code') {
            steps {
                git branch: 'main', url: 'https://github.com/tinhpham/backend-fastapi.git'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t fastapi-backend .'
            }
        }
        stage('Run Container') {
            steps {
                sh '''
                docker stop fastapi-backend || true
                docker rm fastapi-backend || true
                docker run -d --name fastapi-backend -p 8000:8000 fastapi-backend
                '''
            }
        }
    }
}
