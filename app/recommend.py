import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q, FloatField, Value as V, Count
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from app.models import *
from .token import user_tokenizer_generate

@login_required
def log_interaction(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        interaction_type = data.get('interaction_type')
        product_id = data.get('product_id')

        if interaction_type and product_id:
            product = get_object_or_404(Product, id=product_id)
            ProductInteraction.objects.create(user=request.user, product=product, interaction_type=interaction_type)

            # Update recommendations based on the interaction
            recommended_products = combined_recommendations(request.user)

            return JsonResponse({'status': 'Interaction logged', 'recommended_products': recommended_products})
        return JsonResponse({'status': 'Invalid data'}, status=400)
    return JsonResponse({'status': 'Invalid method'}, status=405)


def content_based_filtering(user, num_recommendations=8):
    # Fetch user interactions
    interactions = ProductInteraction.objects.filter(user=user)
    user_products = [interaction.product for interaction in interactions]

    if not user_products:
        return []

    # Fetch all products except those the user has already interacted with
    products = list(Product.objects.exclude(id__in=[product.id for product in user_products]))

    if not products:
        print("No products found to recommend")
        return []

    # Combine descriptions with discounted_price and category for TF-IDF
    product_features = [
        f"{product.description} {product.discounted_price} "
        for product in products
    ]
    user_product_features = [
        f"{product.description} {product.discounted_price}"
        for product in user_products
    ]

    # Create TF-IDF matrix for product features
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(product_features)

    # Create TF-IDF matrix for user product features
    user_tfidf_matrix = tfidf_vectorizer.transform(user_product_features)

    # Compute cosine similarities
    cosine_similarities = cosine_similarity(user_tfidf_matrix, tfidf_matrix)

    # Compute average similarity for each product
    avg_similarities = np.mean(cosine_similarities, axis=0)

    # Sort products by similarity and select top recommendations
    similar_product_indices = avg_similarities.argsort()[::-1]

    recommended_products = []
    for idx in similar_product_indices:
        product = products[idx]
        if len(recommended_products) < num_recommendations:
            recommended_products.append(product)

    # Serialize the recommended products
    serialized_recommended_products = [serialize_product(product) for product in recommended_products]
    return serialized_recommended_products


def serialize_product(product):
    return {
        'id': product.id,
        'name': product.title,
        'description': product.description,
        'selling_price': product.selling_price,
        'discounted_price': product.discounted_price,
        'image_url': product.product_image.url if product.product_image else None,
        'brand': product.brand,
        'category': product.category,
    }

def user_based_collaborative_filtering(user, num_recommendations=8):
    other_users = User.objects.exclude(id=user.id)

    user_similarities = []
    for other_user in other_users:
        ratings_user = Rating.objects.filter(user=user)
        ratings_other_user = Rating.objects.filter(user=other_user)

        common_products = set(ratings_user.values_list('product_id', flat=True)) & set(ratings_other_user.values_list('product_id', flat=True))

        if common_products:
            user_ratings = []
            other_user_ratings = []

            for product_id in common_products:
                user_rating = ratings_user.get(product_id=product_id).rating
                other_user_rating = ratings_other_user.get(product_id=product_id).rating

                user_ratings.append(user_rating)
                other_user_ratings.append(other_user_rating)

            similarity = np.dot(user_ratings, other_user_ratings) / (np.linalg.norm(user_ratings) * np.linalg.norm(other_user_ratings))
            user_similarities.append((other_user, similarity))

    user_similarities.sort(key=lambda x: x[1], reverse=True)

    recommended_products = set()

    for similar_user, similarity in user_similarities:
        similar_user_ratings = Rating.objects.filter(user=similar_user, rating__gte=4)

        for rating in similar_user_ratings:
            recommended_products.add(rating.product)

        if len(recommended_products) >= num_recommendations:
            break

    return list(recommended_products)[:num_recommendations]



def get_recommended_products(user,num_recommendations=8):
    search_history = SearchHistory.objects.filter(user=user).values('query').annotate(search_count=Count('query')).order_by('-search_count')
    recommended_products = Product.objects.none()
    
    if search_history.exists():
        frequent_queries = search_history[:5]
        for query in frequent_queries:
            query_str = query['query'].lower()
            query_str = CATEGORY_MAP.get(query_str, query_str)  # Map to category code if it exists
            recommended_products |= Product.objects.filter(
                Q(title__icontains=query_str) |
                Q(description__icontains=query_str) |
                Q(category__icontains=query_str) |
                Q(brand__icontains=query_str),
                quantity__gt=0  # Apply quantity greater than 0 filter
            )
    
    return recommended_products[:num_recommendations]


def combined_recommendations(user, num_recommendations=8):
    collaborative_recs = user_based_collaborative_filtering(user, num_recommendations)
    serialized_collaborative_recs = [serialize_product(product) for product in collaborative_recs]
    

    search_recs= get_recommended_products(user,num_recommendations)
    serialized_search_recs = [serialize_product(product) for product in search_recs]

    content_based_recs = content_based_filtering(user, num_recommendations)

    
    combined_recs = serialized_collaborative_recs + content_based_recs +  serialized_search_recs
    
    # Use a set to track unique products
    seen = set()
    unique_recs = []
    for rec in combined_recs:
        # Convert the dictionary to a tuple of items for hashing
        rec_tuple = tuple(rec.items())
        if rec_tuple not in seen:
            seen.add(rec_tuple)
            unique_recs.append(rec)

    # Limit the number of recommendations to the specified number
    return unique_recs[:num_recommendations]

# def search_view(request):
#     query = request.GET.get('q', '')
#     products = Product.objects.filter(
#         Q(category__icontains=query) |
#         Q(brand__icontains=query) |
#         Q(discounted_price__icontains=query)
#     ) if query else Product.objects.none()

#     product_ids = request.COOKIES.get('product_ids', '')
#     product_count_in_cart = len(set(product_ids.split('|'))) if product_ids else 0

#     word = "Searched Result:"

#     context = {
#         'products': products,
#         'word': word,
#         'product_count_in_cart': product_count_in_cart,
#         'query': query,
#     }
