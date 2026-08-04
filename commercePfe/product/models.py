from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
User = get_user_model()

class Product(models.Model):
    MAIN_CATEGORIES = [
        ('clothing', 'Clothing'),
        ('shoes', 'Shoes'),
        ('bags', 'Bags'),
        ('accessories','Accessories'),
        ('self-care', 'Self-care'),
        ('school', 'School'),
        ('newborn', 'Newborn'),
        ('toys', 'Toys'),
    ]   

    TARGET_AUDIENCE_CHOICES = [
        ('men', 'Men'),
        ('women', 'Women'),
        ('girls', 'Girls'),
        ('boys', 'Boys'),
        ('babies', 'Babies'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  
    seller = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    main_category = models.CharField(max_length=50, choices=MAIN_CATEGORIES)
    category = models.CharField(max_length=100)
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE_CHOICES)  # Added gender field
    image = models.ImageField(upload_to='products/')  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category}, {self.target_audience})"

class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid'),
    ]
    DELIVERY_STATUS_CHOICES = [
        ('not_delivered', 'Not Delivered'),
        ('in_progress', 'In Progress'),
        ('delivered_not_confirm', 'Delivered Not Confirmed'),
        ('delivered_confirm', 'Delivered Confirmed'),
        ('cancelled', 'Cancelled'),
        ('return_requested', 'Return Requested'),
        ('refunded', 'Refunded'),
    ]

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='not_paid')
    delivery_status = models.CharField(max_length=50, choices=DELIVERY_STATUS_CHOICES, default='not_delivered')
    payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.full_name}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    seller_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price per unit at time of order

    @property
    def total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"