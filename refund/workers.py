import stripe
import eco_sys.secrets as secrets
from order.models import Order

def perform_refund(order : Order):
    try:
        print ("Refunding order: ", order)
        stripe.api_key = secrets.STRIPE_SECRET_KEY
        refund = stripe.Refund.create(
            payment_intent=order.receipt['id'],
            
        )
        print (f"Refund: {refund}")
        if refund.status != 'succeeded':
            return False, Exception("Refund failed.")
        else:
            order.status = 'refunded'
            order.refundd = refund
            order.save()
            return True, None
    except Exception as e:
        return False, e
    