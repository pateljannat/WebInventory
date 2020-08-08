from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime, timezone

app = Flask(__name__)
app.secret_key = '_5#y2L"F4Q8z\n\xec]/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
db = SQLAlchemy(app)

# Product Model
class Product(db.Model):
    __tablename__ = "Product"
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return "Product " + str(self.product_id)

# Location Model
class Location(db.Model):
    __tablename__ = "Location"
    location_id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return "Location " + str(self.location_id)

# Product Movement Model
class ProductMovement(db.Model):
    __tablename__ = "ProdutMovement"
    movement_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default =datetime.utcnow )
    from_location = db.Column(db.Integer, db.ForeignKey('Location.location_id'))
    to_location = db.Column(db.Integer,db.ForeignKey('Location.location_id'))
    product_id = db.Column(db.Integer,db.ForeignKey('Product.product_id'))
    from_location_ref = db.relationship("Location",foreign_keys=[from_location])
    to_location_ref = db.relationship("Location",foreign_keys=[to_location])
    product_ref = db.relationship("Product", foreign_keys=[product_id])
    qty = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "Product Movement " + str(self.movement_id)
    
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
        movement.from_location = getLocationName(movement.from_location)
        movement.to_location = getLocationName(movement.to_location)
        movement.product_id = getProductName(movement.product_id)
    return render_template('product_movement.html', movements=movements)

# Add Product Movements
@app.route('/product-movement/add', methods=["GET", "POST"])
def add_product_movement():
    if request.method == "POST":
        from_location = request.form['from_location']
        to_location = request.form["to_location"]
        product_id = request.form["product_id"]
        qty = int(request.form["qty"])
        result = checkStock(from_location, product_id, qty)
        if result != True:
            displayMessage(result)
            return redirect('/product-movement')
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
        from_location = request.form['from_location']
        to_location = request.form["to_location"]
        product_id = request.form["product_id"]
        qty = int(request.form["qty"])
        result = checkStock(from_location, product_id, qty)
        if result != True:
            displayMessage(result)
            return redirect('/product-movement')
        movement.from_location = from_location
        movement.to_location = to_location
        movement.product_id = product_id
        movement.qty = qty
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

# Generates report
def report_data(location, product):
    report = {}
    if location:
        movements = ProductMovement.query.filter((ProductMovement.from_location == location) | (ProductMovement.to_location == location ))
    else:
        movements = ProductMovement.query.all()
    for movement in movements:
        # Get the From Location, To Location and Product name
        movementProcessed = getMovementData(movement)
        locationCheck = location and location != "null" 
        productCheck = product and int(product) == movement.product_id
        # Check if From Location is present in the report and From Location has the product then reduce the mentioned quantity of that product 
        if ((locationCheck and int(location) == movement.from_location and productCheck) or not location):
            if movementProcessed["from_location"]:
                computeReportForLocation(movementProcessed, report, "subtract")
        # Check if To Location is present in the report and To Location has the product then add the mentioned quantity to that product
        if ((locationCheck  and int(location) == movement.to_location and productCheck) or not location):
            if movementProcessed["to_location"]:
                computeReportForLocation(movementProcessed, report, "add")
    return report   

# Display Inventory Report
@app.route('/report')
def generate_report():
    report = report_data(False, False)
    return render_template("report.html", report=report)

# Returns Location name
def getLocationName(location_id):
    location = Location.query.filter_by(location_id = location_id).first()
    return location.location_name if location else location

#Returns Product name
def getProductName(product_id):
    product = Product.query.filter_by(product_id = product_id).first()
    return product.product_name if product else product

# Returns movement information
def getMovementData(movement):
    movementData = {
        "from_location" : getLocationName(movement.from_location),
        "to_location": getLocationName(movement.to_location),
        "product_id" : getProductName(movement.product_id),
        "qty": movement.qty
    }
    return movementData

# Performs quantity update if location is present in report
def getLocationItems(location, movement, report, operation):
    if location in report:
        return calculateQuantity(report[location], movement, operation)
    return

def calculateQuantity(locationData, movement, operation):
    if movement["product_id"] in locationData:
            locationData[movement["product_id"]] = locationData[movement["product_id"]] - movement["qty"] if operation == "subtract" else locationData[movement["product_id"]] + movement["qty"]
    else:
        locationData[movement["product_id"]] =  - movement["qty"] if operation == "subtract" else movement["qty"]
    return locationData

# Adds location information to report if not already present
def addLocationDataToReport(movement, report, operation):
    if operation == "subtract":
        report[movement["from_location"]] = {
            movement["product_id"]: -movement["qty"]
        }
    else:
        report[movement["to_location"]] = {
            movement["product_id"]: movement["qty"]
        }

# Generates location information for report
def computeReportForLocation(movement, report, operation):
    location = movement["from_location"] if operation == "subtract" else movement["to_location"]
    itemsInLocation = getLocationItems(location, movement, report, operation)
    if not itemsInLocation:
        addLocationDataToReport(movement, report, operation)

# Checks if a product is present in a location and its quantity in that location
def checkStock(location, product, qty):
    report = report_data(location, product)
    location = getLocationName(location)
    product = getProductName(product)
    if location in report:
        locationData = report[location]
        if product in locationData:
            return True if locationData[product] >= qty else {"value": locationData[product], "product": product, "location": location}
        else: 
            return { "value" : False, "product": product, "location": location}
    elif not location:
        return True
    else: 
        return { "value" : False, "product": product, "location": location }

# Displays flash messages
def displayMessage(result):
    if not result["value"]:
        message = "Sorry " + result["product"] + " is not available in " + result["location"] 
        flash(message, 'error')
    else:
        message = "Sorry only " + str(result["value"]) + " " + (result["product"]) + " is available in " + (result["location"]) 
        flash(message, 'error')


if __name__ == "__main__":
    app.run(debug=True)