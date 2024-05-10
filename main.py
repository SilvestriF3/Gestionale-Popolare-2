#!.\venv\Scripts\python.exe

from flask import Flask, render_template, jsonify, request
import json
#import time
import threading
from core import *
import os

connection = sqlite3.connect("./data/myDatabase.db", timeout=10, check_same_thread=False)
app = Flask(__name__, static_folder="assets")


@app.route("/")
def gestionale():
    return render_template('./gestionale/gestionale-popolare.html')

#send the menu list
@app.route("/api/menu")
def menu():
    f = open("./data/lista_menu.json", "r")
    data = f.read()
    f.close()
    return jsonify(data)

#send open orders to display
@app.route("/api/ordersList")
def orderList():
    data = retrieveOrderList(connection)
    return jsonify(data)

#send open orders to display
@app.route("/api/completedOrdersList")
def completedOrderList():
    data = retrieveRecentCompletedOrderList(connection)
    return jsonify(data)

#send open orders to display
@app.route("/api/requestOrderNumber")
def getOrderNumber():
    data = {'orderId': retrieveOrderNumber(connection)}
    return jsonify(data)

@app.route("/api/getItemsByOrderId")
def getOrderItems():
    orderId = request.args.get('orderId')
    orderType = request.args.get('orderType')
    data = {'items': retrieveOrderItems(connection, orderId, orderType)}
    return jsonify(data)

#register order to database (fill the order data)
@app.route("/api/orders", methods = ['POST'])
def orders():
    responseData = {'status': ""}
    if request.method == 'POST':
        order = request.get_json()
        dbStatus = registerOrderToDatabase(connection, order)
        if (dbStatus == 0):
            #start print thread
            t = threading.Thread(target=printCommand, args=(connection, order), daemon=True)
            t.start()
            responseData["status"] = "success"
        print(order)
    return jsonify(responseData)

#update an order status and/or table id
@app.route("/api/orderDataUpdate", methods = ['POST'])
def orderDataUpdate():
    if request.method == 'POST':
        r = request.get_json()
        print(r)
        updateData(connection, r)
    return "{}"

@app.route("/api/orderRequestReprint", methods = ['POST'])
def orderRequestReprint():
    if request.method == 'POST':
        r = request.get_json()
        orderId = request.args.get('orderId')
        orderType = request.args.get('orderType')
        print(r)
        requestReprint(connection, orderId, orderType)
    return "{}"

@app.route("/ordini")
def getOrders():
    return render_template('./gestionale/gestionale-popolare-gestione-ordini.html')

@app.route("/summary")
def getSummary():
    return render_template('./gestionale/gestionale-popolare-summary.html')

#send open orders to display
@app.route("/api/summaryData")
def summaryData():
    data = retrieveSummaryData(connection)
    return jsonify(data)

#archive order and items
@app.route("/api/close_archive", methods = ['POST'])
def archive():
    responseData = {'status': ""}
    if request.method == 'POST':
        dbStatus = archiveDatabaseData(connection)
        if (dbStatus == 0):
            responseData["status"] = "success"
        elif (dbStatus == 1):
            responseData["status"] = "orderOpen"
        elif (dbStatus == 2):
            responseData["status"] = "noOrder"
    return jsonify(responseData)

#print daily report
@app.route("/api/print_report", methods = ['POST'])
def print_report():
    responseData = {'status': ""}
    if request.method == 'POST':
        selectedDate = request.get_json()
        printStatus = printReport(connection, selectedDate)
        #status = archiveDatabaseData(connection)
        #if (status == 0):
        #    responseData["status"] = "success"
        #elif (status == 1):
        #    responseData["status"] = "orderOpen"
        #elif (status == 2):
        #    responseData["status"] = "noOrder"
    return jsonify(responseData)

#useless function (to remove)
def startServer():
    print(connection.total_changes)
    #test functions
    orderInJson = """{
  "operatorId": "cassa1",
  "datetime": "2024-03-06 15:28:07",
  "totalValue": 100,
  "paymentType": "cash",
  "items": [ {
  "itemId": 10,
  "quantity": 2,
  "notes": "some notes"
  },
  {
  "itemId": 11,
  "quantity": 1,
  "notes": "more notes"
  },
   {
  "itemId": 13,
  "quantity": 1,
  "notes": "more notes"
  },
  {
  "itemId": 12,
  "quantity": 1,
  "notes": "more notes"
  }]
}"""
    orderInJson = json.loads(orderInJson)
    registerOrderToDatabase(connection, orderInJson)


    #test functions END
    print('Avvio del server...')
    print('Server in esecuzione...')


#utility function
def jsonMenu():
    f = open("./data/lista_menu.json", "r+")
    data = json.loads(f.read())
    i = 1
    for category in data:
       for item in data[category]:
           item["productId"] = i
           print(item)
           i += 1
    f.write(data)
    f.close()

def fillMenu():
    f = open("./data/lista_menu.json", "r")
    data = json.loads(f.read())
    for category in data:
        for item in data[category]:
            item["category"] = category
            sql = ''' INSERT INTO itemProp(name, itemId, itemClass, unitPrice)
                              VALUES(:name, :productId, :category, :price) '''
            cur = connection.cursor()
            cur.execute(sql, item)
            connection.commit()
    f.close()

if __name__ == '__main__':
    data = """{
  "orderId": 20,
  "orderStatus": 2,
  "tableId": 200
}"""
    directory = os.path.dirname(os.path.abspath(__file__))
    print(os.getcwd())
    #prod server
    #from waitress import serve
    #serve(app, host="0.0.0.0", port=5000)
    app.run(threaded=True, debug=True, host="0.0.0.0")

