from rest_framework import generics
from rest_framework.response import Response
from .utils.utils import *
from eco_sys.secrets import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

from order.serializers import OrderSerializer
from order.models import Order

import stripe


class PaymentStripeWebhookView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = []
    
    def post(self, request, *args, **kwargs):
        print ('WEBHOOK CALLED')
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        stripe.api_key = STRIPE_SECRET_KEY
        endpoint_secret = STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Invalid payload.', data=str(e))
            return Response(data, status=data['status'])
        except stripe.error.SignatureVerificationError as e:
            data = ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='Invalid signature.', data=str(e))
            return Response(data, data['status'])
        
        # todo: event of invoice creation

        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            return self.handle_successful_payment(session)

        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            return self.handle_failed_payment(payment_intent)
        
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Invalid event type.', data=event['type'])
        return Response(data, status=data['status'])

    def handle_successful_payment(session):
        """
        Handle the successful payment logic here.
        """
        session = session['data']['object']  # Checkout Session object
        order_id = session['metadata']['order_id']
        OrderSerializer().update(Order.objects.filter(id=order_id).first(), {'status':'processing'})
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Payment successful.', data=session)
        return Response(data, status=data['status'])
            

    def handle_failed_payment(payment_intent):
        """
        Handle the failed payment logic here.
        """
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Payment failed. Forget something in your purchase?', data=payment_intent)
        return Response(data, status=data['status'])
            







