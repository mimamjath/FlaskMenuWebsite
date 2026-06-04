from flask import Flask, render_template, request, redirect, url_for, flash, session
import firebase_admin
from firebase_admin import credentials, db
import os
from werkzeug.utils import secure_filename
from PIL import Image


app = Flask(__name__)
app.secret_key = "amanwebsite"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
FIXED_SIZE = (1507, 1595)  # Set the fixed size (width, height)

# Initialize Firebase
#cred = credentials.Certificate("firebase_credentials.json")
#firebase_admin.initialize_app(cred, {
    #'databaseURL': 'https://aman-f7b63-default-rtdb.firebaseio.com/'
#})

cred = credentials.Certificate({
    "type": "service_account",
    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
})

firebase_admin.initialize_app(cred, {
    "databaseURL": os.environ.get("FIREBASE_DB_URL")
})

menu_ref = db.reference('menu')
categories_ref = db.reference('categories')
users_ref = db.reference('users')

@app.route('/')
def menu():
    categories = categories_ref.get() or {}  
    menu_items = menu_ref.get() or {}  
    return render_template("menu.html", categories=categories, menu_items=menu_items)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))

    # your existing admin code here
    if request.method == 'POST':
        if 'add_category' in request.form:
            category_name = request.form['category_name']
            categories_ref.push({'name': category_name})
            flash("Category added successfully!", "success")

        else:
            name_en = request.form['name_en']
            name_ar = request.form['name_ar']
            description = request.form['description']
            description_ar = request.form['description_ar']
            price = request.form['price']
            category = request.form['category']
            image = request.files['image']

            image_url = ''

            if image and image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # Open + resize image properly
                with Image.open(image) as img:
                    img = img.convert("RGB")
                    img = img.resize(FIXED_SIZE, Image.Resampling.LANCZOS)
                    img.save(image_path)

                image_url = f'static/uploads/{filename}'


            menu_ref.push({
                'name_en': name_en,
                'name_ar': name_ar,
                'description': description,
                'description_ar': description_ar,
                'price': price,
                'category': category,
                'image': image_url
            })
        flash("Menu item added successfully!", "success")

        return redirect(url_for('admin'))
    

    categories = categories_ref.get() or {}
    menu_items = menu_ref.get() or {}
    return render_template('admin.html', categories=categories, menu_items=menu_items)

@app.route('/edit/<item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    item = menu_ref.child(item_id).get()
    if request.method == 'POST':
        name_en = request.form['name_en']
        name_ar = request.form['name_ar']
        description = request.form['description']
        description_ar = request.form['description_ar']
        price = request.form['price']
        category = request.form['category']
        image = request.files['image']
        
        image_url = item.get('image', '')  # Keep existing image if not replaced
        if image and image.filename:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = f'static/uploads/{filename}'

        menu_ref.child(item_id).update({
            'name_en': name_en,
            'name_ar': name_ar,
            'description': description,
            'description_ar': description_ar,
            'price': price,
            'category': category,
            'image': image_url
        })
        flash("Item updated successfully!", "success")
        return redirect(url_for('admin'))
    
    categories = categories_ref.get() or {}
    return render_template('edit.html', item=item, item_id=item_id, categories=categories)


@app.route('/delete/<item_id>')
def delete_item(item_id):
    menu_ref.child(item_id).delete()
    flash("Item deleted successfully!", "danger")
    return redirect(url_for('admin'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = users_ref.get() or {}

        for key, user in users.items():
            if user.get('username') == username and user.get('password') == password:
                session['admin'] = True
                session['username'] = username
                return redirect(url_for('admin'))

        flash("Invalid username or password", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    #app.run(debug=True)
    app.run()
