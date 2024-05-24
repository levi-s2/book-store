from flask import Flask, jsonify, request, make_response
from flask_migrate import Migrate
from flask_cors import CORS
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, bcrypt, User, Book, Review, Genre, user_books
import os
import traceback

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Change this in a real app

migrate = Migrate(app, db)
db.init_app(app)
bcrypt.init_app(app)
api = Api(app)
CORS(app)
jwt = JWTManager(app)

class Home(Resource):
    def get(self):
        response_dict = {"message": "Book store API"}
        response = make_response(response_dict, 200)
        return response

api.add_resource(Home, '/')

class Books(Resource):
    def get(self):
        response_dict_list = [book.to_dict() for book in Book.query.all()]
        response = make_response(response_dict_list, 200)
        return response

api.add_resource(Books, '/books')

class BookDetail(Resource):
    def get(self, book_id):
        book = Book.query.get(book_id)
        if book:
            return make_response(jsonify(book.to_dict()), 200)
        else:
            return make_response(jsonify({"message": "Book not found"}), 404)

api.add_resource(BookDetail, '/books/<int:book_id>')

class Register(Resource):
    def post(self):
        try:
            data = request.get_json()
            print('Received registration data:', data)

            name = data.get('name')
            password = data.get('password')
            print(f'Name: {name}, Password: {password}')

            if not name or not password:
                print('Name or password not provided')
                return {"message": "Name and password are required"}, 400

            existing_user = User.query.filter_by(name=name).first()
            if existing_user:
                print('User already exists')
                return {"message": "User already exists"}, 400

            new_user = User(name=name)
            new_user.password_hash = password  # Use the password_hash property to hash the password
            print(f'New user created: {new_user}')

            db.session.add(new_user)
            db.session.commit()
            print('User committed to the database')

            return {"message": "User created successfully"}, 201
        except Exception as e:
            print(f"Error during registration: {e}")
            traceback.print_exc()
            return {"message": "Internal Server Error"}, 500

class Login(Resource):
    def post(self):
        try:
            data = request.get_json()
            name = data.get('name')
            password = data.get('password')

            user = User.query.filter_by(name=name).first()
            if not user or not user.authenticate(password):
                return {"message": "Invalid username or password"}, 401

            access_token = create_access_token(identity=user.id)
            return {"access_token": access_token}, 200
        except Exception as e:
            print(f"Error during login: {e}")
            traceback.print_exc()
            return {"message": "Internal Server Error"}, 500

class Protected(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        return {"name": user.name}, 200

api.add_resource(Register, '/register', endpoint='register_endpoint')
api.add_resource(Login, '/login', endpoint='login_endpoint')
api.add_resource(Protected, '/protected', endpoint='protected_endpoint')

class UserBooks(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        user_books = [book.to_dict() for book in user.books]
        return make_response(jsonify(user_books), 200)

    @jwt_required()
    def post(self):
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            book_id = data.get('bookId')
            user = User.query.get(user_id)
            book = Book.query.get(book_id)

            if book in user.books:
                return make_response({"message": "Book already in list"}, 400)

            user.books.append(book)
            db.session.commit()

            return make_response({"message": "Book added to list"}, 201)
        except Exception as e:
            traceback.print_exc()
            return make_response({"message": "Internal Server Error"}, 500)

    @jwt_required()
    def delete(self, book_id):
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            book = Book.query.get(book_id)

            if book not in user.books:
                return make_response({"message": "Book not in list"}, 400)

            user.books.remove(book)
            db.session.commit()

            return make_response({"message": "Book removed from list"}, 200)
        except Exception as e:
            traceback.print_exc()
            return make_response({"message": "Internal Server Error"}, 500)

api.add_resource(UserBooks, '/user/books', '/user/books/<int:book_id>')


class Reviews(Resource):
    @jwt_required()
    def post(self):
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            book_id = data.get('book_id')
            review_body = data.get('review')

            user = User.query.get(user_id)
            book = Book.query.get(book_id)

            if not book:
                return {"message": "Book not found"}, 404

            new_review = Review(body=review_body, user_id=user.id, book_id=book.id)
            db.session.add(new_review)
            db.session.commit()

            return {"message": "Review added successfully"}, 201
        except Exception as e:
            traceback.print_exc()
            return {"message": "Internal Server Error"}, 500

api.add_resource(Reviews, '/reviews')


class UserReviews(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        user_reviews = [{
            "id": review.id,
            "body": review.body,
            "book": {
                "id": review.book.id,
                "title": review.book.title
            }
        } for review in user.reviews]
        return make_response(jsonify(user_reviews), 200)

api.add_resource(UserReviews, '/user/reviews')

if __name__ == '__main__':
    app.run(debug=True)