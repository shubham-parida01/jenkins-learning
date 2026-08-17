// DEMO PIPELINE — no Airflow, no GCP/BigQuery, no real credentials required.
// generate_result.py fakes both checks locally so you can test the full
// Generate -> Flatten -> Slack -> Fail On Errors flow end-to-end.
//
// Slack is optional: if SLACK_WEBHOOK_URL is not configured as a Jenkins
// credential, this pipeline just prints the payloads instead of posting.

pipeline {
    agent any

    parameters {
        string(name: 'LOAD_DATE', defaultValue: 'AUTO',
               description: 'YYYYMMDD or AUTO (= today UTC)')
        choice(name: 'ENVIRONMENT', choices: ['dev', 'prod'])
        choice(name: 'DEMO_MODE', choices: ['random', 'force-errors', 'force-clean'],
               description: 'random = ~30-40% chance of errors, force-errors = always fail, force-clean = always pass')
    }

    environment {
        RESULT_JSON = 'airflow_result.json'
        SLACK_DIR   = 'slack_payloads'
    }

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
                ./venv/bin/pip install --upgrade pip -q
                if [ -f requirements.txt ]; then
                    ./venv/bin/pip install -r requirements.txt -q
                fi
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                if [ -f test_app.py ]; then
                    ./venv/bin/pip install pytest -q
                    ./venv/bin/python -m pytest test_app.py -v
                else
                    echo 'No test_app.py found — skipping tests.'
                fi
                '''
            }
        }

        stage('Generate Result (simulated)') {
            steps {
                script {
                    def demoFlag = ''
                    if (params.DEMO_MODE == 'force-errors') {
                        demoFlag = '--force-errors'
                    } else if (params.DEMO_MODE == 'force-clean') {
                        demoFlag = '--force-clean'
                    }

                    env.GENERATE_EXIT = sh(
                        script: """
                            ./venv/bin/python generate_result.py \
                              --load-date '${params.LOAD_DATE}' \
                              --environment '${params.ENVIRONMENT}' \
                              --output '${RESULT_JSON}' \
                              ${demoFlag}
                        """,
                        returnStatus: true
                    ).toString()
                }
                sh "cat ${RESULT_JSON}"
            }
        }

        stage('Flatten File Results') {
            steps {
                sh """
                ./venv/bin/python flatten_result.py '${RESULT_JSON}' --output-dir '${SLACK_DIR}'
                ls -la ${SLACK_DIR} || true
                """
            }
        }

        stage('Send Slack Notifications') {
            steps {
                script {
                    def files = sh(
                        script: "find ${SLACK_DIR} -name '*.json' -type f | sort",
                        returnStdout: true
                    ).trim()

                    if (!files) {
                        echo 'No errors found — no Slack notifications required.'
                        return
                    }

                    def hasWebhook = false
                    try {
                        withCredentials([string(credentialsId: 'slack-workflow-webhook', variable: 'SLACK_WEBHOOK_URL')]) {
                            hasWebhook = true
                        }
                    } catch (e) {
                        echo '[demo] slack-workflow-webhook credential not configured — will print payloads instead of sending them.'
                    }

                    files.split('\n').each { file ->
                        def payload = readFile(file)
                        if (hasWebhook) {
                            withCredentials([string(credentialsId: 'slack-workflow-webhook', variable: 'SLACK_WEBHOOK_URL')]) {
                                def response = httpRequest(
                                    httpMode: 'POST',
                                    contentType: 'APPLICATION_JSON',
                                    url: SLACK_WEBHOOK_URL,
                                    requestBody: payload,
                                    validResponseCodes: '100:399'
                                )
                                echo "Sent ${file} -> HTTP ${response.status}"
                            }
                        } else {
                            echo "[demo] Would send ${file}:"
                            echo payload
                        }
                    }
                }
            }
        }

        stage('Fail On Errors') {
            steps {
                script {
                    def result = new groovy.json.JsonSlurper().parseText(readFile(RESULT_JSON))
                    if (result.has_errors) {
                        error("Found ${result.critical_error_count} critical error(s) for load_date=${result.load_date} (DEMO DATA)")
                    } else {
                        echo "No critical errors for load_date=${result.load_date} (DEMO DATA)"
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Demo pipeline completed — no critical errors.'
        }
        failure {
            echo 'Demo pipeline failed — critical errors found in simulated data. See airflow_result.json / slack_payloads/.'
        }
        always {
            archiveArtifacts artifacts: 'airflow_result.json', allowEmptyArchive: true
            archiveArtifacts artifacts: 'slack_payloads/*.json', allowEmptyArchive: true
        }
    }
}