from django.db import models
from django.utils.safestring import mark_safe
from accounts.models import *
from django.utils import timezone
# Create your models here.

class   Size(models.Model):
    size = models.CharField(max_length=50)
    
    def __str__(self):
        return self.size

def generic_directory_path(instance,filename):
    model_name = instance.__class__.__name__.lower()

    pk = instance.pid if hasattr(instance,'pid') else None

    if pk:
        return f'{model_name}_{pk}/{filename}'
    else:
        return f'{model_name}_unknown/{filename}'


class Category(models.Model):
    c_id = models.BigAutoField(unique=True, primary_key=True)
    c_name = models.CharField(max_length = 50, null=True)
    c_image = models.ImageField(upload_to='category',default='category.jpg')
    is_blocked = models.BooleanField(default=False)
    class Meta:
        verbose_name_plural = "Categories"

    def category_image(self):
        if self.c_image:
            return mark_safe('<img src="%s" width="50" height="50" />' % (self.c_image.url))
        else:
            return "No Image Available"


    def __str__(self):
        return self.c_name
    
class Subcategory(models.Model):
    sid = models.BigAutoField(unique=True, primary_key=True)
    sub_name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, related_name="subcategories", db_column='c_id')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sub_name}"


class Product(models.Model):
    p_id = models.BigAutoField(unique=True, primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, related_name="products")
    sub_category = models.ForeignKey(Subcategory, on_delete=models.CASCADE, null=True, related_name="products")
    title = models.CharField(default="product")
    description = models.TextField(null=True, blank=True, default="This is the product")
    specifications = models.TextField(null=True, blank=True)
    shipping = models.TextField(null=True)
    availability = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)
    latest = models.BooleanField(default=False)
    popular = models.BooleanField(default=False)
    image = models.ImageField(upload_to='product_images', default='product.jpg')

    class Meta:
        verbose_name_plural = "Products"
        
    def __str__(self):
        return self.title

   

class ProductImages(models.Model):
    images = models.ImageField(upload_to='product_images', default='product.jpg')
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Product Images'

class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_attributes')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, default=None, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1.99)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.IntegerField(default=1)
    is_blocked = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    related = models.ManyToManyField('self', blank=True)
    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.size:
            return f"{self.product.title} - {self.size.size} - Price: {self.price}"
        else:
            return f"{self.product.title} - No Size - Price: {self.price}"

    def reduce_stock(self, quantity):
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False

    def check_stock(self, quantity):
        return self.stock >= quantity


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"
    
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    quantity = models.PositiveBigIntegerField(default=1)
    is_deleted = models.BooleanField(default=False)
    size = models.CharField(max_length=10, blank=True, null=True)

    def product_image(self):
        first_image = self.product.p._images.first()
        if first_image:
            return first_image.Images.url
        return None
    
    def __str__(self):
        return f'{self.quantity} x {self.product} in {self.cart}'
    