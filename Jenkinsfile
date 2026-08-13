pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage("Install Dependencies") {
            steps {
                sh '''
                python3 -m venv venv
                ./venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh './venv/bin/pytest'
            }
        }

        stage('Build'){
            steps {
                sh 'echo "Building the application..."'
                sh './venv/bin/python app.py '
            }
        }

    }

    post {
        success {
            withCredentials([string(credentialsId: 'slack-workflow-webhook', variable: 'SLACK_WEBHOOK_URL')]) {
                httpRequest(
                    httpMode: 'POST',
                    contentType: 'APPLICATION_JSON',
                    url: env.SLACK_WEBHOOK_URL,
                    requestBody: """{
                        "job_name": "${env.JOB_NAME}",
                        "build_number": "${env.BUILD_NUMBER}",
                        "status": "success",
                        "message": "The Jenkins pipeline has completed successfully."
                    }"""
                )
            }
            
            echo 'Pipeline completed successfully.'
        }
        failure {
            withCredentials([string(credentialsId: 'slack-workflow-webhook', variable: 'SLACK_WEBHOOK_URL')]) {
            httpRequest(
                httpMode: 'POST',
                contentType: 'APPLICATION_JSON',
                url: env.SLACK_WEBHOOK_URL,
                requestBody: """{
                    "job_name": "${env.JOB_NAME}",
                    "build_number": "${env.BUILD_NUMBER}",
                    "status": "failure",
                    "message": "The Jenkins pipeline has failed."
                }"""
            )
            echo 'Pipeline failed. Please check the logs for details.'
        }
        }

    }
}