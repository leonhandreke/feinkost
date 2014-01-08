from flask import render_template

from feinkost import app

@app.route('/')
def inventoryitem_list():
    return render_template('inventoryitem_list.html')
