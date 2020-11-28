import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from datetime import datetime
from pytz import timezone

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# methods for use by jinja
def getname(_):
    return db.execute("SELECT username FROM users WHERE id = :id", {"id": session["user_id"]}).fetchall()[0]["username"]


def getcash(_):
    return db.execute("SELECT cash FROM users WHERE id = :id", {"id": session["user_id"]}).fetchall()[0]["cash"]


# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["lookup"] = lookup
app.jinja_env.filters["getname"] = getname
app.jinja_env.filters["getcash"] = getcash

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect to stocks.db sqlite database
engine = create_engine(environ.get('DATABASE_URL') or 'sqlite:///stocks.db')  # database engine object from SQLAlchemy that manages connections to the database
db = scoped_session(sessionmaker(bind=engine))  # ensures different users' interactions are separate

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/", methods=["GET"])
@login_required
def index():
    """Show portfolio of stocks"""
    if request.args.get("xhr") == "true":
        temp_stocks = db.execute("SELECT symbol, SUM(quantity) FROM transactions WHERE person_id = :person_id GROUP BY symbol", {"person_id": session["user_id"]}).fetchall()
        stocks = []
        for stock in temp_stocks:
            if stock["SUM(quantity)"] > 0:
                stocks.append({"symbol": stock["symbol"], "shares": stock["SUM(quantity)"]})
        cash = db.execute("SELECT cash FROM users WHERE id = :id", {"id": session["user_id"]}).fetchall()[0]["cash"]
        total = 0
        for stock in stocks:
            stock_info = lookup(stock["symbol"])
            # Make sure request succeeded
            if not stock_info:
                return jsonify({"success": False})
            price = stock_info["price"]
            stock["name"] = stock_info["name"]
            stock["priceRaw"] = price
            stock["price"] = usd(price)
            subtotal = stock["shares"] * price
            stock["subtotal"] = usd(subtotal)
            total += subtotal
        # If all requests succeeded
        return jsonify({"success": True, "stocks": stocks, "cash": usd(cash), "total": usd(total + cash)})
            
    else:
        return render_template("index.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == 'POST':
        # Initial POST, inputted symbol & shares
        if request.form.get("symbol1") is None:
            symbol = request.form.get("symbol").upper()
            shares = request.form.get("shares")
            stock_info = lookup(symbol)
            if not symbol:
                return apology("must provide symbol", 403)
            elif not shares:
                return apology("must provide number of shares", 403)
            elif not stock_info:
                return apology("invalid stock symbol", 403)
            elif int(shares) <= 0:
                return apology("shares must be greater than 0", 403)
            elif db.execute("SELECT cash FROM users WHERE id = :id", {"id": session["user_id"]}).fetchall()[0]["cash"] < stock_info["price"] * int(shares):
                return apology("insufficient amount of money", 403)
            return render_template("confirmation.html", action='Buying:', symbol=symbol, name=stock_info["name"], shares=int(shares), price=stock_info["price"])
        # Confirmation POST, clicked Confirm button
        else:
            symbol = request.form.get("symbol1")
            shares = request.form.get("shares")
            time = datetime.now(timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S")
            price = lookup(symbol)["price"]
            if db.execute("SELECT cash FROM users WHERE id = :id", {"id": session["user_id"]}).fetchall()[0]["cash"] < price * int(shares):
                return apology("insufficient amount of money", 403)
            db.execute("INSERT INTO transactions (person_id, symbol, quantity, price, time) VALUES(:person_id, :symbol, :quantity, :price, :time)", {"person_id": session["user_id"], "symbol": symbol, "quantity": int(shares), "price": price, "time": time})
            db.execute("UPDATE users SET cash = cash - :amount WHERE id = :id", {"amount": price * int(shares), "id": session["user_id"]})
            db.commit()
            flash('Successful Transaction!')
            return redirect(url_for("index"))
    else:
        return render_template("buy.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # Initial POST, inputted symbol & shares
        if request.form.get("symbol1") is None:
            symbol = request.form.get("symbol")
            shares = request.form.get("shares")
            if not symbol:
                return apology("must provide symbol", 403)
            stock_info = lookup(symbol)
            if not shares:
                return apology("must provide number of shares", 403)
            elif not stock_info:
                return apology("invalid stock symbol", 403)
            elif int(shares) <= 0:
                return apology("shares must be greater than 0", 403)
            elif db.execute("SELECT SUM(quantity) FROM transactions WHERE person_id = :person_id AND symbol = :symbol GROUP BY symbol", {"person_id": session["user_id"], "symbol": symbol}).fetchall()[0]["SUM(quantity)"] < int(shares):
                return apology("insufficient shares", 403)
            return render_template("confirmation.html", action='Selling:', symbol=symbol, name=stock_info["name"], shares=int(shares), price=stock_info["price"])#TODO
        # Confirmation POST, clicked Confirm button
        else:
            symbol = request.form.get("symbol1")
            shares = request.form.get("shares")
            time = datetime.now(timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S")
            price = lookup(symbol)["price"]
            if db.execute("SELECT SUM(quantity) FROM transactions WHERE person_id = :person_id AND symbol = :symbol GROUP BY symbol", {"person_id": session["user_id"], "symbol": symbol}).fetchall()[0]["SUM(quantity)"] < int(shares):
                return apology("insufficient shares", 403)
            db.execute("INSERT INTO transactions (person_id, symbol, quantity, price, time) VALUES(:person_id, :symbol, :quantity, :price, :time)", {"person_id": session["user_id"], "symbol": symbol, "quantity": -int(shares), "price": price, "time": time})
            db.execute("UPDATE users SET cash = cash + :amount WHERE id = :id", {"amount": price * int(shares), "id": session["user_id"]})
            db.commit()
            flash('Successful Transaction!')
            return redirect(url_for("index"))
    else:
        return render_template("sell.html", stocks=db.execute("SELECT symbol, SUM(quantity) FROM transactions WHERE person_id = :person_id GROUP BY symbol", {"person_id": session["user_id"]}).fetchall())


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return render_template("history.html", transactions=db.execute("SELECT symbol, quantity, price, time FROM transactions WHERE person_id = :person_id ORDER BY time", {"person_id": session["user_id"]}).fetchall())


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
    
        # Query database for username
        rows = db.execute("SELECT id, hash FROM users WHERE username = :username", {"username": request.form.get("username")}).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/stocks")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Temporary "easy login" code
        if request.args.get("user") and request.args.get("pass"):
            rows = db.execute("SELECT id, hash FROM users WHERE username = :username", {"username": request.args.get("user")}).fetchall()
    
            # Ensure username exists and password is correct
            if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.args.get("pass")):
                return apology("invalid username and/or password", 403)
    
            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]
    
            # Redirect user to home page
            return redirect("/stocks")
        
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/stocks/login")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        stocks = []
        for i in range(int(request.form.get("len"))):
            temp_dict = {}
            stock_info = lookup(request.form.get(str(i)))
            # Make sure request succeeded
            if not stock_info:
                return jsonify({"success": False})
            temp_dict["name"] = stock_info["name"]
            temp_dict["price"] = usd(stock_info["price"])
            temp_dict["symbol"] = request.form.get(str(i))
            stocks.append(temp_dict)
        # If all requests succeeded
        return jsonify({"success": True, "stocks": stocks})
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation", 403)
        elif len(db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchall()) != 0:
            return apology("username already exists", 403)
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)
        hashe = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", {"username": username, "hash": hashe})
        db.commit()
        session.clear()
        session["user_id"] = db.execute("SELECT id FROM users WHERE username = :username", {"username": username}).fetchall()[0]["id"]
        flash('Registered!')
        return redirect("/stocks")
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
