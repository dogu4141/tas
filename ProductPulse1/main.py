
import os
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

if __name__ == '__main__':
    # Instance klasörünü oluştur
    os.makedirs('instance', exist_ok=True)
    
    with app.app_context():
        # Veritabanını yeniden oluştur
        db.drop_all()
        db.create_all()
        
        # Demo hesapları oluştur
        admin = User(
            username='admin',
            email='admin@tasdanlar.com',
            password_hash=generate_password_hash('password123'),
            role='admin',
            first_name='Admin',
            last_name='User',
            is_active=True
        )
        db.session.add(admin)

        moderator = User(
            username='moderator1',
            email='moderator@tasdanlar.com',
            password_hash=generate_password_hash('password123'),
            role='moderator',
            first_name='Moderator',
            last_name='User',
            is_active=True
        )
        db.session.add(moderator)

        driver = User(
            username='driver1',
            email='driver@tasdanlar.com',
            password_hash=generate_password_hash('password123'),
            role='driver',
            first_name='Driver',
            last_name='User',
            license_plate='34ABC123',
            is_active=True
        )
        db.session.add(driver)

        db.session.commit()
        print("Demo hesapları oluşturuldu!")
        
    # Uygulamayı başlat    
    app.run(host='0.0.0.0', port=5001, debug=True)
