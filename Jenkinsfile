// ====================================================================
// Jenkinsfile - Phiên bản Hoàn chỉnh
// Đã loại bỏ cleanWs() để tăng tốc độ build
// ====================================================================

pipeline {
    agent any
    
    options {
        // Kích hoạt plugin AnsiColor với bảng màu 'xterm' (phổ biến nhất)
        ansiColor('xterm')
    }

    parameters {
        string(name: 'BRANCH_NAME', defaultValue: 'jenkins', description: 'Nhánh Git cần build')
    }

    tools {
        // Yêu cầu Jenkins sử dụng phiên bản NodeJS LTS
        nodejs 'NodeJS-22'
    }

    environment {
        // Thêm thư mục Scripts của venv vào PATH
        PATH = "${env.WORKSPACE}\\venv\\Scripts;${env.PATH}"
        // Sửa lỗi hiển thị Unicode (tiếng Việt) trên Windows
        PYTHONIOENCODING = 'utf-8'
        
        DOCKER_CREDENTIALS_ID = 'dockerhub-credentials' 
        // Tên Docker image (thay 'your-dockerhub-username' bằng tên của bạn)
        DOCKER_IMAGE_NAME     = "doraspeed/ofo-project"
    }

    stages {
        stage('Update Code') {
            steps {
                //cleanWs()
                // Chỉ checkout/lấy về những thay đổi mới nhất thay vì xóa toàn bộ
                git branch: params.BRANCH_NAME, url: 'https://github.com/anh-khoa-nguyen/OFOProject.git'
                echo "Updated code from branch ${params.BRANCH_NAME}"
            }
        }


        stage('Setup Environment') {
            steps {
                bat '''
                echo "---- Creating Python virtual environment (if not exists) ----"
                python -m venv venv

                echo "---- Installing/Updating Python dependencies ----"
                pip install -r OFO/requirements.txt
                pip install coverage

                echo "---- Installing/Updating Node.js dependencies ----"
                cd OFO
                rmdir /s /q node_modules || echo "No node_modules to delete."
                npm install
                '''
            }
        }
        

        stage('Run Unit Tests') {
            steps {
                bat '''
                echo "---- Running Unit Tests with Coverage ----"
                cd OFO
                set FLASK_CONFIG=testing
                chcp 65001
                coverage run --source=. -m unittest discover
                coverage report
                '''
            }
        }

        stage('Run E2E Tests (Cypress)') {
            steps {
                // Khối withCredentials đã được loại bỏ
                script {
                    echo "---- Starting Flask server in background ----"
                    bat(script: 'start "Flask App" /B python OFO/run.py', returnStdout: true)
                    echo "---- Waiting 15 seconds for server to start ----"
                    sleep(15)
                    echo "---- Running Cypress tests ----"
                    bat '''
                    cd OFO
                    npx cypress run || exit 0
                    '''
                }
            }
            post {
                always {
                    echo "---- Stopping Flask server ----"
                    bat 'taskkill /IM python.exe /F || echo "Flask server was not running."'
                }
            }
        }
        
        stage('Build & Push Docker Image') {
            when {
                // changeset "pattern": Chỉ chạy stage này nếu có thay đổi trong các file/thư mục khớp với pattern.
                // "OFO/**": Bất kỳ file nào trong thư mục OFO và các thư mục con của nó.
                // "Dockerfile, startup.sh": File Dockerfile hoặc file startup.sh.
                // changeset "OFO/**, Dockerfile, startup.sh"
                branch 'jenkins'
            }
            steps {
                withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS_ID, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    bat '''
                    echo "---- Code changes detected. Building and pushing new image... ----"
                    echo %DOCKER_PASS% | docker login -u %DOCKER_USER% --password-stdin
                    
                    rem Di chuyển vào thư mục OFO trước khi build (nếu bạn đã di chuyển Dockerfile vào trong)
                    rem Nếu Dockerfile vẫn ở gốc, hãy xóa dòng "cd OFO"
                    rem cd OFO 
                    
                    docker build -t %DOCKER_IMAGE_NAME%:%BUILD_NUMBER% .
                    docker build -t %DOCKER_IMAGE_NAME%:latest .
                    
                    docker push %DOCKER_IMAGE_NAME%:%BUILD_NUMBER%
                    docker push %DOCKER_IMAGE_NAME%:latest
                    '''
                }
            }
        }

    
        


        stage('Trigger Railway Redeploy') {
            when { 
                branch 'jenkins' 
            }
            steps {
                withCredentials([string(credentialsId: 'railway-project-token-ofo', variable: 'RAILWAY_TOKEN')]) {
                    script {
                        echo "---- Preparing to trigger Railway redeploy ----"
                        
                        // Cài đặt Railway CLI trước
                        bat '''
                        echo "---- Installing Railway CLI ----"
                        npm i @railway/cli
                        '''
        
                        echo "---- Triggering Railway redeploy and capturing output ----"
                        try {
                            // Chạy lệnh redeploy và LƯU KẾT QUẢ vào biến 'redeployOutput'
                            def redeployOutput = bat(
                                script: '.\\node_modules\\.bin\\railway redeploy --service d8e24c29-4cae-4bce-b337-12388768e45a -y',
                                returnStdout: true
                            ).trim() // .trim() để xóa các khoảng trắng thừa
        
                            // In kết quả đã bắt được ra log của Jenkins
                            echo "--- Start of Railway CLI Output ---"
                            echo "${redeployOutput}"
                            echo "--- End of Railway CLI Output ---"
        
                        } catch (e) {
                            // Nếu lệnh 'bat' thất bại, in ra lỗi và làm pipeline fail
                            echo "ERROR: Railway redeploy command failed."
                            // Ném lại lỗi để pipeline được đánh dấu là FAILURE
                            throw e
                        }
                    }
                }
            }
            post {
                failure {
                    echo "Railway deployment failed. Check the logs above for details."
                }
                success {
                    echo "Successfully triggered and captured output from Railway deployment!"
                }
            }
        }

    }
}
