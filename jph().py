"""This file calculates required total cost of party hire items for kiwis."""
from tkinter import messagebox, ttk
import tkinter as tk
import sqlite3
import json
import datetime
import re

# Initialize data

# Identifying items and their prices
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


def initialize_database():
    """Initialize the SQLite database."""
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

# Functions for GUI Operations


def add_to_cart():
    """Define cart values."""
    item = item_var.get()
    quantity = int(quantity_entry.get())
    if item in items and items[item]['stock'] >= quantity:
        if item in cart:
            cart[item] += quantity
        else:
            cart[item] = quantity
        items[item]['stock'] -= quantity
        update_cart()
        update_total()
    else:
        messagebox.showerror("Error", "Insufficient stock for selected item.")


def remove_from_cart():
    
    selected = cart_list.curselection()
    if selected:
        item = cart_list.get(selected)
        item_name = item.split(" x ")[0]
        quantity = int(item.split(" x ")[1])
        del cart[item_name]
        items[item_name]['stock'] += quantity
        update_cart()
        update_total()


def update_cart():
    
    cart_list.delete(0, tk.END)
    for item, quantity in cart.items():
        cart_list.insert(tk.END, f"{item} x {quantity}")



def select_addon(addon, price):
    
    
    if addon_vars[addon].get():
        selected_addons[addon] = price
    else:
        if addon in selected_addons:
            del selected_addons[addon]
    update_total()


def update_total():
   
    total = sum(items[item]['price'] * quantity for item, quantity in cart.items())
    total += sum(selected_addons.values())
    total_label.config(text=f"Total: ${total:.2f}")


def validate_customer_name(p):
   
   # Allow only alphabetic characters and spaces
    return bool(re.match(r"^[A-Za-z\s]*$", p))



def proceed_order():
    
    
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

        cursor.execute('''
        INSERT INTO orders (customer_name, receipt_number, items, addons, total, date) VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer_name, new_receipt_number, json.dumps(cart), json.dumps(selected_addons), sum(items[item]['price'] * quantity for item, quantity in cart.items()) + sum(selected_addons.values()), date_time))

        cursor.execute("UPDATE metadata SET value = ? WHERE key = 'last_receipt_number'", (new_receipt_number,))
    conn.commit()
    messagebox.showinfo("Success", f"Order placed successfully! Receipt Number: {new_receipt_number}")
    reset_order()
    update_table()

def reset_order():
    cart.clear()
    selected_addons.clear()
    name_entry.delete(0, tk.END)
    update_cart()
    update_total()
    for var in addon_vars.values():
        var.set(0)

def update_table():
    for row in table.get_children():
        table.delete(row)
    with sqlite3.connect('party_hire.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date, customer_name, receipt_number, items, total FROM orders")
        rows = cursor.fetchall()
        for row in rows:
            table.insert("", tk.END, values=row)

def delete_order():
    selected = table.selection()
    if not selected:
        messagebox.showerror("Error", "Please select an order to delete.")
        return

    receipt_number = table.item(selected[0], 'values')[2]
    confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the order with Receipt Number {receipt_number}?")
    if confirm:
        with sqlite3.connect('party_hire.db') as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM orders WHERE receipt_number = ?", (receipt_number,))
            conn.commit()

        table.delete(selected[0])
        messagebox.showinfo("Success", f"Order with Receipt Number {receipt_number} has been deleted.")

# GUI Setup
root = tk.Tk()
root.title("Julie's Party Hire")
# Information to be tabulated
def create_widgets(root):
    global name_entry, item_var, item_menu, quantity_entry, cart_list, addon_vars, total_label, receipt_entry, table

    # Customer name
    tk.Label(root, text="Customer Name: ").grid(row=0, column=0, padx=5, pady=5)
    vcmd = (root.register(validate_customer_name), '%P')
    name_entry = tk.Entry(root, validate='key', validatecommand=vcmd)
    name_entry.grid(row=0, column=1, padx=5, pady=5)

    # Receipt number (for display)
    tk.Label(root, text="Receipt Number: ").grid(row=1, column=0, padx=5, pady=5)
    receipt_entry = tk.Entry(root, state='readonly')
    receipt_entry.grid(row=1, column=1, padx=5, pady=5)

    # Item Selection
    tk.Label(root, text="Select Item:").grid(row=2, column=0, padx=5, pady=5)
    item_var = tk.StringVar(value="Item")
    item_menu = ttk.Combobox(root, textvariable=item_var, values=list(items.keys()))
    item_menu.grid(row=2, column=1, padx=5, pady=5)

    # Quantity
    tk.Label(root, text="Quantity:").grid(row=3, column=0, padx=5, pady=5)
    quantity_entry = tk.Entry(root)
    quantity_entry.grid(row=3, column=1, padx=5, pady=5)
    quantity_entry.insert(0, "1")

    # Cart
    tk.Label(root, text="Cart:").grid(row=4, column=0, padx=5, pady=5)
    cart_list = tk.Listbox(root)
    cart_list.grid(row=4, column=1, padx=5, pady=5)

    # Buttons
    tk.Button(root, text="Add to Cart", command=add_to_cart).grid(row=5, column=0, padx=5, pady=5)
    tk.Button(root, text="Remove from Cart", command=remove_from_cart).grid(row=5, column=1, padx=5, pady=5)

    # Add-ons
    tk.Label(root, text="Add-ons:").grid(row=6, column=0, padx=5, pady=5)
    addon_vars = {addon: tk.IntVar() for addon in addons.keys()}
    for i, (addon, price) in enumerate(addons.items()):
        check = tk.Checkbutton(root, text=f"{addon} @ ${price}", variable=addon_vars[addon],
                               command=lambda a=addon, p=price: select_addon(a, p))
        check.grid(row=7 + i, column=1, sticky='w', padx=5, pady=5)

    # Total Cost
    total_label = tk.Label(root, text="Total: $0.00")
    total_label.grid(row=9, column=1, padx=5, pady=5)

    # Order Buttons
    tk.Button(root, text="Proceed Order", command=proceed_order).grid(row=10, column=0, padx=5, pady=5)
    tk.Button(root, text="Cancel Order", command=reset_order).grid(row=10, column=1, padx=5, pady=5)
    tk.Button(root, text="Delete Order", command=delete_order).grid(row=11, column=1, padx=5, pady=5)

    # Exit Button

    tk.Button(root, text="Exit", command=root.quit).grid(row=12, column=1, columnspan=2, padx=5, pady=5)

    # Order Table
    cols = ("Date / Time", "Customer Name", "Receipt Number", "Items", "Total")
    table = ttk.Treeview(root, columns=cols, show='headings')
    table.grid(row=13, column=0, columnspan=2, padx=5, pady=5)
    for col in cols:
        table.heading(col, text=col)

create_widgets(root)


initialize_database()
update_table()
root.mainloop()
