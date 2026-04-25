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
- SQLite  
- HTML / CSS  

---

## Project Structure
News Application/
|
|-- articles/
| |-- models.py
| |-- views.py
| |-- urls.py
| |-- api/
| | |-- views.py
| | |-- urls.py
| |
| |-- forms.py
|
|-- news_project/
| |-- settings.py
| |-- urls.py
|
|-- templates/
|-- base.html


---

## Setup Instructions

1. Clone the repo

git clone https://github.com/tractionctr/News-Application.git

cd news-application


2. Install dependencies

pip install -r requirements.txt


3. Run migrations

python manage.py migrate


4. Create superuser (optional but recommended)

python manage.py createsuperuser


5. Run server

python manage.py runserver


6. Open in browser

http://127.0.0.1:8000/


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
