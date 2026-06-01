from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, db
import os
from werkzeug.utils import secure_filename
from PIL import Image


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
FIXED_SIZE = (1507, 1595)  # Set the fixed size (width, height)

# Initialize Firebase
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://aman-f7b63-default-rtdb.firebaseio.com/'
})

menu_ref = db.reference('menu')
categories_ref = db.reference('categories')

@app.route('/')
def menu():
    categories = categories_ref.get() or {}  
    menu_items = menu_ref.get() or {}  
    return render_template("menu.html", categories=categories, menu_items=menu_items)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if 'add_category' in request.form:
            category_name = request.form['category_name']
            categories_ref.push({'name': category_name})

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

                 # Open the image and resize
                image = Image.open(image)
                image = Image.resize(FIXED_SIZE, Image.ANTIALIAS)

                image.save(image_path)
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
        return redirect(url_for('admin'))
    
    categories = categories_ref.get() or {}
    return render_template('edit.html', item=item, item_id=item_id, categories=categories)


@app.route('/delete/<item_id>')
def delete_item(item_id):
    menu_ref.child(item_id).delete()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=80)
