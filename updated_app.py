from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask.views import MethodView
import mysql.connector
from mysql.connector import Error
import bcrypt
from functools import wraps
import datetime


app = Flask(__name__)
app.secret_key = 'G3mELYIU45AjG3NhQ6c1Og'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to view this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

from flask import request

from flask import request

@app.route('/payment_options', methods=['GET', 'POST'])
@login_required
def payment_options():
    if request.method == 'POST':
        # Process the payment form submission
        payment_type = request.form['payment_type']
        number = request.form['number']
        amount = request.form['amount']
        description = request.form.get('description', '')  # Optional description
        # Logic to process payment here (not implemented in detail)
        flash('Payment processed successfully!')
        # Redirect to the same page to display the flashed message
        return redirect(url_for('payment_options'))
    else:
        # Display the payment options form
        return render_template('payment_options.html')

class DBConnection:
    @staticmethod
    def create_connection():
        """Create a database connection."""
        try:
            connection = mysql.connector.connect(
                host='sql6.freesqldatabase.com',
                user='sql6704054',
                password='NdFnURGXaW',
                database='sql6704054',
                port='3306'
            )
            print("MySQL Database connection successful")
            return connection
        except Error as err:
            print(f"Error: '{err}'")
            return None


class User:
    def __init__(self, email):
        self.email = email

    def register(self, full_name, password):
        conn = DBConnection.create_connection()
        if conn:
            cursor = conn.cursor()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            try:
                # Check if the email already exists
                cursor.execute("SELECT email FROM Users WHERE email = %s", (self.email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    flash('This email is already registered. Please use a different email.')
                    return False

                # Register the user if the email doesn't exist
                cursor.execute(
                    "INSERT INTO Users (full_name, email, password) VALUES (%s, %s, %s)",
                    (full_name, self.email, hashed_password)
                )
                conn.commit()
                return True
            finally:
                cursor.close()
                conn.close()
        return False

    def login(self, password):
        conn = DBConnection.create_connection()
        if conn:
            cursor = conn.cursor(buffered=True)
            cursor.execute("SELECT user_id, password FROM Users WHERE email = %s", (self.email,))
            user = cursor.fetchone()
            conn.close()

            if user:
                user_id, stored_password = user
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    return user_id
        return None



class MoneyAccount:
    @staticmethod
    def add_payment_method(name, card_number, expiry_date):
        connection = DBConnection.create_connection()
        cursor = connection.cursor()
        query = """
        INSERT INTO MoneyAccount (name, payment_method, expiry_date)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (name, card_number, expiry_date))
        connection.commit()
        cursor.close()
        connection.close()
        flash("Payment method added successfully")

    @staticmethod
    def view_payment_methods():
        conn = DBConnection.create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name, payment_method, expiry_date, balance, currency, account_id FROM MoneyAccount")
            payment_methods = cursor.fetchall()
        except Error as e:
            flash('Error fetching payment methods: ' + str(e))
            payment_methods = []
        finally:
            cursor.close()
            conn.close()
        return payment_methods


    @staticmethod
    def delete_payment_method(account_id):
        conn = DBConnection.create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM MoneyAccount WHERE account_id = %s", (account_id,))
            conn.commit()
            flash('Payment method removed successfully!')
        except Error as e:
            flash('Error removing payment method: ' + str(e))
        finally:
            cursor.close()
            conn.close()



class Payment:
    def __init__(self, user_id, amount, currency_id, status_id, transfer_details, payment_method_id):
        self.user_id = user_id
        self.amount = amount
        self.currency_id = currency_id
        self.status_id = status_id
        self.transfer_details = transfer_details
        self.payment_method_id = payment_method_id

    def create_payment(self):
        connection = DBConnection.create_connection()
        cursor = connection.cursor()
        query = """
        INSERT INTO Payment (userID, amount, currencyID, statusID, transferDetails, paymentMethodID, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        cursor.execute(query, (self.user_id, self.amount, self.currency_id, self.status_id, self.transfer_details, self.payment_method_id))
        connection.commit()
        cursor.close()
        connection.close()
        print("Payment record added successfully")


class PaymentMethodForm(MethodView):
    @login_required
    def get(self):
        payment_methods = MoneyAccount.view_payment_methods()  # Fetch payment methods
        return render_template('add_payment.html', payment_methods=payment_methods)

    def post(self):
        name = request.form['name']
        card_number = request.form['cardNumber']
        expiry_date = request.form['expiry']
        balance = request.form['balance']  # Assume you handle balance input in your form
        currency = request.form['currency']  # Assume you handle currency input in your form
        account = MoneyAccount()
        account.add_payment_method(name, card_number, expiry_date, balance, currency)
        return redirect(url_for('paymentmethodform'))


class RegisterView(MethodView):
    def get(self):
        return render_template('register.html')

    def post(self):
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match. Please try again.')
            return redirect(url_for('register'))

        user = User(email)
        if user.register(full_name, password):
            session['user_id'] = user.login(password)
            flash('You have successfully registered!')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.')

        return render_template('register.html')



class LoginView(MethodView):
    def get(self):
        return render_template('login.html')

    def post(self):
        email = request.form['email']
        password = request.form['password']
        user = User(email)
        user_id = user.login(password)
        if user_id:
            session['user_id'] = user_id
            return redirect(url_for('transaction_history'))
        else:
            flash('Email or password is not correct.')
        return render_template('login.html')

   
class WelcomePage(MethodView):

    @login_required
    def get(self):
        # Here you can add any logic to fetch transaction data if needed
        return render_template('index.html')
    
class InquiryView(MethodView):
    @login_required
    def get(self):
        # Here you can add any logic to fetch transaction data if needed
        return render_template('inquiry.html')
    
class PaymentMethodsView(MethodView):
    @login_required
    def get(self):
        payment_methods = MoneyAccount.view_payment_methods()
        return render_template('view_accounts.html', payment_methods=payment_methods)

class DeletePaymentMethodView(MethodView):
    @login_required
    def post(self, account_id):
        MoneyAccount.delete_payment_method(account_id)
        return redirect(url_for('payment_methods_view'))


class TransactionHistory(MethodView):
    @login_required
    def get(self):
        user_id = session['user_id']
        transactions, balance = self.get_transactions_and_balance_by_user(user_id)
        return render_template('transaction_history.html', transactions=transactions, balance=balance)

    @staticmethod
    def get_transactions_and_balance_by_user(user_id):
        conn = DBConnection.create_connection()
        cursor = conn.cursor()
        query = """
        SELECT transaction_id, transaction_details, amount, creation_timestamp
        FROM Transaction
        WHERE user_id = %s
        ORDER BY creation_timestamp DESC
        """
        cursor.execute(query, (user_id,))
        transactions = cursor.fetchall()

        # Calculate balance by summing up the amount of each transaction
        balance_query = """
        SELECT COALESCE(SUM(amount), 0.0) FROM Transaction WHERE user_id = %s
        """
        cursor.execute(balance_query, (user_id,))
        balance = cursor.fetchone()[0]

        cursor.close()
        conn.close()
        return transactions, balance

class Subscription:
    def __init__(self, userID, service, paymentFrequency, active=True):
        self.userID = userID
        self.service = service
        self.paymentFrequency = paymentFrequency
        self.active = active

    def activateSubscription(self):
        self.active = True
        return self.update_active_status(True)

    def cancelSubscription(self):
        self.active = False
        return self.update_active_status(False)

    def update_active_status(self, subscription_id, status):
        conn = DBConnection.create_connection()
        cursor = conn.cursor()
        query = """
        UPDATE Subscription SET active = %s WHERE subscriptionID = %s
        """
        cursor.execute(query, (status, subscription_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True

    @staticmethod
    def create_subscription(userID, service, paymentFrequency):
        conn = DBConnection.create_connection()
        cursor = conn.cursor()

        # Get the current date and calculate renews_at based on paymentFrequency
        now = datetime.datetime.now()
        if paymentFrequency == 'Monthly':
            renews_at = now + datetime.timedelta(days=30)  # Approximately one month
        elif paymentFrequency == 'Quarterly':
            renews_at = now + datetime.timedelta(days=120)  # Approximately four months
        else:  # Assuming 'Yearly'
            renews_at = now + datetime.timedelta(days=365)  # Approximately one year

        query = """
        INSERT INTO Subscription (userID, service, paymentFrequency, active, renews_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (userID, service, paymentFrequency, True, renews_at))
        conn.commit()
        cursor.close()
        conn.close()

    
    @staticmethod
    def get_subscriptions_by_user(userID):
        conn = DBConnection.create_connection()
        cursor = conn.cursor()
        query = """
        SELECT subscriptionID, service, paymentFrequency, active, renews_at
        FROM Subscription
        WHERE userID = %s
        ORDER BY subscriptionID DESC
        """
        cursor.execute(query, (userID,))
        subscriptions = cursor.fetchall()
        cursor.close()
        conn.close()
        return subscriptions
    def delete_subscription(subscription_id):
        conn = DBConnection.create_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM Subscription WHERE subscriptionID = %s", (subscription_id,))
                conn.commit()
                return True
            except Error as e:
                return False
            finally:
                cursor.close()
                conn.close()



class SubscriptionsView(MethodView):
    @login_required
    def get(self):
        user_id = session['user_id']
        subscriptions = Subscription.get_subscriptions_by_user(user_id)
        return render_template('subscriptions.html', subscriptions=subscriptions)

class AddSubscriptionView(MethodView):
    @login_required
    def get(self):
        return render_template('add_subscription.html')

    def post(self):
        user_id = session['user_id']
        service = request.form['service']
        payment_frequency = request.form['paymentFrequency']

        try:
            Subscription.create_subscription(user_id, service, payment_frequency)
            flash('Subscription added successfully!')
        except Exception as e:
            flash(f'Error in adding subscription: {str(e)}')

        return redirect(url_for('subscriptions'))

class CancelSubscriptionView(MethodView):
    @login_required
    def post(self, subscription_id):
        user_id = session['user_id']
        subscription = Subscription(userID=user_id, service="", paymentFrequency="")  # Initializing with placeholders
        subscription.update_active_status(subscription_id, False)
        flash('Subscription canceled successfully!')
        return redirect(url_for('subscriptions'))

class ActivateSubscriptionView(MethodView):
    @login_required
    def post(self, subscription_id):
        user_id = session['user_id']
        subscription = Subscription(userID=user_id, service="", paymentFrequency="")  # Initializing with placeholders
        subscription.update_active_status(subscription_id, True)
        flash('Subscription activated successfully!')
        return redirect(url_for('subscriptions'))

class DeleteSubscriptionView(MethodView):
    decorators = [login_required]  # Ensure the user is logged in

    def post(self, subscription_id):
        try:
            if Subscription.delete_subscription(subscription_id):
                flash('Subscription successfully deleted.', 'success')
            else:
                flash('Failed to delete subscription.', 'error')
        except Exception as e:
            flash(f'Error during deletion: {str(e)}', 'error')
        
        return redirect(url_for('subscriptions'))

    
class PaymentMethodsView(MethodView):
    @login_required
    def get(self):
        payment_methods = MoneyAccount.view_payment_methods()
        return render_template('view_accounts.html', payment_methods=payment_methods)

class DeletePaymentMethodView(MethodView):
    @login_required
    def post(self, account_id):
        MoneyAccount.delete_payment_method(account_id)
        return redirect(url_for('payment_methods_view'))
    

class MakePaymentView(MethodView):
    @login_required
    def get(self):
        return render_template('make_payment.html')

    def post(self):
        user_id = session['user_id']
        account_number = request.form['account_number']
        amount = float(request.form['amount'])
        description = request.form['description']

        # Ensure the amount is positive
        if amount <= 0:
            flash('Amount must be greater than zero.')
            return redirect(url_for('make_payment'))

        # Check if the user has sufficient balance
        balance = self.get_balance_by_user(user_id)
        if balance < amount:
            flash('Insufficient balance to complete the transaction.')
            return redirect(url_for('make_payment'))

        # Create a transaction for the payment
        try:
            self.create_payment_transaction(user_id, account_number, amount, description)
            flash('Payment successful!')
        except Exception as e:
            flash(f'Error in processing payment: {str(e)}')

        return redirect(url_for('transaction_history'))

    @staticmethod
    def get_balance_by_user(user_id):
        conn = DBConnection.create_connection()
        cursor = conn.cursor()
        query = """
        SELECT SUM(amount) FROM Transaction WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        balance = cursor.fetchone()[0] or 0.0
        cursor.close()
        conn.close()
        return balance

    @staticmethod
    def create_payment_transaction(user_id, account_number, amount, description):
        conn = DBConnection.create_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO Transaction (user_id, transaction_details, amount, creation_timestamp)
        VALUES (%s, %s, %s, NOW())
        """
        cursor.execute(query, (user_id, f'Payment to Card Ending: {account_number[-4:]}, {description}', -amount))
        conn.commit()
        cursor.close()
        conn.close()





app.add_url_rule('/', view_func=WelcomePage.as_view('welcome'))
app.add_url_rule('/inquiry', view_func=InquiryView.as_view('inquiry_view'))
app.add_url_rule('/register', view_func=RegisterView.as_view('register'))
app.add_url_rule('/login', view_func=LoginView.as_view('login'))
app.add_url_rule('/add_payment', view_func=PaymentMethodForm.as_view('add_payment'))
app.add_url_rule('/transaction_history', view_func=TransactionHistory.as_view('transaction_history'))
app.add_url_rule('/view_accounts', view_func=PaymentMethodsView.as_view('payment_methods_view'))
app.add_url_rule('/delete_payment_method/<int:account_id>', view_func=DeletePaymentMethodView.as_view('delete_payment_method'), methods=['POST'])
app.add_url_rule('/make_payment', view_func=MakePaymentView.as_view('make_payment'))
app.add_url_rule('/subscriptions', view_func=SubscriptionsView.as_view('subscriptions'))
app.add_url_rule('/add_subscription', view_func=AddSubscriptionView.as_view('add_subscription'))
app.add_url_rule('/cancel_subscription/<int:subscription_id>', view_func=CancelSubscriptionView.as_view('cancel_subscription'), methods=['POST'])
app.add_url_rule('/activate_subscription/<int:subscription_id>', view_func=ActivateSubscriptionView.as_view('activate_subscription'), methods=['POST'])
app.add_url_rule('/delete_subscription/<int:subscription_id>', view_func=DeleteSubscriptionView.as_view('delete_subscription'), methods=['POST'])



if __name__ == '__main__':
    app.run(debug=True, port=5001)


class MakePaymentView(MethodView):
    @login_required
    def get(self):
        payment_methods = MoneyAccount.view_payment_methods()
        return render_template('make_payment.html', payment_methods=payment_methods)

    def post(self):
        user_id = session['user_id']
        account_number = request.form['account_number']
        amount = float(request.form['amount'])
        description = request.form['description']

        if amount <= 0:
            flash('Amount must be greater than zero.')
            return redirect(url_for('make_payment'))

        balance = self.get_balance_by_user(user_id)
        if balance < amount:
            flash('Insufficient balance to complete the transaction.')
            return redirect(url_for('make_payment'))

        try:
            self.create_payment_transaction(user_id, account_number, -amount, f'Payment to Card Ending: {account_number[-4:]}, {description}')
            flash('Payment successful!')
        except Exception as e:
            flash(f'Error in processing payment: {str(e)}')

        return redirect(url_for('transaction_history'))

    @staticmethod
    def get_balance_by_user(user_id):
        conn = DBConnection.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM Transaction WHERE user_id = %s", (user_id,))
        balance = cursor.fetchone()[0] or 0.0
        cursor.close()
        conn.close()
        return balance

    @staticmethod
    def create_payment_transaction(user_id, account_number, amount, description):
        conn = DBConnection.create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Transaction (user_id, transaction_details, amount, creation_timestamp) VALUES (%s, %s, %s, NOW())", (user_id, f'Payment to Card Ending: {account_number[-4:]}, {description}', amount))
        conn.commit()
        cursor.close()
        conn.close()
