# import os
# import pickle
# import pandas as pd

# # Define the paths to your model and dataset
# model_dir = r'C:\Users\asus\OneDrive\Desktop\New folder (2)'
# data_file = r'C:\Users\asus\OneDrive\Desktop\New folder (2)\sample-data.csv'

# # Load the saved model and result dictionary
# with open(os.path.join(model_dir, 'tfidf_vectorizer.pkl'), 'rb') as f:
#     tfidf_vectorizer = pickle.load(f)

# with open(os.path.join(model_dir, 'result_dict.pkl'), 'rb') as f:
#     result_dict = pickle.load(f)

# # Load the dataset (ensure it has the same structure as the one used for training)
# ds = pd.read_csv(data_file)

# # Function to get item description
# def get_product_details(id):
#     product = ds.loc[ds['id'] == id].iloc[0]
#     return {
#         'id': product['id'],
#         'name': product['title'],
#         'image_url': product['image_url'],
#         'discounted_price': product['discounted_price'],
#         'average_rating': product['average_rating'],
#         'stock_status': product['stock_status']
#     }

# # Recommendation function
# def recommend(item_id, num=10):
#     recs = result_dict[item_id][:num]
#     recommendations = []
#     for rec in recs:
#         if rec[0] > 0.1:
#             product_details = get_product_details(rec[1])
#             recommendations.append(product_details)
#     return recommendations


import os
import pickle
import pandas as pd

# Define the paths to your model and dataset
model_dir = r'C:\Users\asus\OneDrive\Desktop\New folder (2)'
data_file = r'C:\Users\asus\OneDrive\Desktop\New folder (2)\sample-data.csv'

# Load the saved model and result dictionary
with open(os.path.join(model_dir, 'tfidf_vectorizer.pkl'), 'rb') as f:
    tfidf_vectorizer = pickle.load(f)

with open(os.path.join(model_dir, 'result_dict.pkl'), 'rb') as f:
    result_dict = pickle.load(f)

# Load the dataset (ensure it has the same structure as the one used for training)
ds = pd.read_csv(data_file)

# Print the columns to debug
print(ds.columns)

# Function to get item details
def get_product_details(product_id):
    try:
        product = ds.loc[ds['id'] == product_id].iloc[0]
        return {
            'id': product['id'],
            'title': product['title'],
            'image_url': product['product_image'],  # Update according to your dataset column names
            'discounted_price': product['discounted_price'],
            'average_rating': product['average_rating'],
            'stock_status': product['stock_status']
        }
    except IndexError:
        print(f"Product with id {product_id} not found.")
        return None
    except KeyError as e:
        print(f"KeyError: {e}")
        return None

# Recommendation function
def recommend(item_id, num=10):
    if item_id not in result_dict:
        print(f"No recommendations found for item_id {item_id}.")
        return []
    recs = result_dict[item_id][:num]
    recommendations = []
    for rec in recs:
        if rec[0] > 0.1:
            product_details = get_product_details(rec[1])
            if product_details:
                recommendations.append(product_details)
    print(f"Recommendations generated: {recommendations}")  # Debug print
    return recommendations