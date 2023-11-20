import datetime
import emoji

from cs50 import SQL
from flask import Flask, redirect, render_template, jsonify, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Configure application
app = Flask(__name__)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show Dashboard"""

    user_id = session["user_id"]

    # Get the current date
    current_date = datetime.date.today()
    formatted_date = current_date.strftime("%Y-%m-%d")
    current_month = current_date.strftime("%m")

    # Welcome page for new users
    if (
        db.execute("SELECT COUNT(*) FROM blobs WHERE user_id = (?);", user_id)[0][
            "COUNT(*)"
        ]
        == 0
    ):
        name = db.execute("SELECT username FROM users WHERE id = (?);", user_id)[0][
            "username"
        ]
        return render_template("welcome.html", name=name)

    # reset INCOME and EXPENSES to 0 at the beginning of the new month
    if (
        db.execute("SELECT COUNT(*) FROM transactions WHERE user_id = (?);", user_id)[
            0
        ]["COUNT(*)"]
        > 0
    ):
        if (
            current_month
            != db.execute(
                "SELECT strftime('%m', date) AS last_month FROM transactions JOIN date ON transactions.transaction_date = date.id WHERE user_id = (?) ORDER BY date.id DESC LIMIT 1;",
                user_id,
            )[0]["last_month"]
        ):
            db.execute(
                "UPDATE blobs SET money = 0 WHERE user_id = (?) AND type_id IN (SELECT id FROM type WHERE type = 'income' OR type = 'expenses');",
                user_id,
            )

    # Check if the current date is already in the database
    if not db.execute("SELECT * FROM date WHERE date = (?);", formatted_date):
        db.execute("INSERT INTO date (date) VALUES (?);", formatted_date)

    # INCOME - money, type, currency
    income = db.execute(
        "SELECT blob_name, money, type, emoji FROM blobs JOIN users ON blobs.user_id = users.id JOIN type ON blobs.type_id = type.id WHERE users.id = (?) AND type = 'income';",
        user_id,
    )

    # ACCOUNTS - money, type, currency
    account = db.execute(
        "SELECT blob_name, money, type, emoji FROM blobs JOIN users ON blobs.user_id = users.id JOIN type ON blobs.type_id = type.id WHERE users.id = (?) AND type = 'account';",
        user_id,
    )

    # EXPENSES - money, type, currency
    expenses = db.execute(
        "SELECT blob_name, money, type, emoji FROM blobs JOIN users ON blobs.user_id = users.id JOIN type ON blobs.type_id = type.id WHERE users.id = (?) AND type = 'expenses';",
        user_id,
    )

    # getting currency symbol
    currency = db.execute(
        "SELECT currency FROM currency JOIN users ON users.currency_id = currency.id WHERE users.id = (?);",
        user_id,
    )[0]["currency"]

    # getting lists of blobs for select menu
    income_account = income + account

    received = round((sum(item["money"] for item in income)), 2)
    balance = round((sum(item["money"] for item in account)), 2)
    spent = round((sum(item["money"] for item in expenses)), 2)

    transactions_today = db.execute(
        "SELECT from_blobs.emoji AS from_emoji, to_blobs.emoji AS to_emoji, from_blobs.blob_name AS fromm, to_blobs.blob_name AS too, amount, date.date AS transaction_date, transactions.id FROM transactions JOIN blobs AS from_blobs ON transactions.from_blob = from_blobs.id JOIN blobs AS to_blobs ON transactions.to_blob = to_blobs.id JOIN date ON transactions.transaction_date = date.id WHERE transactions.user_id = (?) AND date = DATE('now') ORDER BY transactions.id DESC;",
        user_id,
    )

    expenses_today = db.execute(
        "SELECT amount FROM transactions JOIN date ON transactions.transaction_date = date.id JOIN blobs ON transactions.to_blob = blobs.id JOIN type ON blobs.type_id = type.id WHERE transactions.user_id = (?) AND date.date = DATE('now') AND transactions.amount < 0 AND type = 'expenses';",
        user_id,
    )
    spent_today = round((abs(sum(item["amount"] for item in expenses_today))), 2)

    return render_template(
        "index.html",
        income=income,
        account=account,
        expenses=expenses,
        currency=currency,
        income_account=income_account,
        received=received,
        balance=balance,
        spent=spent,
        transactions_today=transactions_today,
        spent_today=spent_today,
    )


@app.route("/add_item", methods=["GET", "POST"])
@login_required
def add_item():
    """Add Item"""

    user_id = session["user_id"]

    list = db.execute(
        "SELECT emoji, type FROM blobs JOIN type ON blobs.type_id = type.id WHERE user_id = (?) GROUP BY type ORDER BY CASE WHEN type = 'income' THEN 1 WHEN type = 'account' THEN 2 ELSE 3 END;",
        user_id,
    )

    if len(list) == 3:
        type_list = list

    else:
        type_list = db.execute("SELECT type FROM type;")

    if request.method == "POST":
        name = request.form.get("name")
        type = request.form.get("type")

        if not (name and type):
            must = "All fields must be filled"
            return render_template("add_item.html", type_list=type_list, must=must)

        elif db.execute(
            "SELECT blob_name FROM blobs WHERE user_id = (?) AND blob_name = (?);",
            user_id,
            name,
        ):
            must = "This name already exists"
            return render_template("add_item.html", type_list=type_list, must=must)

        elif " " in name:
            must = "Sorry, you can't use spaces"
            return render_template("add_item.html", type_list=type_list, must=must)

        else:
            # Get the current date
            current_date = datetime.date.today()
            formatted_date = current_date.strftime("%Y-%m-%d")

            # Check if the current date is already in the database
            if not db.execute("SELECT * FROM date WHERE date = (?);", formatted_date):
                db.execute("INSERT INTO date (date) VALUES (?);", formatted_date)

            type_id = (db.execute("SELECT id FROM type WHERE type = (?);", type))[0][
                "id"
            ]

            type_emoji = db.execute(
                "SELECT emoji FROM blobs WHERE user_id = (?) AND type_id = (?) GROUP BY 'emoji';",
                user_id,
                type_id,
            )
            if type_emoji:
                type_emoji = type_emoji[0]["emoji"]
            else:
                if type == "income":
                    type_emoji = "💰"
                elif type == "account":
                    type_emoji = "💼"
                else:
                    type_emoji = "🛒"

            db.execute(
                "INSERT INTO blobs (blob_name, user_id, type_id, date_id, emoji) VALUES (?, ?, ?, ?, ?);",
                name,
                user_id,
                type_id,
                (db.execute("SELECT id FROM date WHERE date = (?);", formatted_date))[
                    0
                ]["id"],
                type_emoji,
            )

            return redirect("/")

    else:
        return render_template("add_item.html", type_list=type_list)


@app.route("/emoji", methods=["GET", "POST"])
@login_required
def check_emoji():
    """Choose emoji"""

    user_id = session["user_id"]
    type_list = db.execute("SELECT type FROM type;")
    selected_emoji = request.form.get("emoji")
    selected_type = request.form.get("type")

    # List of emojis for selected menu
    emoji_dictionary = db.execute(
        "SELECT emoji FROM blobs JOIN type ON blobs.type_id = type.id WHERE user_id = (?) GROUP BY type ORDER BY CASE WHEN type = 'income' THEN 1 WHEN type = 'account' THEN 2 ELSE 3 END;",
        user_id,
    )
    emoji_list = [d["emoji"] for d in emoji_dictionary]

    if request.method == "POST":
        if not (selected_emoji and selected_type):
            must = "Please choose type and emoji"
            return render_template(
                "emoji.html", must=must, type_list=type_list, emoji_list=emoji_list
            )

        else:
            if emoji.emoji_list(selected_emoji):
                if emoji.emoji_count(selected_emoji) > 1:
                    must = "Please choose only ONE emoji"
                    return render_template(
                        "emoji.html",
                        must=must,
                        type_list=type_list,
                        emoji_list=emoji_list,
                    )

                elif not (
                    db.execute(
                        "SELECT emoji FROM blobs WHERE user_id = (?) AND type_id IN (SELECT id FROM type WHERE type = (?)) GROUP BY 'emoji';",
                        user_id,
                        selected_type,
                    )
                ):
                    must = "Please make an item in this category first"
                    return render_template(
                        "emoji.html",
                        must=must,
                        type_list=type_list,
                        emoji_list=emoji_list,
                    )

                else:
                    # Finally updating emoji
                    db.execute(
                        "UPDATE blobs SET emoji = (?) WHERE type_id IN (SELECT id FROM type WHERE type = (?)) AND user_id = (?);",
                        selected_emoji,
                        selected_type,
                        user_id,
                    )

                    return redirect("/")

            else:
                must = "This is not an emoji"
                return render_template(
                    "emoji.html", must=must, type_list=type_list, emoji_list=emoji_list
                )

    else:
        return render_template("emoji.html", type_list=type_list, emoji_list=emoji_list)


@app.route("/currency", methods=["GET", "POST"])
@login_required
def currency():
    """Currency"""

    user_id = session["user_id"]
    currency_list = db.execute("SELECT currency FROM currency;")
    actual_currency = db.execute(
        "SELECT currency FROM currency JOIN users ON currency.id = users.currency_id WHERE users.id = (?);",
        user_id,
    )[0]["currency"]

    if request.method == "POST":
        currency = request.form.get("currency")

        if not currency:
            must = "Currency must be chosen!"
            return render_template(
                "currency.html", currency_list=currency_list, must=must
            )
        else:
            currency_id = db.execute(
                "SELECT id FROM currency WHERE currency = (?);", currency
            )[0]["id"]

            db.execute(
                "UPDATE users SET currency_id = (?) WHERE id = (?);",
                currency_id,
                user_id,
            )
            return redirect("/")

    else:
        return render_template(
            "currency.html",
            currency_list=currency_list,
            actual_currency=actual_currency,
        )


@app.route("/delete_item", methods=["GET", "POST"])
@login_required
def delete_item():
    """Delete Item"""

    user_id = session["user_id"]

    all_blobs = db.execute(
        "SELECT blob_name, type, emoji FROM blobs JOIN users ON blobs.user_id = users.id JOIN type ON blobs.type_id = type.id WHERE users.id = (?) ORDER BY CASE WHEN type = 'income' THEN 1 WHEN type = 'account' THEN 2 ELSE 3 END;",
        user_id,
    )

    if request.method == "POST":
        selected_blob_name = request.form.get("selected_blob_name")

        if not selected_blob_name:
            must = "Please select item"
            return render_template("delete_item.html", must=must, all_blobs=all_blobs)

        else:
            blob_id = db.execute(
                "SELECT id FROM blobs WHERE user_id = (?) AND blob_name = (?);",
                user_id,
                selected_blob_name,
            )[0]["id"]

            db.execute(
                "DELETE FROM transactions WHERE user_id = (?) AND from_blob = (?);",
                user_id,
                blob_id,
            )
            db.execute(
                "DELETE FROM transactions WHERE user_id = (?) AND to_blob = (?);",
                user_id,
                blob_id,
            )
            db.execute(
                "DELETE FROM blobs WHERE user_id = (?) AND id = (?);", user_id, blob_id
            )

            return redirect("/")

    else:
        return render_template("delete_item.html", all_blobs=all_blobs)


@app.route("/delete_transaction", methods=["GET", "POST"])
@login_required
def delete_transaction():
    """Delete Transaction"""

    user_id = session["user_id"]

    # Get the current month
    current_date = datetime.date.today()
    current_month = current_date.strftime("%m")

    transaction_id = request.form.get("tr_delete")

    amount = db.execute(
        "SELECT amount FROM transactions WHERE id = (?);", transaction_id
    )[0]["amount"]

    type_from = db.execute(
        "SELECT type FROM blobs JOIN type ON blobs.type_id = type.id WHERE blobs.id IN (SELECT from_blob FROM transactions WHERE id = (?));",
        transaction_id,
    )[0]["type"]
    type_to = db.execute(
        "SELECT type FROM blobs JOIN type ON blobs.type_id = type.id WHERE blobs.id IN (SELECT to_blob FROM transactions WHERE id = (?));",
        transaction_id,
    )[0]["type"]

    # A way to delete transactions made in previous months
    if (
        current_month
        != db.execute(
            "SELECT strftime('%m', date) AS month FROM transactions JOIN date ON transactions.transaction_date = date.id WHERE transactions.id = (?);",
            transaction_id,
        )[0]["month"]
    ):
        if type_from == "income" and type_to == "account":
            db.execute(
                "UPDATE blobs SET money = round(money - (?), 2) WHERE blobs.id IN (SELECT to_blob FROM transactions WHERE id = (?));",
                amount,
                transaction_id,
            )

        elif type_from == "account" and type_to == "account":
            db.execute(
                "UPDATE blobs SET money = round(money + (?), 2) WHERE blobs.id IN (SELECT from_blob FROM transactions WHERE id = (?));",
                amount,
                transaction_id,
            )
            db.execute(
                "UPDATE blobs SET money = round(money - (?), 2) WHERE blobs.id IN (SELECT to_blob FROM transactions WHERE id = (?));",
                amount,
                transaction_id,
            )

        else:
            db.execute(
                "UPDATE blobs SET money = round(money - (?), 2) WHERE blobs.id IN (SELECT from_blob FROM transactions WHERE id = (?));",
                amount,
                transaction_id,
            )

    # A way to delete transactions made in this month
    else:
        if type_from == "income" and type_to == "account":
            db.execute(
                "UPDATE blobs SET money = round(money - (?), 2) WHERE blobs.id IN (SELECT from_blob FROM transactions WHERE id = (?));",
                amount,
                transaction_id,
            )
            db.execute(
                "UPDATE blobs SET money = round(money - (?), 2) WHERE blobs.id IN (SELECT to_blob FROM transactions WHERE id = (?));",
                amount,
                transaction_id,
            )

        elif type_from == "account" and type_to == "account":
            db.execute(
                "UPDATE blobs SET money = round(money + (?), 2) WHERE blobs.id IN (SELECT from_blob FROM transactions WHERE id = (?));",
                amount,
                transaction_id,
            )
            db.execute(
                "UPDATE blobs SET money = round(money - (?), 2) WHERE blobs.id IN (SELECT to_blob FROM transactions WHERE id = (?));",
                amount,
                transaction_id,
            )

        else:
            db.execute(
                "UPDATE blobs SET money = round(money - (?), 2) WHERE blobs.id IN (SELECT from_blob FROM transactions WHERE id = (?));",
                amount,
                transaction_id,
            )
            db.execute(
                "UPDATE blobs SET money = round(money + (?), 2) WHERE blobs.id IN (SELECT to_blob FROM transactions WHERE id = (?));",
                amount,
                transaction_id,
            )

    db.execute("DELETE FROM transactions WHERE id = (?);", transaction_id)

    return redirect("/")


@app.route("/get_options/<account_type>")
@login_required
def get_options(account_type):
    user_id = session["user_id"]

    # Getting account list for "To" selection menu
    account = db.execute(
        "SELECT blob_name, money, type, emoji FROM blobs JOIN users ON blobs.user_id = users.id JOIN type ON blobs.type_id = type.id WHERE users.id = (?) AND type = 'account';",
        user_id,
    )
    account_list = [
        f"{item['emoji']} {item['blob_name']} {item['type']}" for item in account
    ]

    # Getting account and expenses list for "To" selection menu
    expenses = db.execute(
        "SELECT blob_name, money, type, emoji FROM blobs JOIN users ON blobs.user_id = users.id JOIN type ON blobs.type_id = type.id WHERE users.id = (?) AND type = 'expenses';",
        user_id,
    )
    account_expenses = account + expenses
    account_expenses_list = [
        f"{item['emoji']} {item['blob_name']} {item['type']}"
        for item in account_expenses
    ]

    # Getting list of emoji blob_name and type to compare with account_type
    blobs_income = db.execute(
        "SELECT emoji, blob_name, type FROM blobs JOIN users ON blobs.user_id = users.id JOIN type ON blobs.type_id = type.id WHERE users.id = (?) AND type = 'income';",
        user_id,
    )
    blob_income_list = [
        f"{item['emoji']} {item['blob_name']} {item['type']}" for item in blobs_income
    ]

    if account_type in blob_income_list:
        data = account_list
    else:
        data = account_expenses_list

    return jsonify(data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            must = "Must provide username"
            return render_template("login.html", must=must)

        # Ensure password was submitted
        elif not request.form.get("password"):
            must = "Must provide password"
            return render_template("login.html", must=must)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            must = "Invalid username and/or password"
            return render_template("login.html", must=must)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    if request.method == "POST":
        if not (username and password and confirmation):
            must = "Please fill in all fields"
            return render_template("register.html", must=must)

        elif db.execute("SELECT username FROM users WHERE username = (?);", username):
            must = "User already exist"
            return render_template("register.html", must=must)

        elif password != confirmation:
            must = "Password do not match"
            return render_template("register.html", must=must)

        else:
            password_hash = generate_password_hash(password)
            db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?);",
                username,
                password_hash,
            )
            print("102")
            return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions():
    user_id = session["user_id"]
    years = db.execute("SELECT DISTINCT strftime('%Y', date) AS year FROM date;")

    # transactions = db.execute("SELECT from_blobs.emoji AS from_emoji, to_blobs.emoji AS to_emoji, from_blobs.blob_name AS fromm, to_blobs.blob_name AS too, amount, date.date AS transaction_date, transactions.id FROM transactions JOIN blobs AS from_blobs ON transactions.from_blob = from_blobs.id JOIN blobs AS to_blobs ON transactions.to_blob = to_blobs.id JOIN date ON transactions.transaction_date = date.id WHERE transactions.user_id = (?) AND date = DATE('now') ORDER BY transactions.id DESC;", user_id,)

    if request.method == "POST":
        year = request.form.get("year")
        month = request.form.get("month")
        day = request.form.get("day")

        if not year:
            must = "Please select at least a year"
            return render_template("transactions.html", years=years, must=must)
        else:
            if day and month and year:
                transactions = db.execute(
                    "SELECT from_blobs.emoji AS from_emoji, to_blobs.emoji AS to_emoji, from_blobs.blob_name AS fromm, to_blobs.blob_name AS too, amount, date.date AS transaction_date, transactions.id FROM transactions JOIN blobs AS from_blobs ON transactions.from_blob = from_blobs.id JOIN blobs AS to_blobs ON transactions.to_blob = to_blobs.id JOIN date ON transactions.transaction_date = date.id WHERE transactions.user_id = (?) AND strftime('%Y', date.date) = (?) AND strftime('%m', date.date) = (?) AND strftime('%d', date.date) = (?) ORDER BY transactions.id DESC;",
                    user_id,
                    year,
                    month,
                    day,
                )
                print(transactions)
                return render_template(
                    "transactions.html", years=years, transactions=transactions
                )

            elif month and year:
                transactions = db.execute(
                    "SELECT from_blobs.emoji AS from_emoji, to_blobs.emoji AS to_emoji, from_blobs.blob_name AS fromm, to_blobs.blob_name AS too, amount, date.date AS transaction_date, transactions.id FROM transactions JOIN blobs AS from_blobs ON transactions.from_blob = from_blobs.id JOIN blobs AS to_blobs ON transactions.to_blob = to_blobs.id JOIN date ON transactions.transaction_date = date.id WHERE transactions.user_id = (?) AND strftime('%Y', date.date) = (?) AND strftime('%m', date.date) = (?) ORDER BY transactions.id DESC;",
                    user_id,
                    year,
                    month,
                )
                print(transactions)
                return render_template(
                    "transactions.html", years=years, transactions=transactions
                )

            else:
                transactions = db.execute(
                    "SELECT from_blobs.emoji AS from_emoji, to_blobs.emoji AS to_emoji, from_blobs.blob_name AS fromm, to_blobs.blob_name AS too, amount, date.date AS transaction_date, transactions.id FROM transactions JOIN blobs AS from_blobs ON transactions.from_blob = from_blobs.id JOIN blobs AS to_blobs ON transactions.to_blob = to_blobs.id JOIN date ON transactions.transaction_date = date.id WHERE transactions.user_id = (?) AND strftime('%Y', date.date) = (?) ORDER BY transactions.id DESC;",
                    user_id,
                    year,
                )
                print(transactions)
                return render_template(
                    "transactions.html", years=years, transactions=transactions
                )

    else:
        years = db.execute("SELECT DISTINCT strftime('%Y', date) AS year FROM date;")
        return render_template("transactions.html", years=years)


@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    """Transfer Money"""

    user_id = session["user_id"]

    if request.method == "POST":
        # Get the current date
        current_date = datetime.date.today()
        formatted_date = current_date.strftime("%Y-%m-%d")

        # Check if the current date is already in the database
        if not db.execute("SELECT * FROM date WHERE date = (?);", formatted_date):
            db.execute("INSERT INTO date (date) VALUES (?);", formatted_date)

        # getting POST from index.html
        fromm = request.form.get("from")
        amount_string = request.form.get("amount")
        to = request.form.get("to")

        if fromm and amount_string and to:
            # getting blob_name from index.html
            fromm = fromm.split()
            to = to.split()

            # replacing "," to "."
            amount_string = amount_string.replace(",", ".")
            print(amount_string)

            # converting amount to integer
            try:
                amount = float(amount_string)

            except ValueError:
                return redirect("/")

            # a float with only two decimal places (just in case)
            amount = round(amount, 2)

            blob_name_from = fromm[1]
            blob_name_to = to[1]

            # checking for positive amount
            if amount > 0:
                # sending or adding mony from one account to another
                db.execute(
                    "UPDATE blobs SET money = round(money + (?), 2) WHERE user_id = (?) AND blob_name = (?);",
                    amount,
                    user_id,
                    blob_name_to,
                )

                # if money spent amount became negative
                if fromm[2] == "account":
                    amount = -amount

                db.execute(
                    "UPDATE blobs SET money = round(money + (?), 2) WHERE user_id = (?) AND blob_name = (?);",
                    amount,
                    user_id,
                    blob_name_from,
                )

                # if money sent to another account amount became positif but only for transactions
                if to[2] == "account":
                    amount = abs(amount)

                # adding this operation to transaction
                db.execute(
                    "INSERT INTO transactions (user_id, from_blob, to_blob, transaction_date, amount) VALUES (?, ?, ?, ?, ?);",
                    user_id,
                    (
                        db.execute(
                            "SELECT id FROM blobs WHERE blob_name = (?) AND user_id = (?);",
                            blob_name_from,
                            user_id,
                        )
                    )[0]["id"],
                    (
                        db.execute(
                            "SELECT id FROM blobs WHERE blob_name = (?) AND user_id = (?);",
                            blob_name_to,
                            user_id,
                        )
                    )[0]["id"],
                    (
                        db.execute(
                            "SELECT id FROM date WHERE date = (?);", formatted_date
                        )
                    )[0]["id"],
                    amount,
                )

        return redirect("/")
