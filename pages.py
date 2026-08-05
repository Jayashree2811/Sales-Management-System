import streamlit as st
import psycopg2
import pandas as pd

# --------------------------------------------------------------------
# Page Configuration
# --------------------------------------------------------------------
st.set_page_config(
    page_title="Sales Intelligence Hub",
    page_icon="📊",
    layout="wide")

# --------------------------------------------------------------------
# Custom CSS
# --------------------------------------------------------------------


# ------------------------------------------------------------------------------------------------------------------------------------
# PostgreSQL Connection
# ------------------------------------------------------------------------------------------------------------------------------------
try:
    conn = psycopg2.connect(
        host="localhost",
        database="sales management system",
        user="postgres",
        password="Jayashree",
        port="5432"
    )
    cursor = conn.cursor()  #Establishes a connection with the postgreSQL DB

except Exception as e:
    st.error(f"Database Connection Failed: {e}") #Stops the application if the connection fails.
    st.stop()

# ------------------------------------------------------------------------------------------------------------------------------------
# Session State
# Stores login information so the user remains authenticated,while navigating between different pages
# ------------------------------------------------------------------------------------------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# ------------------------------------------------------------------------------------------------------------------------------------
# Login Page
# Authenticate users using their username and password. Stores user information in Streamlit session state after successful login.
# ------------------------------------------------------------------------------------------------------------------------------------
def login_page():

    st.title("Sales Management System,")
    st.caption("A Smart Sales Management and Business Analytics Dashboard")
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        #Validate entered credentials from the users table.
        cursor.execute("""
            SELECT user_id,
                   username,
                   password,
                   branch_id,
                   role,
                   email
            FROM users
            WHERE username = %s
              AND password = %s
        """, (username, password))

        user = cursor.fetchone()

        if user:

            #  Save logged-in user information for future use.
            st.session_state.logged_in = True

            # User Details
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.branch_id = user[3]
            st.session_state.role = user[4]
            st.session_state.email = user[5]

            st.success(f"Welcome, {st.session_state.username}!")

            st.rerun()

        else:
            st.error("Invalid Username or Password")


# ------------------------------------------------------------------------------------------------------------------------------------
# Payments
#Allows users to: 1. Select a customer 2. Record payment 3.Update received amount 4. Close sale when payment is completed
# ------------------------------------------------------------------------------------------------------------------------------------
def show_Payments():
    st.title("💳 Payment Entry")

    if st.session_state.role == "Super Admin":
   # Load only sales that still have pending payments.
        sales = pd.read_sql("""
            SELECT sale_id,
                   customer_name,
                   pending_amount
            FROM customer_sales
            WHERE status='Open'
            ORDER BY sale_id
        """, conn)

    else:

        sales = pd.read_sql("""
            SELECT sale_id,
                   customer_name,
                   pending_amount
            FROM customer_sales
            WHERE status='Open'
              AND branch_id=%s
            ORDER BY sale_id
        """, conn,
        params=(st.session_state.branch_id,))

    if sales.empty:
        st.info("No pending payments.")
        return
    # Select the customer whose payment is being collected.
    # Dropdown
    sale = st.selectbox(
        "Select Sale",
        sales["sale_id"]
    )
    # Retrieve complete customer details.
    customer = pd.read_sql(
        """
        SELECT *
        FROM customer_sales
        WHERE sale_id=%s
        """,
        conn,
        params=(sale,)
    )

    st.write("### Customer Details")

    st.write("Customer :", customer["customer_name"][0])
    st.write("Product :", customer["product_name"][0])
    st.write("Gross :", customer["gross_sales"][0])
    st.write("Received :", customer["received_amount"][0])
    st.write("Pending :", customer["pending_amount"][0])

    st.divider()

    payment_date = st.date_input("Payment Date")

    amount = st.number_input(
        "Payment Amount",
        min_value=0.0
    )

    mode = st.selectbox(
        "Payment Mode",
        [
            "Cash",
            "UPI",
            "Card",
            "Bank Transfer"
        ]
    )

    #remarks = st.text_area("Remarks")

    if st.button("Save Payment"):
        print("INSERT payment")

        cursor.execute(
    # Save payment transaction into payment history.
                    """
    
    INSERT INTO payment_splits 
    (
        sale_id,
        payment_date,
        amount_paid,
        payment_method
    )
    VALUES
    (%s,%s,%s,%s)
    """,
    (
        sale,
        payment_date,
        amount,
        mode
    )
)
        # Increase received amount after successful payment.
        print("UPDATE payment")
        cursor.execute(
            """
            UPDATE customer_sales
            SET received_amount = received_amount + %s
            WHERE sale_id= %s;
            """,
            (
                amount,
                sale
            )
        )
        print("UPDATE status")
        cursor.execute(
            """
            UPDATE customer_sales
            SET status='Close'
            WHERE sale_id= %s
            AND pending_amount =0
            """,
            (sale,)
        )
        # Save all database changes permanently.
        conn.commit()

        st.success("Payment Added Successfully")

        st.rerun()#line number 181




# ------------------------------------------------------------------------------------------------------------------------------------
# Customers
# Displays customer sales records.
# ------------------------------------------------------------------------------------------------------------------------------------
def show_customers():

    if st.session_state.role == "Super Admin":

     query = """SELECT cs.*, b.branch_name FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id ORDER BY cs.sale_id
    """

     df = pd.read_sql(query, conn)

    else:
        # Retrieve customer sales along with branch name.
     query = """
    SELECT
        cs.*,
        b.branch_name
    FROM customer_sales cs
    JOIN branches b
        ON cs.branch_id = b.branch_id
    WHERE cs.branch_id=%s
    ORDER BY cs.sale_id
    """
    # Display customer information in tabular format.
    df = pd.read_sql(
        query,
        conn,
        params=(st.session_state.branch_id,))

    if df.empty:
        st.warning("No customers found.")
        return

    st.dataframe(df, use_container_width=True)
    
# ------------------------------------------------------------------------------------------------------------------------------------
# Add Sales
# Creates a new customer sales record.
# ------------------------------------------------------------------------------------------------------------------------------------
def add_sales():

    st.title("New Sales Entry")
# Maps branch names with corresponding database IDs.
    branch_dict = {
    "Ahmedabad": 1,
    "Chennai": 2,
    "Coimbatore": 3,
    "Madurai": 4,
    "Trichy": 5
    }
    with st.form("sales_form"):

        col1, col2 = st.columns(2)

        with col1:

            branch = st.selectbox(
                "Branch",
                list(branch_dict.keys())
            )

            customer_name = st.text_input("Customer Name")

            mobile = st.text_input("Mobile Number")

            gross = st.number_input(
                "Gross Sales",
                min_value=0.0
            )

        with col2:

            product = st.selectbox(
                "Product",
                ["DS", "BA", "DA", "FSD"]
            )

            sale_date = st.date_input("Sale Date")

            

            status = st.selectbox(
                "Status",
                ["Open", "Close"]
            )
# Calculate pending amount based on received payment.
        pending = gross 

        st.info(f"Pending Amount : ₹{pending:,.2f}")

        submit = st.form_submit_button("Save")

    if submit:

        cursor.execute(
            # Save new sales record into the customer_sales table.
            """
            INSERT INTO customer_sales
            (
                branch_id,
                sale_date,
                customer_name,
                mobile_number,
                product_name,
                gross_sales,
                status
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                branch_dict[branch],
                sale_date,
                customer_name,
                mobile,
                product,
                gross,
                status
            )
        )

        conn.commit()

        st.success("Sales Entry Added Successfully")
        st.balloons()


# ------------------------------------------------------------------------------------------------------------------------------------
# Dashboard
# Displays the sales dashboard.
# ------------------------------------------------------------------------------------------------------------------------------------
def show_dashboard():

  if st.session_state.role == "Super Admin":

     query = """
    SELECT
        cs.*,
        b.branch_name
    FROM customer_sales cs
    INNER JOIN branches b
        ON cs.branch_id = b.branch_id
    ORDER BY cs.sale_id
    """

     df = pd.read_sql(query, conn)

  else:

    query = """
    SELECT
        cs.*,
        b.branch_name
    FROM customer_sales cs
    INNER JOIN branches b
        ON cs.branch_id = b.branch_id
    WHERE cs.branch_id = %s
    ORDER BY cs.sale_id
    """

    df = pd.read_sql(
        query,
        conn,
        params=(st.session_state.branch_id,)
    )
  if df.empty:
        st.warning("No data available.")
        return
  df["sale_date"] = pd.to_datetime(df["sale_date"])

  col1, col2, col3 = st.columns(3)

  with col1:
        branch = st.selectbox(
            "Branch",
            ["All"] + sorted(df["branch_name"].unique().tolist())
        )

  with col2:
        customer = st.selectbox(
            "Customer",
            ["All"] + sorted(df["customer_name"].unique().tolist())
        )

  with col3:
        status = st.selectbox(
            "Status",
            ["All"] + sorted(df["status"].unique().tolist())
        )

  from_date = st.date_input(
        "From Date",
        df["sale_date"].min().date()
    )

  to_date = st.date_input(
        "To Date",
        df["sale_date"].max().date()
    )
# Create a copy to apply user-selected filters.
  filtered = df.copy()

  if branch != "All":
        filtered = filtered[
            filtered["branch_name"].astype(str) == branch
        ]

  if customer != "All":
        filtered = filtered[
            filtered["customer_name"] == customer
        ]

  if status != "All":
        filtered = filtered[
            filtered["status"] == status
        ]

  filtered = filtered[
        (filtered["sale_date"] >= pd.to_datetime(from_date)) &
        (filtered["sale_date"] <= pd.to_datetime(to_date))
    ]

  gross = filtered["gross_sales"].sum()
  received = filtered["received_amount"].sum()
  pending = filtered["pending_amount"].sum()
  if gross == 0:
        pending_percent = 0
  else:
        pending_percent = (pending / gross) * 100

  c1, c2, c3, c4 = st.columns(4)
# Calculate dashboard KPIs.
  c1.metric("Gross Sales", f"₹{gross:,.2f}")
  c2.metric("Received", f"₹{received:,.2f}")
  c3.metric("Pending", f"₹{pending:,.2f}")
  c4.metric("Pending %", f"{pending_percent:.2f}%")

  st.divider()
# Display filtered sales records.
  st.dataframe(filtered, use_container_width=True)


#---------------------------------------------
# Demonstrates SQL queries
# Users can select a predefined business question and execute its corresponding SQL query.
#---------------------------------------------

def show_LiveSQLEngine():
# Collection of business questions and their SQL solutions.
    analysis_queries = {
        "1.Retrieve all records from the customer_sales table.":
        """SELECT * FROM customer_sales;""",
        "2.Retrieve all records from the branches table.":
        """SELECT * FROM branches;""",
        "3.Retrieve all records from the payment_splits table.":
        """SELECT * FROM payment_splits;""",
        "4.Retrieve all sales belonging to the Chennai branch.":
        """SELECT cs.* FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id WHERE b.branch_name = 'Chennai';""",
        "5.Calculate the total received amount across all sales.":
        """SELECT SUM(received_amount) AS total_received_amount FROM customer_sales;""",
        "6.Calculate the total pending amount across all sales.":
        """SELECT SUM(pending_amount) AS total_pending_amount FROM customer_sales;""",
        "7.Count the total number of sales per branch.":
        """SELECT b.branch_name, COUNT(cs.sale_id) AS total_sales FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id GROUP BY b.branch_name;""",
        "8.Find the average gross sales amount.":
        """SELECT AVG(gross_sales) AS average_gross_sales FROM customer_sales;""",
        "9. Retrieve sales details along with the branch name.":
        """SELECT cs.sale_id, cs.customer_name, cs.product_name, cs.gross_sales, b.branch_name FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id;""",
        "10. Retrieve sales details along with total payment received.":
        """SELECT cs.sale_id,cs.customer_name,SUM(ps.amount_paid) AS total_payment_received FROM customer_sales cs JOIN payment_splits ps ON cs.sale_id = ps.sale_id GROUP BY cs.sale_id, cs.customer_name; """,
        "11. Show branch-wise total gross sales.":
        """SELECT b.branch_name, SUM(cs.gross_sales) AS total_gross_sales FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id GROUP BY b.branch_name;""",
        "12. Display sales along with payment method used.":
        """SELECT cs.sale_id,cs.customer_name, ps.payment_method,ps.amount_paid FROM customer_sales cs JOIN payment_splits ps ON cs.sale_id = ps.sale_id;""",
        "13. Retrieve top 3 highest gross sales.":
        """SELECT sale_id,customer_name, gross_sales FROM customer_sales ORDER BY gross_sales DESC LIMIT 3;""",
        "14. Find the branch with highest total gross sales.":
        """SELECT b.branch_name,SUM(cs.gross_sales) AS total_gross_sales FROM customer_sales cs JOIN branches b ON cs.branch_id = b.branch_id GROUP BY b.branch_name ORDER BY total_gross_sales DESC LIMIT 1; """,
        "15. Retrieve monthly sales summary.":
        """SELECT EXTRACT(YEAR FROM sale_date) AS year, EXTRACT(MONTH FROM sale_date) AS month,SUM(gross_sales) AS total_sales FROM customer_sales GROUP BY year, month ORDER BY year, month;""",
        "16. Calculate payment method-wise total collection.":
        """SELECT payment_method, SUM(amount_paid) AS total_collection FROM payment_splits GROUP BY payment_method;"""

    }
    selected_question = st.selectbox(
    "Select a Business Question",
    list(analysis_queries.keys())
    )

    st.subheader("SQL Query")
    st.code(analysis_queries[selected_question], language="sql")

    if st.button("Run Query"):
        query = analysis_queries[selected_question]
        df = pd.read_sql(query, conn)
        st.dataframe(df)
# ------------------------------------------------------------------------------------------------------------------------------------
# Main Menu
# Controls application navigation using the sidebar menu.
# ------------------------------------------------------------------------------------------------------------------------------------
def main():

    menu = st.sidebar.selectbox(
        "Menu",
        [
            "Dashboard",
            "Customers",
            "Sales",
            "Payments",
            "Live SQL Engine",
            "Logout"
        ]
    )

    if menu == "Dashboard":
        show_dashboard()

    elif menu == "Customers":
        show_customers()

    elif menu == "Sales":
        add_sales()

    elif menu == "Payments":
        show_Payments()
    elif menu == "Live SQL Engine":
            show_LiveSQLEngine()

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()


# ------------------------------------------------------------------------------------------------------------------------------------
# Run App
# Entry point of the application.
# If the user is already logged in, load the main application.  Otherwise, display the login page for authentication.

# ------------------------------------------------------------------------------------------------------------------------------------
if st.session_state.logged_in:
    main()
else:
    login_page()