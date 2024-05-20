from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)


app.config["MONGO_URI"] = "mongodb://localhost:27017/yourdbname"
app.config["SECRET_KEY"] = "asdasd123231qwe"
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Ensure the upload folder exists
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id
        self.user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    @property
    def username(self):
        return self.user_data.get("username")
# =======================================================-- register --===================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        mongo.db.users.insert_one({"username": username, "password": hashed_password})
        flash("Registration successful!", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# ======================================================--login--============================================================

@app.route('/', methods=['GET', 'POST'])

def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = mongo.db.users.find_one({"username": username})
        if user and bcrypt.check_password_hash(user['password'], password):
            user_obj = User(str(user["_id"]))
            login_user(user_obj)
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", "error")
    return render_template('login.html')

#===============================-- this is the basic logout function-- ==========================
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

#============================-- here all the product will be shown --========================
# this is homepage of the website
# which is name as INDEX

@app.route('/index')
def index():
    products = mongo.db.products.find()
    return render_template('index.html', products=products)

#======================-- new product can be add but only by the seller --======================

@app.route('/add', methods=['POST'])
@login_required
def add_product():
    name = request.form['name']
    price = request.form['price']
    description = request.form['description']
    image = request.files['image']

    if name and price:
        filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        product = {
            'name': name,
            'price': price,
            'description': description,
            'image': filename,
            'seller': current_user.username
        }
        mongo.db.products.insert_one(product)
        flash("Product added successfully!", "success")
    else:
        flash("Name and Price are required.", "error")

    return redirect(url_for('index'))

#======================-- here the seller can remove the product  from the home page--====================
    
@app.route('/delete/<id>', methods=['POST'])

@login_required
def delete_product(id):
    product = mongo.db.products.find_one({"_id": ObjectId(id)})
    if product and 'image' in product and product['image']:
        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], product['image']))
    
    mongo.db.products.delete_one({"_id": ObjectId(id)})
    flash("Product deleted successfully!", "success")
    return redirect(url_for('index'))

#======================-- with this product will be update with it's ID --===================

@app.route('/update/<id>', methods=['POST'])
@login_required
def update_product(id):
    name = request.form['name']
    price = request.form['price']
    description = request.form['description']
    image = request.files['image']

    update_data = {}
    if name:
        update_data['name'] = name
    if price:
        update_data['price'] = price
    if description:
        update_data['description'] = description
    
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        update_data['image'] = filename

        # Remove old image file
        product = mongo.db.products.find_one({"_id": ObjectId(id)})
        if product and 'image' in product and product['image']:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], product['image']))

    if update_data:
        mongo.db.products.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        flash("Product updated successfully!", "success")
    else:
        flash("No updates provided.", "error")
    
    return redirect(url_for('index'))

#===============================-- basic --======================
if __name__ == '__main__':
    app.run(debug=True)
