from django.db import models
from product.models import Order  # ou le bon chemin vers ton modèle Order
from delivery.models import CustomUser  # ou le bon chemin vers CustomUser

class DeliveryAssignment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    delivery_person = models.ForeignKey(
        CustomUser,
        limit_choices_to={'is_livreur': True},
        on_delete=models.CASCADE
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order.id} assigned to {self.delivery_person.username}"
