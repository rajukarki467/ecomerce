from urllib.parse import quote_plus
import pymongo
username = quote_plus('raju')
password = quote_plus('Admin')
cluster = quote_plus('weshop.wq4umeo.mongodb.net')
url = 'mongodb+srv://' + username + ':' + password + '@' + cluster

my_client = pymongo.MongoClient(url)
# First define the database name
dbname = my_client['weshop']

# Now get/create collection name (remember that you will see the database in your mongodb cluster only after you create a collection
collection_name = dbname["medicinedetails"]


#let's create two documents
medicine_1 = {
    "medicine_id": "RR000123456",
    "common_name" : "Paracetamol",
    "scientific_name" : "",
    "available" : "Y",
    "category": "fever"
}
medicine_2 = {
    "medicine_id": "RR000342522",
    "common_name" : "Metformin",
    "scientific_name" : "",
    "available" : "Y",
    "category" : "type 2 diabetes"
}
# Insert the documents
# collection_name.insert_many([medicine_1,medicine_2])