from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
import os  # os is like a python class or dictionary that holds the environment variables of this appl in heroku server.
from passlib.hash import pbkdf2_sha256
from models import *
from models import Restaurant, Menu
from wtform_fields import *
from wtform_fields import EditMenuForm
from flask_login import LoginManager, login_user, current_user, login_required, logout_user

#------------------------------------------------------------------------------------------#


app = Flask(__name__)
bootstrap = Bootstrap(app)
app.debug = True

# Configure database
# NOTE: DATABASE_URL is an attribute or variable provided by heroku which fetches the actual value of the database url
app.config.update(

    # SECRET_KEY='whatever',
    SECRET_KEY=os.environ.get('SECRET'),
    # SQLALCHEMY_DATABASE_URI='postgresql://localhost/RestaurantMenusDB',
    SQLALCHEMY_DATABASE_URI=os.environ['DATABASE_URL'],
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)


db = SQLAlchemy(app)

# User Authentication: Configure flask login
login = LoginManager(app)
login.init_app(app)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# The "index()" method is the "Registration" method. So I could also name it "registration()".
@app.route("/", methods=['GET', 'POST'])
def index():
    reg_form = RegistrationForm()
    # Collect the "username" and "password" from the "RegistrationForm".
    # Update database if validation success.
    if reg_form.validate_on_submit():
        username = reg_form.username.data
        password = reg_form.password.data
        # Hash password
        hashed_pswd = pbkdf2_sha256.hash(password)

        # Check if the "username" exist using "Flask SQLAlchemy"
        # NOTE: The query below returns only one row(list) containing the "id", "username", & "password"
        # user_object = User.query.filter_by(username=username).first()

        # The if statement says that "user_object" already exist in the database table.
        # if user_object:
        #    return "Someone else has taken this username!"

        # Add the user to the database if "user_object" does not exist in the database table.
        # Also add the hashed password to the database.
        user = User(username=username, password=hashed_pswd)
        db.session.add(user)
        db.session.commit()

        flash('Registered successfully. Please login.', 'success')

        return redirect(url_for('login'))

    return render_template('index.html', form=reg_form)


@app.route("/login", methods=['GET', 'POST'])
def login():

    login_form = LoginForm()

    # Allow login if validation is successful
    if login_form.validate_on_submit():
        # "user_object" contains a one row list of "username" & "password". "login_user()" function logs in the user.
        user_object = User.query.filter_by(username=login_form.username.data).first()
        # user_object = User.query.filter_by(username=login_form.username.data).first()
        login_user(user_object)
        # if current_user.is_authenticated:
        # return "Logged in, finally!"
        # return redirect(url_for('chat')) #
        return redirect(url_for('display_menus'))
        # return "Not logged in"
    return render_template("login.html", form=login_form)
#-------------------------------------------------------------------------#

# display all the menus
@app.route('/display_menus', methods=['GET', 'POST'])
# @app.route('/display_menus')
def display_menus():
    menuses = Menu.query.all()
    # return 'home'
    return render_template('home.html', menus=menuses)

# "log out" the user
@app.route("/logout", methods=['GET'])
def logout():
    logout_user()
    flash('You have logged out successfully', 'success')
    # return "You are now logged out"
    return redirect(url_for('login'))

# Error handling
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# display all the restaurants specified by the user with the integer "restaurant_id".
@app.route('/display/restaurant/<restaurant_id>')
def display_restaurant(restaurant_id):
    restaurant = Restaurant.query.filter_by(id=restaurant_id).first()  # The first row with id=restaurant_id is passed to "restaurant"
    # All the rows with the Foreign Keys in "menus" table equal to the Primary Key value in the "restaurant" table are passed to "restaurant_menus"
    restaurant_menus = Menu.query.filter_by(res_id=restaurant.id).all()
    return render_template('restaurant.html', restaurant=restaurant, restaurant_menus=restaurant_menus)

# Gives the user the possibility of creating a new menu item and uploading its picture.
@app.route('/create/menu/<res_id>', methods=['GET', 'POST'])
def create_menu(res_id):
    if not current_user.is_authenticated:
        flash('Please login.', 'danger')
        return redirect(url_for('login'))
    form = CreateMenuForm()
    form.res_id.data = res_id  # pre-populates res_id box of the form.
    if form.validate_on_submit():
        # https://github.com/lepture/flask-wtf/blob/534e1734b86c2f0907af131c11b981e6146ca57c/docs/form.rst#file-uploads
        f = form.uploaded_photo.data  # File upload will work without this line.
        filename = secure_filename(f.filename)  # File upload will work without this line.
        f.save(os.path.join('static/uploaded_photo', filename))  # File upload will work without this line.

        # NOTE: picture=form.picture_url.data; "picture" is a field in the database class "Menu", while "picture_url" is a field
        #       in the "wtform_fields.py" under the "class CreateMenuForm(FlaskForm)"
        #       picture=form.picture_url.data
        menus = Menu(menu_name=form.menu_name.data, address=form.address.data, phone=form.phone.data,
                     price=form.price.data, picture=form.picture_url.data, res_id=form.res_id.data)  # picture=form.picture_url.data
        db.session.add(menus)
        db.session.commit()
        flash('Menu and contact details added successfully')
        return redirect(url_for('display_restaurant', restaurant_id=res_id))
        # return redirect(url_for('display_menus'))
    return render_template('create_menu.html', form=form, res_id=res_id)


# Edits menu name, address, phone, & price.
# "menu_id" is id of menu the user wants to edit.
@app.route('/edit/menu/<menu_id>', methods=['GET', 'POST'])
def edit_menu(menu_id):
    if not current_user.is_authenticated:
        flash('Please login.', 'danger')
        return redirect(url_for('login'))
    # This gives a list(only one row) of menu with given "id = menu_id"
    menu = Menu.query.get(menu_id)  # menu is a variable(list) that contains the menu row with the specified id called menu_id
    form = EditMenuForm(obj=menu)  # pass the columns of the menu list(one row) value to the form
    if form.validate_on_submit():
        menus.menu_name = form.menu_name.data  # menu_name entered by user in the form is stored in the database field.
        menus.address = form.address.data  # menus.address field of database accepts address entered by user in the form.
        menus.phone = form.phone.data  # menus.phone field of database accepts phone entered by user in the form.
        menus.price = form.price.data  # menus.price field of database accepts price entered by user in the form.
        db.session.add(menus)  # add the added properties to the database table called menus
        db.session.commit()  # save these properties
        flash('Menu deleted successfully')
        return redirect(url_for('display_menus'))
    return render_template('edit_menu.html', form=form)


# "menu_id" is the id of menu the user wants to delete.
# Deletes a given menu
@app.route('/menu/delete/<menu_id>', methods=['GET', 'POST'])
def delete_menu(menu_id):
    if not current_user.is_authenticated:
        flash('Please login.', 'danger')
        return redirect(url_for('login'))
    # This gives a list(only one row) of menu with given "id = menu_id"
    menu = Menu.query.get(menu_id)  # menu is a variable(single row list) that contains the menu row with the specified id called menu_id
    if request.method == 'POST':
        db.session.delete(menu)  # deletes the given row with id=menu_id
        db.session.commit()
        flash('Menu deleted successfully')
        return redirect(url_for('display_menus'))  # After deletion, send user back to home page.
    # NOTE: "menu_id=menu.id" returns only the "id" number of the "menu" row.
    return render_template('delete_menu.html', menu=menu, menu_id=menu.id)  # If it is a "GET" request rather, the delete.html page is displayed.


if __name__ == "__main__":
    app.run()
