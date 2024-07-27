
document.addEventListener('DOMContentLoaded', function () {
    var carouselElement = document.querySelector('#carouselExampleControls');
    var carousel = new bootstrap.Carousel(carouselElement, {
        interval: false // Disable automatic cycling
    });

    carouselElement.addEventListener('mouseenter', function () {
        carousel.cycle();
    });

    carouselElement.addEventListener('mouseleave', function () {
        carousel.pause();
    });

    // Function to fetch and update stock status for each product
    function fetchAndUpdateStockStatus(productId) {
        fetch(`/check_stock/${productId}/`)
            .then(response => response.json())
            .then(data => {
                const stockStatusElement = document.getElementById(`stock-status-${productId}`);
                if (stockStatusElement) {
                    stockStatusElement.innerText = data.message;
                    stockStatusElement.classList.remove('out-of-stock', 'limited-stock', 'in-stock'); // Clear previous classes
                    if (data.message === 'Out of Stock') {
                        stockStatusElement.classList.add('out-of-stock');
                    } else if (data.message === 'Limited Stock') {
                        stockStatusElement.classList.add('limited-stock');
                    } else {
                        stockStatusElement.classList.add('in-stock');
                    }
                }
            })
            .catch(error => console.error(`Error fetching stock status for product ${productId}:`, error));
    }

    // Update stock status for products in different sections
    const productElements = document.querySelectorAll('.card-body');

    productElements.forEach(function (productElement) {
        const productId = productElement.dataset.productId;
        fetchAndUpdateStockStatus(productId); // Fetch and update stock status for each product
    });

    // Example of how to handle recommended products separately (if needed)
    const ProductElements = document.querySelectorAll('.product_list, .latest-product, .recommended-product');

    ProductElements.forEach(function (productElement) {
        const productId = productElement.dataset.productId;
        fetchAndUpdateStockStatus(productId); // Fetch and update stock status for recommended products
    });



    // Add any additional sections as needed

    productElements.forEach(function (productElement) {
        productElement.addEventListener('click', function () {
            const productId = productElement.dataset.productId;
            logInteraction('click', productId);
        });
    });

    function logInteraction(interactionType, productId) {
        fetch('/log-interaction/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ interaction_type: interactionType, product_id: productId })
        })
            .then(response => response.json())
            .then(data => {
                if (data.recommended_products) {
                    updateRecommendedProducts(data.recommended_products);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function updateRecommendedProducts(products) {
        const container = document.querySelector('#recommended-products-container');
        container.innerHTML = '';

        products.forEach(product => {
            const productHTML = `
                <div class="col-md-4" style="width: 100%;">
                    <div class="card" style="border: 1px solid #ededed;">
                        <div class="card-body text-center" data-product-id="${product.id}">
                            <a href="/product-detail/${product.id}" class="btn btn-link"></a>
                            <div class="item">
                                <h5 class="fw-bold text-uppercase">${product.name}</h5>
                                <img class="thumbnail" src="${product.image_url}" alt="${product.name}" height="150px" width="150px">
                                <div class="mt-3">
                                    <span class="fw-bold">${product.name}</span><br>
                                    <span class="fs-5">Rs. ${product.discounted_price}</span>
                                    <span class="fs-6">${average_rating}</span><br>
                                    <span class="fs-6" id="stock-status-${product.id}"></span>
                                </div>
                            </div>
                            <div class="d-flex justify-content-between mt-3">
                                <i class="fa fa-shopping-cart" style="color: gray; cursor: pointer;"></i>
                                <a href="/product-detail/${product.id}" class="btn btn-primary" style="background-color: rgb(181, 76, 76);">More Details</a>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            container.innerHTML += productHTML;
            fetchAndUpdateStockStatus(product.id); // Update stock status for this product in the recommendations
        });
    }

    $(document).ready(function () {
        var owl = $('#slider1');
        owl.owlCarousel({
            items: 4,
            margin: 10,
            loop: true,
            nav: true,
            autoplay: false
        });

        $('#slider1').hover(
            function () {
                owl.trigger('play.owl.autoplay', [1000]);
            },
            function () {
                owl.trigger('stop.owl.autoplay');
            }
        );
    });
});

