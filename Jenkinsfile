pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
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

        stage('Build') {
            steps {
                sh 'echo "Building the application..."'
                sh './venv/bin/python app.py'
            }
        }

        stage('Generate Airflow Result') {
            steps {
                sh './venv/bin/python generate_result.py'
                sh 'cat airflow_result.json'
            }
        }

        stage('Flatten File Results') {
            steps {
                sh './venv/bin/python flatten_result.py airflow_result.json'
                sh 'ls -la slack_payloads'
            }
        }

        stage('Send Slack Notifications') {
    steps {
        script {

            withCredentials([
                string(
                    credentialsId: 'slack-workflow-webhook',
                    variable: 'SLACK_WEBHOOK_URL'
                )
            ]) {

                def files = sh(
                    script: 'find slack_payloads -name "*.json" -type f',
                    returnStdout: true
                ).trim()

                if (!files) {
                    echo 'No failed files. No Slack notifications required.'
                    return
                }

                files.split('\n').each { file ->

                    echo "Sending failure notification: ${file}"

                    def payload = readFile(file)

                    httpRequest(
                        httpMode: 'POST',
                        contentType: 'APPLICATION_JSON',
                        url: SLACK_WEBHOOK_URL,
                        requestBody: payload
                    )
                }
            }
        }
    }
}
    }

    post {

        success {
            echo 'Pipeline completed successfully.'
        }

        failure {
            echo 'Pipeline failed. Please check the logs for details.'
        }
    }
}