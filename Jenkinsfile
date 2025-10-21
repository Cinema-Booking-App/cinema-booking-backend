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
                    docker rm -f cinema_backend || true
                    docker run -d \
                        -p 8000:8000 \
                        --name cinema_backend \
                        -e DATABASE_URL="postgresql+psycopg2://postgres:12345678@172.22.0.3:5432/cinema-booking" \
                        -e SECRET_KEY="supersecretkey" \
                        -e ACCESS_TOKEN_EXPIRE_MINUTES=30 \
                        -e REFRESH_TOKEN_EXPIRE_DAYS=7 \
                        -e ALGORITHM="HS256" \
                        -e CORS_ALLOW_ORIGINS="http://136.110.0.26:3000" \
                        phamvantinh/cinema-backend-fastapi:latest
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
