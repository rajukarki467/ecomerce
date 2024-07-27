from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Product, CATEGORY_MAP, SearchHistory
import re

# Define common queries and responses
corpus = [
    "Give me men's clothes under 1000",
    "Show me shoes under 500",
    "Find cosmetics under 200",
    "I want women's clothes under 800",
    "What are the latest arrivals?",
    "Can you recommend some products on sale?",
    "Show me products with high ratings",
    "I need products in the 'electronics' category"
]

responses = [
    "Here are men's clothes priced under 1000.",
    "Check out these shoes priced under 500.",
    "We have cosmetics available under 200.",
    "Here are women's clothes priced under 800.",
    "Here are the latest arrivals.",
    "Check out our products on sale.",
    "Here are some highly rated products.",
    "Here are products in the electronics category."
]

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(corpus)

def get_response(user_message, user=None):
    response = ""
    products = []

    # Handle general greetings and questions
    greetings = ["hi", "hello", "how are you", "what is your name"]
    if user_message.lower() in greetings:
        if user_message.lower() in ["hi", "hello"]:
            response = "Hello! How can I assist you today?"
        elif user_message.lower() == "how are you":
            response = "I'm just a bot, but I'm here to help you!"
        elif user_message.lower() == "what is your name":
            response = "I'm your friendly chatbot assistant."

    # Handle common queries using TF-IDF and cosine similarity
    else:
        query_vec = vectorizer.transform([user_message])
        cosine_similarities = cosine_similarity(query_vec, X)
        response_idx = cosine_similarities.argmax()
        common_response = responses[response_idx]

        # If the response is a common query, return it
        if cosine_similarities.max() > 0.5:  # Threshold to ensure relevance
            response = common_response
        else:
            # Extract category, price, and brand from user message
            category = None
            brand = None
            price_min = None
            price_max = None

            # Check for specific category keywords
            for cat in CATEGORY_MAP.keys():
                if cat in user_message.lower():
                    category = CATEGORY_MAP[cat]
                    break

            # Check for specific brand keywords
            brands = ["jordyn", "sugar", "goldmind", "brand4", "brand5"]  # Replace with actual brand names
            for br in brands:
                if br in user_message.lower():
                    brand = br
                    break

            # Extract price range if mentioned
            price_range = re.search(r'(\d+)\s*-\s*(\d+)', user_message)
            if price_range:
                price_min = float(price_range.group(1))
                price_max = float(price_range.group(2))
            else:
                price_min = re.search(r'over\s*(\d+)', user_message)
                price_max = re.search(r'under\s*(\d+)', user_message)
                if price_min:
                    price_min = float(price_min.group(1))
                if price_max:
                    price_max = float(price_max.group(1))

            # Filter products based on category, brand, and price
            product_queryset = Product.objects.all()
            if category:
                product_queryset = product_queryset.filter(category=category)
            if brand:
                product_queryset = product_queryset.filter(brand__icontains=brand)
            if price_min is not None and price_max is not None:
                product_queryset = product_queryset.filter(selling_price__gte=price_min, selling_price__lte=price_max)
            elif price_min is not None:
                product_queryset = product_queryset.filter(selling_price__gte=price_min)
            elif price_max is not None:
                product_queryset = product_queryset.filter(selling_price__lte=price_max)

            # Optionally include search history logging
            if user:
                SearchHistory.objects.create(user=user, query=user_message)

            products = list(product_queryset.values('id', 'title', 'selling_price', 'discounted_price', 'description', 'brand', 'category', 'product_image', 'average_rating', 'stock_status'))

            if not products:
                response = "Sorry, no products found matching your criteria."
            else:
                response = "Here are some products you might like."

    return response, products
