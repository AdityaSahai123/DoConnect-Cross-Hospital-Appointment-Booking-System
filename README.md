# 🏥 DocConnect – Unified Multi-Hospital Appointment Booking System

Welcome to **DocConnect**, a powerful Django-based web application that enables patients to book appointments across multiple hospitals seamlessly. Built to handle **heterogeneous schemas** across different database systems, DocConnect intelligently maps and integrates data using **semantic matching** and **NLP techniques**.

## 📌 Features

### ✅ Patient-Centric Appointment Management
- User registration & login
- View available doctors by specialization
- Book & cancel appointments
- View upcoming, completed, and cancelled appointments

### 🧠 Intelligent Schema Matching
- Matches global schema with hospital-specific schemas using:
  - `token`, `fuzzy`, and `semantic` matching (using `Sentence-BERT`)
  - Automatic table name detection
  - Foreign key resolution

### 🔄 Multi-Database Integration
- PostgreSQL (Render-hosted)
- MySQL (TiDB Cloud-hosted)
- Schema-agnostic querying across hospitals

---

## 🏗️ Project Architecture

```text
📦 docconnect/
 ┣ 📂 appointments/
 ┣ 📁 docconnect 
 ┣ 📂 patients/
 ┣ 📂 templates/
 ┣ 📂 static/
 ┣ 📜 manage.py
 ┣ 📜 .env
 ┗ 📜 README.md

```

## ⚙️ Technologies Used

| Area | Tech Stack |
|------|------------|
| 🧠 NLP | sentence-transformers, difflib |
| 🎯 Backend | Django 5.1.2, Python 3.11 |
| 🗃 Databases | PostgreSQL, MySQL (TiDB Cloud) |
| 💻 Frontend | HTML, CSS, Bootstrap 5 |


## 🔐 Security & Session Handling
- Session-based authentication for patients
- Password hashing and data validation (can be extended using django.contrib.auth)
- Role-based access ready (extendable)

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/docconnect.git
cd docconnect
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Configure .env
Create a `.env` file and fill in your database credentials:


### 4. Run Migrations
```bash
python manage.py migrate
```

### 5. Start the Development Server
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000 to access the app.

---


---
