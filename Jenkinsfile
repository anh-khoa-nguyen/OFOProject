pipeline {
    agent any
    
    // Thêm thư mục Scripts của môi trường ảo vào biến PATH
    // Điều này cho phép bạn gọi 'python' và 'pip' một cách ngắn gọn ở các bước sau
    environment {
        PATH = "${env.WORKSPACE}\\venv\\Scripts;${env.PATH}"
    }
    
    stages {
        stage('Clone Code') {
            steps {
                // Jenkins sẽ tự động checkout code từ nhánh đã được cấu hình trong job
                checkout scm 
                echo "Cloned code from branch ${env.BRANCH_NAME}"
            }
        }

        stage('Set up') {
            steps {
                bat '''
                echo "---- Creating virtual environment ----"
                rem Lệnh 'python' ở đây vẫn là python của hệ thống
                python -m venv venv
                
                echo "---- Installing dependencies into venv ----"
                rem Từ đây, 'pip' là pip của venv do biến PATH đã được cập nhật
                pip install -r OFO/requirements.txt
                '''
            }
        }
        
        stage('Test') {
            steps {
                bat '''
                echo "---- Running tests using venv python ----"
                cd OFO
                rem Lệnh 'python' ở đây là python của venv, nên nó sẽ thấy các thư viện đã cài
                python -m unittest tests.test_admin
                '''
            }
        }
    }
}
