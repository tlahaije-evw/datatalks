from werkzeug.security import generate_password_hash
import os

def seed_data(db, User, Dataset):
    basedir = os.path.abspath(os.path.dirname(__file__))
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        print('Admin niet gevonden')
        admin = User(
            username='admin',
            password=generate_password_hash('admin'),
            firstname='Admin',
            lastname='User',
            email='admin@example.com'
        )
        user1 = User(
            username='john',
            password=generate_password_hash('1234'),
            firstname='John',
            lastname='Doe',
            email='john@example.com'
        )
        dataset1 = Dataset(
            name="DAF KPI's",
            path=f'{basedir}\Datasets\daf-data.xlsx' 
        )
        db.session.add(admin)
        db.session.add(user1)
        db.session.add(dataset1)
        db.session.commit()
    else:
        print('Admin gevonden')