from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError


class Categorie(models.Model):
    model_name = models.CharField(max_length=200)

    def __str__(self):
        return self.model_name


class Color(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Filter_Price(models.Model):
    Filter_Price_Choices = (
        ('100 TO 1000', '1000 TO 2000'),
        ('200 TO 3000', '3000 TO 4000'),
        ('4000 TO 10000', '10000 To 30000'),
    )
    price = models.CharField(choices=Filter_Price_Choices, max_length=90)


class Product(models.Model):
    STOCK_CHOICES = (
        ('IN STOCK', 'IN STOCK'),
        ('OUT OF STOCK', 'OUT OF STOCK')
    )

    unique_id = models.CharField(
        unique=True, max_length=200, null=True, blank=True)
    image = models.ImageField(upload_to='Product_images/img')
    name = models.CharField(max_length=60)
    price = models.FloatField()
    description = models.CharField(max_length=500)
    quantity = models.PositiveIntegerField(default=0)  # ✅ Stock quantity
    # ✅ Auto-updated stock status
    stock = models.CharField(choices=STOCK_CHOICES,
                             max_length=200, editable=False)
    added_date = models.DateTimeField(default=timezone.now)

    categorie = models.ForeignKey('Categorie', on_delete=models.CASCADE)
    color = models.ForeignKey('Color', on_delete=models.CASCADE)
    filter_price = models.ForeignKey('Filter_Price', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        """✅ Auto-update stock status based on quantity."""
        self.stock = 'IN STOCK' if self.quantity > 0 else 'OUT OF STOCK'

        # Unique ID generation
        if not self.unique_id and self.added_date:
            if not self.id:
                super().save(*args, **kwargs)
            self.unique_id = self.added_date.strftime(
                '75%Y%m%d23') + str(self.id)

        super().save(*args, **kwargs)

    def restock(self, amount):
        """✅ Restock the product by increasing quantity."""
        self.quantity += amount
        self.save()

    def reduce_stock(self, amount):
        """✅ Reduce stock when an order is placed."""
        print(
            # Debug print
            f"Before reducing stock for {self.name}: Available {self.quantity}, Reducing by {amount}")
        if self.quantity >= amount:
            self.quantity -= amount
        else:
            self.quantity = 0  # Prevent negative stock
        self.save()  # Save the updated stock
        # Debug print
        print(
            f"After reducing stock for {self.name}: Available {self.quantity}")

    def __str__(self):
        return self.name


class images(models.Model):
    image = models.ImageField(upload_to='Product_images/img')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return self.image


class tag(models.Model):
    name = models.CharField(max_length=200)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class CustomUser(models.Model):
    email = models.EmailField(unique=True, validators=[
                              EmailValidator(message="Enter a valid email address.")])

    def clean(self):
        email_exists = CustomUser.objects.exclude(
            pk=self.pk).filter(email=self.email).exists()
        if email_exists:
            raise ValidationError(
                {'email': 'This email address is already in use.'})


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Cash on Delivery', 'Cash on Delivery'),
        # Add more payment methods as needed
    )

    product = models.ForeignKey(
        Product, related_name='orders', on_delete=models.CASCADE, default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100, default='')
    lastname = models.CharField(max_length=100, default='')
    address = models.TextField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    phone = models.IntegerField(default='0')
    email = models.EmailField(max_length=100, default='')
    amount = models.CharField(max_length=20, default=(0.0))
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(default=timezone.now)
    deleted = models.BooleanField(default=False)
    payment_done = models.BooleanField(default=False)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default='Cash on Delivery')

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

    def reduce_stock(self):
        """Reduce the stock when the order is placed."""
        if self.product.quantity >= self.quantity:
            self.product.quantity -= self.quantity
            self.product.save()
        else:
            raise ValidationError(
                f"Not enough stock available for {self.product.name}!")

    def save(self, *args, **kwargs):
        # Remove stock reduction from here
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    images = models.ImageField(
        upload_to="Product_images/Order_Img", default='', blank=True)
    # Consider using IntegerField
    quantity = models.CharField(max_length=20, default='0')
    # Consider using DecimalField
    price = models.CharField(max_length=20, default='0')
    # Consider using DecimalField
    total = models.CharField(max_length=100, default='0')

    def __str__(self):
        return f"{self.order.user.username} - {self.product.name}"

    def calculate_total(self):
        """Calculate the total price for this order item."""
        return float(self.price) * int(self.quantity)


class Delivery(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    # Add other fields related to deliveries


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add other fields related to wishlist


class CartManager(models.Manager):
    pass


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CartManager()


class ProductReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class ESEWATransaction(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    # Link transaction to an order
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=50, default='eSewa')
    payment_date = models.DateTimeField(auto_now_add=True)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"eSewa Transaction {self.transaction_id} - {self.status}"

    @property
    def user_first_name(self):
        return self.user.first_name if self.user else ""

    @property
    def user_last_name(self):
        return self.user.last_name if self.user else ""
