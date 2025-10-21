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
                    withCredentials([usernamePassword(
                        credentialsId: 'dockerhub-cred',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        echo "🚧 Building Docker image..."
                        sh '''
                            docker build -t $IMAGE_NAME:latest .
                        '''
                    }
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
                    cd /home/phamvantinh27032004/project

                    # Auto-detect docker compose
                    if docker compose version >/dev/null 2>&1; then
                        COMPOSE_CMD="docker compose"
                    elif docker-compose version >/dev/null 2>&1; then
                        COMPOSE_CMD="docker-compose"
                    else
                        echo "❌ Docker Compose chưa được cài trong hệ thống!"
                        exit 1
                    fi

                    echo "🔧 Sử dụng Compose command: $COMPOSE_CMD"

                    $COMPOSE_CMD pull
                    $COMPOSE_CMD down
                    $COMPOSE_CMD up -d --remove-orphans
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
