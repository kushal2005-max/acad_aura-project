# run.py - CORRECT VERSION
from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    # Create database tables
    print("🔄 Creating database tables...")
    db.create_all()
    print("✅ Database tables created!")
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(email='admin@acadaura.com').first()
    if not admin:
        admin_user = User(
            name='Administrator',
            email='admin@acadaura.com',
            role='admin',
            status='approved'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created!")
        print("📧 Email: admin@acadaura.com")
        print("🔑 Password: admin123")
    else:
        print("ℹ️  Admin user already exists")

    # Check for existing users
    total_users = User.query.count()
    print(f"👥 Total users in database: {total_users}")

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting AcadAura Application...")
    print("="*50)
    print("📱 Running on: http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)