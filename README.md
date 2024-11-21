![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)
[![Machine Learning Client CI Pipeline](https://github.com/software-students-fall2024/4-containers-put-the-fries-in-the-bag/actions/workflows/ml-client.yml/badge.svg)](https://github.com/software-students-fall2024/4-containers-put-the-fries-in-the-bag/actions/workflows/ml-client.yml)
[![Web App CI/CD Pipeline](https://github.com/software-students-fall2024/4-containers-put-the-fries-in-the-bag/actions/workflows/web-app.yml/badge.svg)](https://github.com/software-students-fall2024/4-containers-put-the-fries-in-the-bag/actions/workflows/web-app.yml)

# Containerized App Exercise- HarryFace

## Description
- Harry Face is a fun and interactive web application that uses face recognition technology to determine which Harry Potter character you most resemble. Whether you\'re a Gryffindor, Slytherin, Ravenclaw, or Hufflepuff, Harry Face brings a magical twist to face recognition!

## Team Members   
- [Alex Ruan](https://github.com/axruan)
- [Angela Zhang](https://github.com/angelazzh)
- [Leo Bernarbezheng](https://github.com/leonaurdo)
- [David Lai](https://github.com/danonymouse)

## 📚 Features

1. **🔒 User Authentication:**
    - Secure Registration & Login: Create an account or log in with your credentials.
    - Password Security: Passwords are securely hashed with bcrypt.

2. **🎭 Face Matching:**
    - Upload a Photo: The app identifies which Harry Potter character you resemble using machine learning.

3. **📊 Analytics Dashboard:**
    - Match Statistics: Track which characters you resemble most over time.
    - Percentage Distribution: See your matches as percentages for each character.

4. **🕰️ Match History:**
    - Timestamped Records: View a complete history of all your matches.

5. **⚙️Robust Error Handling:**
    - Friendly error messages for invalid uploads or system issues.
    - Secure endpoints to protect user data.

## 🚀 How to Run the Project

### **Prerequisites**
1. **Python:** Ensure you have Python 3.10 or higher installed.
2. **Docker:** Install the Docker desktop app to run the MongoDB service.
3. **Pipenv:** Install Pipenv for managing dependencies:
    ```bash
        pip install pipenv
    ```
3. **Environment Variables:** Prepare a .env file for both the ML client and web app.

### **Clone the Repository**
```bash
    git clone https://github.com/software-students-fall2024/4-containers-put-the-fries-in-the-bag.git
```
### **Change Directory**
```bash
    cd 4-containers-put-the-fries-in-the-bag
```

### **Set Up Environment Variables**
- Create a .env file in the root directory of the repository.
- Please check Discord for more information about the .env file.

### **Set Up the Machine Learning Client**
- Navigate to the ml-client directory:
    ```bash
        cd machine_learning_client
    ```
- Activate the Pipenv virtual environment:
    ```bash
        pipenv shell
    ```
- Install development dependencies:
    ```bash
        pipenv install --dev
    ```

### **Set Up the Web App Client**
- Navigate to the ml-client directory:
    ```bash
        cd web_app    
    ```
- Activate the Pipenv virtual environment:
    ```bash
        pipenv shell
    ```
- Install development dependencies:
    ```bash
        pipenv install --dev
    ```

### **Building the Containers with Docker**
- Open the Docker application and register for an account (if you don't have one already).
- Keep the application running in the background and start/buiild Docker by:
    ```bash
        docker compose up --force-recreate --build
    ```
- Wait for the containers to build and start.
- Open your browser and navigate to http://localhost:5001 to access the web app.

### **Navigating HarryFace**
- Register an account and log in.
- A webcam will pop up, allow it to access your camera and click the "Capture Photo" button.
- The app will recognize your face and display the most similar Harry Potter character.
- You can view your match statistics and match history on the dashboard.

### **Shut Down the Docker Containers**
- To shut down the Docker containers, run:
    ```bash
        docker compose down
    ```
