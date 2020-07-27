from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
db = SQLAlchemy(app)

# Product Model
class Product(db.Model):
    __tablename__ = "Product"
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return "Product" + str(self.product_id)

# Location Model
class Location(db.Model):
    __tablename__ = "Location"
    location_id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return "Location" + str(self.location_id)

# Product Movement Model
class ProductMovement(db.Model):
    __tablename__ = "ProdutMovement"
    movement_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default =datetime.utcnow )
    from_location = db.Column(db.Integer,db.ForeignKey('Location.location_id'))
    to_location = db.Column(db.Integer,db.ForeignKey('Location.location_id'))
    product_id = db.Column(db.Integer,db.ForeignKey('Product.product_id'))
    qty = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "Product Movement" + str(self.movement_id)
    
# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Product View Page
@app.route('/product')
def view_product():
    return render_template('product.html', products=Product.query.all())

# Add New Products
@app.route('/product/add', methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form['product_name']
        db.session.add(Product(product_name=name))
        db.session.commit()
        return redirect('/product')
    else:
        return render_template('modify_product.html')    

# Edit Products
@app.route('/product/edit/<int:id>', methods=["GET","POST"])
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == "POST":
        product.product_name = request.form["product_name"]
        db.session.commit()
        return redirect("/product")
    else:
        return render_template('modify_product.html', product=product)

# Delete Products
@app.route('/product/delete/<int:id>', methods=["GET","POST"])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect('/product')

# View Locations Page
@app.route('/location')
def location():
    return render_template('location.html',locations=Location.query.all())

# Add Locations
@app.route('/location/add', methods=["GET", "POST"])
def add_location():
    if request.method == "POST":
        name = request.form['location_name']
        db.session.add(Location(location_name=name))
        db.session.commit()
        return redirect('/location')
    else:
        return render_template('modify_location.html')    

# Edit Locations
@app.route('/location/edit/<int:id>', methods=["GET","POST"])
def edit_location(id):
    location = Location.query.get_or_404(id)
    if request.method == "POST":
        location.location_name = request.form["location_name"]
        db.session.commit()
        return redirect("/location")
    else:
        return render_template('modify_location.html', location=location)

# Delete Locations
@app.route('/location/delete/<int:id>', methods=["GET","POST"])
def delete_location(id):
    location = Location.query.get_or_404(id)
    db.session.delete(location)
    db.session.commit()
    return redirect('/location')

# View Product Movements
@app.route('/product-movement')
def product_movement():
    movements = ProductMovement.query.all()

    # Get the From Location, To Location and Product name
    for movement in movements:
        from_query = db.session.query(Location).filter(Location.location_id == movement.from_location)
        for row in from_query:
            movement.from_location = row.location_name
        to_query = db.session.query(Location).filter(Location.location_id == movement.to_location)
        for row in to_query:
            movement.to_location = row.location_name
        product_query = db.session.query(Product).filter(Product.product_id == movement.product_id)
        for row in product_query:
            movement.product_id = row.product_name
    return render_template('product_movement.html', movements=movements)

# Add Product Movements
@app.route('/product-movement/add', methods=["GET", "POST"])
def add_product_movement():
    if request.method == "POST":
        from_location = request.form['from_location']
        to_location = request.form["to_location"]
        product_id = request.form["product_id"]
        qty = request.form["qty"]
        db.session.add(ProductMovement(from_location=from_location, to_location=to_location, product_id=product_id, qty=qty ))
        db.session.commit()
        return redirect('/product-movement')
    else:
        return render_template('modify_product_movement.html', products=Product.query.all(), locations=Location.query.all())    

# Edit Product Movement
@app.route('/product-movement/edit/<int:id>', methods=["GET","POST"])
def edit_product_movement(id):
    movement = ProductMovement.query.get_or_404(id)
    if request.method == "POST":
        movement.from_location = request.form['from_location']
        movement.to_location = request.form["to_location"]
        movement.product_id = request.form["product_id"]
        movement.qty = request.form["qty"]
        db.session.commit()
        return redirect("/product-movement")
    else:
        return render_template('modify_product_movement.html', movement=movement, locations=Location.query.all(), products = Product.query.all())

# Delete Produt Movement
@app.route('/product-movement/delete/<int:id>', methods=["GET","POST"])
def delete_product_movement(id):
    movement = ProductMovement.query.get_or_404(id)
    db.session.delete(movement)
    db.session.commit()
    return redirect('/product-movement')

# Inventory Report
@app.route('/report')
def generate_report():
    report = []
    movements = ProductMovement.query.all()
    for movement in movements:
        from_location = ''
        to_location = ''
        product_id = ''

        # Get the From Location, To Location and Product name
        from_query = db.session.query(Location).filter(Location.location_id == movement.from_location)
        for row in from_query:
            from_location = row.location_name
        to_query = db.session.query(Location).filter(Location.location_id == movement.to_location)
        for row in to_query:
            to_location = row.location_name
        product_query = db.session.query(Product).filter(Product.product_id == movement.product_id)
        for row in product_query:
            product_id = row.product_name

        # Check if From Location is present in the report and From Location has the product then reduce the mentioned quantity of that product 
        if from_location:
            fromLocationFoundInReport = False
            for item in report:
                if(from_location in item):
                    fromLocationFoundInReport = True
                    itemsInFromLocation = item[from_location]
                    if(product_id in itemsInFromLocation):
                        itemsInFromLocation[product_id] = itemsInFromLocation[product_id] - movement.qty
                    else:
                        itemsInFromLocation[product_id] = -movement.qty
            if fromLocationFoundInReport == False:
                report.append({
                    from_location : {
                        product_id : -movement.qty
                    }
                })


        # Check if To Location is present in the report and To Location has the product then add the mentioned quantity to that product
        if to_location:
            toLocationFoundInReport = False
            for item in report:
                if(to_location in item):
                    toLocationFoundInReport = True
                    itemsInToLocation = item[to_location]
                    if(product_id in itemsInToLocation):
                        itemsInToLocation[product_id] = itemsInToLocation[product_id] + movement.qty
                    else:
                        itemsInToLocation[product_id] = movement.qty
        # If To Location was not present in the report already add it to the report with that product and quantity                
            if toLocationFoundInReport == False:
                report.append({
                    to_location : {
                        product_id : movement.qty
                    }
                })     

    return render_template("report.html", report=report)


if __name__ == "__main__":
    app.run(debug=True)