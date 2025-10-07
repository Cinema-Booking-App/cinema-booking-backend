pipeline {
    agent any

    environment {
        REGISTRY = "docker.io"
        IMAGE_NAME = "cinema-backend-fastapi"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'dev',
                    url: 'https://github.com/Cinema-Booking-App/cinema-booking-backend.git',
                    credentialsId: 'github-token'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "🚧 Building Docker image..."
                    sh 'docker build -t $REGISTRY/${DOCKER_USER}/$IMAGE_NAME:latest .'
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: 'dockerhub-cred',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        echo "📦 Pushing image to Docker Hub..."
                        sh '''
                            echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                            docker push $REGISTRY/$DOCKER_USER/$IMAGE_NAME:latest
                        '''
                    }
                }
            }
        }

        stage('Deploy to Server') {
            steps {
                script {
                    echo "🚀 Deploying backend container..."
                    sh '''
                    cd /home/ubuntu/project
                    docker compose pull
                    docker compose down
                    docker compose up -d
                    docker image prune -f
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "✅ Backend deploy thành công!"
        }
        failure {
            echo "❌ Có lỗi xảy ra trong pipeline!"
        }
    }
}
