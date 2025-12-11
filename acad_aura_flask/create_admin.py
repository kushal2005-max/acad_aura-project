from app import create_app
from app.extensions import db
from app.models import User

app = create_app()
app.app_context().push()

name = input("Admin Name: ")
email = input("Admin Email: ")
password = input("Admin Password: ")

u = User(name=name, email=email, role="admin", status="approved")
u.set_password(password)

db.session.add(u)
db.session.commit()

print("Admin created successfully!")
