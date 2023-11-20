# Expense Tracker
#### Video Demo:  https://youtu.be/IIwnNInCA_8
#### Description:

Hello, I am Mykyta, and this is my final project for CS50!

"Expense Tracker" is a web application designed for use in a web browser on desktops. The main goal of this app is to help users keep track of finances, including income, expenses, and their overall balance.

### Environment
Python, Flask, JavaScript, Jinja, HTML, CSS, SQLite3

### Specifications
* The backend is coded in the Python programming language within the /app.py file, utilizing the Flask library.

* JavaScript has been used for AJAX technology, specifically for interdependent dropdown menu on the main page. This script is located in the /templates/index.html file

* All pages have been written in HTML, incorporating Bootstrap and CSS.

* SQLite3 was used to compile databases. The database file is data.db, and it contains tables: users, blobs, transactions, date, type, and currency.

### Some features
* Users can register, log in, and log out. There is no limit to the number of users.

* Every new month, the amounts of all items within the Income and Expenses categories are automatically reset to 0.

* The user's entered amount of money is automatically rounded to two decimal places.

* To separate decimal digits, users can use either a period or a comma. The comma will be automatically converted to a period.

* Incorrect inputs from users are predicted, and explanations are provided to guide users on what should be done differently.

* If the user is new and doesn't have any items or transactions, the “Dashboard” will display a greeting and some helpful information instead of empty tables.

* On the “Add Item” page, a new user won't see any emojis next to the category names until they create at least one item for each category. After this, default emojis will appear, and if the user decides to change emojis, the selected menu will also be updated with the new emojis.

### Structure
On all pages, excluding the “log in” and “Registration” pages, the top section features the navigation menu displaying the app's name: “Expense Tracker,” functioning as a direct link to the main page titled “Dashboard.” Following this, you'll find options for “Add Item,” “Delete Item,” “Currency,” “Emoji,” and “Transactions.”

### Dashboard
At the top of the “Dashboard,” users will find a handy section for managing their finances. Here, users can easily add income to any of accounts, make transfers between accounts, and add expenses from accounts into specific expense categories.

Below on the left side, three main categories stand out: “Income,” “Accounts,” and “Expenses.”

Within each category, next to the category name, users will see:
* “Received” – showing the total income for the current month,
* ”Balance” – displaying your overall financial standing,
* ”Spent” – indicating the total expenses for the ongoing month.

Below these summaries, lists of Items are presented. Each Item is represented by an emoji, followed by the item’s name and the amount of money.

On the right side, users will find a section titled “Today's Transactions,” displaying the total amount spent for the day. Below, a list of all transactions made today.

Next to each transaction, there is a delete button. Users can use this button to delete a transaction, and the money will be automatically returned to the respective items.

### Add Item
On this page, users have the option to create a new item within one of three categories: “Income,” “Accounts,” and “Expenses.” They simply need to choose a name for the item and select the category from the dropdown menu.

### Delete Item
On this page, users can delete an item by selecting it from the dropdown menu and clicking the "Delete" button. All transactions related to this item will be deleted, but the amount of money within the other items will not be changed.

### Currency
On this page, users can view the current currency symbol and have the ability to change it to US Dollars, Euros, or Ukrainian Hryvnia. This is only an aesthetic feature. If the user decides to change the currency, only the symbol will change, and the amount of money will not be converted to the new currency.

### Emoji
When creating a new item within the categories of “Income,” “Accounts,” or “Expenses,” users automatically receive a default emoji symbol for each category. However, on the “Emoji” page, users can change these default emojis to ones of their preference.

### Transactions
On this page, users can view all transactions for a specific year, month, or day by simply selecting the desired date from the dropdown menu. Next to each transaction, there is a “Delete” button that users can use to delete transactions.

If the transaction the user wishes to delete was made in the current month, the money will be automatically returned to the respective items.

However, if the user decides to delete a transaction from the previous month or an earlier period, the amount of money will be returned to the account items, but categories such as “Income” or “Expenses” will not be altered since they were reset to 0 at the beginning of this month.

Thank you!
