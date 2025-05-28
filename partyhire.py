import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import json # For JSON serialization
import datetime
import re
from PIL import Image, ImageTk  # For logo resizing

# ---------------------------
# ---- LOGIN SCREEN ----
# ---------------------------
def login():
    """Validate user login and open the main program."""
    username = entry_username.get()
    password = entry_password.get()
    if username == "admin" and password == "1234":  # Replace with real validation as needed
        messagebox.showinfo("Login Success", "Welcome!")
        login_root.destroy()  # Close login window
        open_main_system()  # Open main party hire system
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")

# Create the login window
login_root = tk.Tk()
login_root.title("Party Vault Rental Login")
login_root.geometry("350x450")

# Set a background color
#login_root.configure(bg="#f5fffa")  # Light blue background

# Load and resize the logo
logo_image = Image.open("logo.png")
logo_image = logo_image.resize((150, 150))  # Adjust size as needed
logo = ImageTk.PhotoImage(logo_image)
logo_label = tk.Label(login_root, image=logo)
logo_label.pack(pady=10)

# Login fields
tk.Label(login_root, text="Username").pack()
entry_username = tk.Entry(login_root)
entry_username.pack()
tk.Label(login_root, text="Password").pack()
entry_password = tk.Entry(login_root, show="*")
entry_password.pack()
tk.Button(login_root, text="Login", command=login).pack(pady=10)

# ---------------------------
# ---- MAIN SYSTEM ----
# ---------------------------
def open_main_system():
    """Initialize the main party hire system."""
    root = tk.Tk()
    root.title("Party Vault Rental System")
    root.geometry("800x600")
    
    main_bg = "#add8e6"  # Alice Blue
    root.configure(bg=main_bg)
    
    # ---- DATABASE INITIALIZATION ----
    with sqlite3.connect('party_hire.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT,
                receipt_number INTEGER,
                items TEXT,
                addons TEXT,
                total REAL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO metadata (key, value) 
            VALUES ('last_receipt_number', '0')
        ''')
        conn.commit()

    # ---- ITEM DATA ----
    items = {
        "Coffee Mugs @ $0.90": {"price": 0.90, "stock": 50},
        "Cup and Saucer @ $0.90": {"price": 0.90, "stock": 50},
        "Dinner Plates @ $0.75": {"price": 0.75, "stock": 50},
        "Side Plates @ $0.75": {"price": 0.75, "stock": 50},
        "Dinner Fork @ $0.70": {"price": 0.70, "stock": 50},
        "Knife @ $0.70": {"price": 0.70, "stock": 50},
        "Soup Spoon @ $0.70": {"price": 0.70, "stock": 50},
        "Dessert Spoon @ $0.80": {"price": 0.80, "stock": 50},
        "Teaspoon @ $0.80": {"price": 0.80, "stock": 50},
        "Juice Glass @ $0.60": {"price": 0.60, "stock": 50},
        "Beer Glass @ $0.60": {"price": 0.60, "stock": 50},
        "Wine Glass@ $0.90": {"price": 0.90, "stock": 50},
    }
    addons = {
        "Delivery": 20,
        "Setup Service": 25,
    }
    cart = {}
    selected_addons = {}

    # ---- FUNCTIONS FOR GUI OPERATIONS ----
    def add_to_cart():
        """Add selected item and quantity to the cart."""
        item = item_var.get()
        try:
            quantity = int(quantity_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity.")
            return
        if item in items and items[item]['stock'] >= quantity:
            cart[item] = cart.get(item, 0) + quantity
            items[item]['stock'] -= quantity
            update_cart()
            update_total()
        else:
            messagebox.showerror("Error", "Insufficient stock for selected item.")

    def remove_from_cart():
        """Remove the selected item from the cart."""
        selection = cart_list.curselection()
        if selection:
            item_text = cart_list.get(selection)
            # Expect format: "Item Name x Quantity"
            item_name, qty = item_text.split(" x ")
            qty = int(qty)
            if item_name in cart:
                del cart[item_name]
                items[item_name]['stock'] += qty
                update_cart()
                update_total()

    def update_cart():
        """Refresh the cart list display."""
        cart_list.delete(0, tk.END)
        for item, quantity in cart.items():
            cart_list.insert(tk.END, f"{item} x {quantity}")

    def update_total():
        """Calculate and display the total cost."""
        total = sum(items[item]['price'] * quantity for item, quantity in cart.items())
        total += sum(selected_addons.values())
        total_label.config(text=f"Total: ${total:.2f}")

    def proceed_order():
        """Finalize the order, update the database, and refresh the table."""
        customer_name = name_entry.get()
        if not customer_name:
            messagebox.showerror("Error", "Please enter the customer name.")
            return
        if not cart:
            messagebox.showerror("Error", "Cart is empty.")
            return

        with sqlite3.connect('party_hire.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM metadata WHERE key = 'last_receipt_number'")
            last_receipt_number = int(cursor.fetchone()[0])
            new_receipt_number = last_receipt_number + 1
            date_time = datetime.datetime.now()
            total_cost = sum(items[item]['price'] * quantity for item, quantity in cart.items()) + sum(selected_addons.values())

            cursor.execute('''
                INSERT INTO orders (customer_name, receipt_number, items, addons, total, date) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (customer_name, new_receipt_number, json.dumps(cart), json.dumps(selected_addons), total_cost, date_time))
            cursor.execute("UPDATE metadata SET value = ? WHERE key = 'last_receipt_number'", (new_receipt_number,))
            conn.commit()

        messagebox.showinfo("Success", f"Order placed successfully! Receipt Number: {new_receipt_number}")
        reset_order()
        update_table()

    def delete_order():
        """Delete the selected order from the database and table."""
        selected_item = table.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select an order to delete.")
            return
        receipt_number = table.item(selected_item[0], 'values')[2]
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the order with Receipt Number {receipt_number}?")
        if confirm:
            with sqlite3.connect('party_hire.db') as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM orders WHERE receipt_number = ?", (receipt_number,))
                conn.commit()
            table.delete(selected_item[0])
            messagebox.showinfo("Success", f"Order with Receipt Number {receipt_number} has been deleted.")

    def reset_order():
        """Reset the order form and clear the cart."""
        cart.clear()
        selected_addons.clear()
        name_entry.delete(0, tk.END)
        update_cart()
        update_total()

    def update_table():
        """Refresh the order table with the latest records from the database."""
        for row in table.get_children():
            table.delete(row)
        with sqlite3.connect('party_hire.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT date, customer_name, receipt_number, items, total FROM orders")
            rows = cursor.fetchall()
            for row in rows:
                table.insert("", tk.END, values=row)

    # ---- GUI ELEMENTS SETUP ----
    # Customer Name
    tk.Label(root, text="Customer Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    name_entry = tk.Entry(root)
    name_entry.grid(row=0, column=1, padx=5, pady=5)

    # Item Selection
    tk.Label(root, text="Select Item:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    item_var = tk.StringVar()
    item_menu = ttk.Combobox(root, textvariable=item_var, values=list(items.keys()))
    item_menu.grid(row=1, column=1, padx=5, pady=5)

    # Quantity
    tk.Label(root, text="Quantity:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    quantity_entry = tk.Entry(root)
    quantity_entry.grid(row=2, column=1, padx=5, pady=5)
    quantity_entry.insert(0, "1")

    # Cart List
    tk.Label(root, text="Cart:").grid(row=3, column=0, padx=5, pady=5, sticky="ne")
    cart_list = tk.Listbox(root, height=5)
    cart_list.grid(row=3, column=1, padx=5, pady=5)

    # Buttons for Cart Operations
    tk.Button(root, text="Add to Cart", command=add_to_cart).grid(row=4, column=0, padx=5, pady=5)
    tk.Button(root, text="Remove from Cart", command=remove_from_cart).grid(row=4, column=1, padx=5, pady=5)
    tk.Button(root, text="Proceed Order", command=proceed_order).grid(row=5, column=0, padx=5, pady=5)
    tk.Button(root, text="Delete Order", command=delete_order).grid(row=5, column=1, padx=5, pady=5)
    tk.Button(root, text="Exit", command=root.quit).grid(row=6, column=1, padx=5, pady=5)

    total_label = tk.Label(root, text="Total: $0.00")
    total_label.grid(row=6, column=0, padx=5, pady=5)

    # Order Table Widget
    cols = ("Date / Time", "Customer Name", "Receipt Number", "Items", "Total")
    global table
    table = ttk.Treeview(root, columns=cols, show='headings', height=8)
    table.grid(row=7, column=0, columnspan=2, padx=5, pady=5)
    for col in cols:
        table.heading(col, text=col)
        table.column(col, width=100)
    
    update_table()
    root.mainloop()

# Start the login UI
login_root.mainloop()
