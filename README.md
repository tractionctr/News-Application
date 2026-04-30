# 📰 News Application

A role-based Django web application where users can read, create, and manage articles and newsletters.

---

## Features

### Authentication
- User registration (sign up)
- Login / logout system
- Role-based access control

### Roles
- **Reader** → View articles and newsletters  
- **Journalist** → Create and manage own content  
- **Editor** → Approve, edit, and manage all content  

### Articles
- Create, edit, and delete articles  
- Approval system (Editor only)  
- View approved articles  

### Newsletters
- Create newsletters  
- Add multiple articles  
- Edit and view newsletters  

### API
- REST API built with Django REST Framework  
- Endpoints for articles and newsletters  
- Custom API docs page at `/api/docs/`  

---

## Tech Stack

- Django  
- Django REST Framework  
- Bootstrap 5  
- MySQL  
- HTML / CSS

---

## Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/tractionctr/News-Application.git
cd News-Application
```

### 2. Create virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**
```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and update values.

Example:

```bash
copy .env.example .env
```

### 5. Create MySQL database

Run this in MySQL:

```sql
CREATE DATABASE news_application;
```

Then update DB credentials in `.env`.

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Create superuser (optional)

```bash
python manage.py createsuperuser
```

### 8. Run server

```bash
python manage.py runserver
```

### 9. Open in browser

```text
http://127.0.0.1:8000/
```

---

## API Endpoints

### Articles
- `GET /api/articles/`
- `POST /api/articles/`
- `GET /api/articles/<id>/`
- `PUT /api/articles/<id>/`
- `DELETE /api/articles/<id>/`

### Newsletters
- `GET /api/newsletters/`
- `POST /api/newsletters/`
- `GET /api/newsletters/<id>/`
- `PUT /api/newsletters/<id>/`
- `DELETE /api/newsletters/<id>/`

---

## Future Improvements

- Search and filtering  
- Comment system  
- Notifications  
- Analytics dashboard  

---
