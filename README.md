# OFO - Online Food Ordering Platform

![Python](https://img.shields.io/badge/python-3.11-blue.svg)![Flask](https://img.shields.io/badge/flask-2.x-green.svg)![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-orange.svg)![Cypress](https://img.shields.io/badge/Cypress-E2E%20Testing-brightgreen)![Jenkins](https://img.shields.io/badge/Jenkins-CI/CD-blue)![Docker](https://img.shields.io/badge/Docker-Container-blue)

OFO is a full-stack web application that simulates a complete online food ordering and delivery platform. The project is designed with a robust architecture to serve three primary user roles: **Customers**, **Restaurant Owners**, and **Administrators**. It integrates modern technologies and features a fully automated CI/CD pipeline for testing and deployment.

## ✨ Key Features

### 👨‍🍳 For Customers
-   **Authentication:** Secure user registration and login using phone number and password.
-   **Intelligent Search:** Search for restaurants by category or based on the user's current location. Restaurants are classified into "Nearby" and "Other Suggestions".
-   **Restaurant & Menu Viewing:** Detailed restaurant pages with categorized menus and customizable dish options (e.g., size, toppings, spice level).
-   **Cart Management:** Add, update, and remove items from a multi-restaurant shopping cart.
-   **Checkout & Promotions:** A streamlined checkout process with integrated **MoMo Payment Gateway** and a system for applying promotional vouchers.
-   **Order Tracking:** Real-time order status tracking from "Pending" to "Completed".
-   **Order History & Reviews:** View past orders and submit detailed reviews with star ratings and image uploads.
-   **AI Chatbot:** An integrated chatbot powered by **Google's Gemini API** to assist users with inquiries and suggestions.
-   **Favorite Restaurants:** Mark restaurants as favorites for quick access.

### 🍽️ For Restaurant Owners
-   **Restaurant Registration:** A dedicated registration flow to create a restaurant profile and owner account, pending admin approval.
-   **Dashboard & Menu Management:** A comprehensive dashboard to manage the restaurant's menu, including:
    -   Creating and managing dish groups (e.g., "Appetizers", "Main Courses").
    -   Adding, editing, and deleting dishes with images and descriptions.
    -   Creating complex, reusable option groups (e.g., "Choose your size," "Add toppings") with mandatory rules and selection limits.
-   **Order Management:** View incoming orders in real-time, update their status (e.g., "Confirmed", "Delivering"), and track order history. Real-time notifications for new orders are powered by **Socket.IO**.
-   **Voucher Management:** Create and manage promotional campaigns and discount codes.
-   **Revenue Statistics:** A reporting dashboard to visualize sales data over selected time periods.

### ⚙️ For Administrators
-   **Admin Panel:** A secure admin interface built with **Flask-Admin**.
-   **Restaurant Approval:** Review and approve new restaurant registrations to activate them on the platform.
-   **User Management:** View, edit, and manage all user accounts across different roles.

## 🛠️ Technology Stack

| Category      | Technology / Library                                                              |
| :------------ | :-------------------------------------------------------------------------------- |
| **Backend**   | Python 3.11, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Admin, Flask-SocketIO    |
| **Frontend**  | HTML5, CSS3, Bootstrap 5, JavaScript (ES6+), Jinja2                               |
| **Database**  | MySQL / MariaDB (for Development/Production), SQLite (for Testing)                |
| **Testing**   | **Unit/Integration:** Unittest (Python), Coverage.py <br> **End-to-End:** Cypress  |
| **APIs**      | MoMo (Payment), Google Gemini (AI Chatbot), Goong Maps (Geocoding & Maps)          |
| **DevOps**    | Docker, Jenkins (CI/CD), Cloudinary (Image Hosting), Railway (Deployment)         |

## 🚀 Setup and Installation

Follow these steps to run the project locally.

### Prerequisites
-   Python 3.11+
-   Node.js and npm (for installing Cypress and other frontend dependencies)
-   A running MySQL or MariaDB server

### Local Setup
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/anh-khoa-nguyen/OFOProject.git
    cd OFOProject/OFO
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    # For Windows
    python -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Update the database connection string in `config.py` (`DevelopmentConfig` class) with your MySQL credentials:
    ```python
    # D:\OFOProject\OFO\config.py
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://YOUR_USER:%s@localhost/ofodb?charset=utf8mb4" % quote('YOUR_PASSWORD')
    ```
    You also need to set up API keys for MoMo, Google, and Cloudinary in the same file.

5.  **Create and Seed the Database:**
    Run the `create_db.py` script to set up the database schema and populate it with sample data.
    ```bash
    python create_db.py
    ```

6.  **Run the Flask Application:**
    The application uses Socket.IO, so run it via `run.py`.
    ```bash
    python run.py
    ```
    The application will be available at `http://127.0.0.1:5000`.

## 🧪 Running Tests

The project includes a comprehensive test suite.

### Unit & Integration Tests
Ensure your Flask environment is configured for testing and run the `unittest` discover command from the `OFO` directory.
```bash
# From the D:\OFOProject\OFO directory
set FLASK_CONFIG=testing
python -m unittest discover```

### End-to-End (E2E) Tests with Cypress
1.  **Install Cypress:**
    ```bash
    # From the D:\OFOProject\OFO directory
    npm install
    ```

2.  **Run the tests:**
    Make sure the Flask application is running. Then, open the Cypress Test Runner:
    ```bash
    npx cypress open
    ```
    Select the desired spec file to run the tests.

## 🔄 CI/CD Pipeline (Jenkins)

This project is configured with a `Jenkinsfile` for a complete Continuous Integration and Continuous Deployment pipeline, which automates the following stages:

1.  **Update Code:** Pulls the latest changes from the specified Git branch.
2.  **Setup Environment:** Installs all necessary Python and Node.js dependencies.
3.  **Run Unit Tests:** Executes the Python unit test suite and generates a coverage report.
4.  **Run E2E Tests:** Starts the Flask server in the background and runs the full Cypress E2E test suite.
5.  **Build & Push Docker Image:** If changes are detected in the source code or Docker configuration, it builds a new Docker image, tags it with the build number and `latest`, and pushes it to Docker Hub.
6.  **Trigger Railway Redeploy:** Automatically triggers a new deployment on the Railway hosting platform using the latest Docker image.
