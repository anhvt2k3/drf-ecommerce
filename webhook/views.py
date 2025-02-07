from rest_framework import generics
from rest_framework.response import Response

from subscription.models import Invoice, Subscription
from subscription.serializers import InvoiceSerializer
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
        
        # Handle the event
        if event.type == 'checkout.session.completed':
            return self.handle_successful_payment(event.data.object)

        elif event.type == 'payment_intent.payment_failed':
            return self.handle_failed_payment(event.data.object)
        
        elif event.type == 'customer.created':
            pass
        
        elif event.type == 'invoice.paid':
            return self.handle_invoice_paid(event.data.object)
        
        #: also happens on subscription renewal
        elif event.type == 'invoice.created':
            return self.handle_invoice_creation(event.data.object)
        
        elif event.type == 'customer.subscription.created':
            return self.handle_subscription_creation(event.data.object)

        #: subscription renewal happens here 
        #@ (other updates too mabe)
        elif event.type == 'customer.subscription.updated':
            pass
        
        elif event.type == 'customer.subscription.deleted':
            return self.handle_subscription_deletion(event.data.object)
            
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Invalid event type.', data=event['type'])
        return Response(data, status=data['status'])

    def handle_subscription_deletion(self, event):
        # print ('SUBSCRIPTION UPDATE')
        stripeSubscription = event
        subscriptionMetadata = stripeSubscription['metadata']
        localSubscription = Subscription.objects.filter(id=subscriptionMetadata['subscription']).first()
        if localSubscription:
            localSubscription.status = 'cancelled'
            localSubscription.stripeSubscriptionID = None
            localSubscription.save()
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Subscription deletion acknowledged.', data=stripeSubscription)
        return Response(data, status=data['status'])

    def handle_subscription_creation(self, event):
        # print ('SUBSCRIPTION UPDATE')
        stripeSubscription = event
        subscriptionMetadata = stripeSubscription['metadata']
        localSubscription = Subscription.objects.filter(id=subscriptionMetadata['subscription']).first()
        if localSubscription:
            localSubscription.status = 'active'
            localSubscription.stripeSubscriptionID = stripeSubscription['id']
            localSubscription.save()
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Subscription creation acknowledged.', data=stripeSubscription)
        return Response(data, status=data['status'])

    def handle_invoice_paid(self, event):
        # print ('INVOICE UPDATE')
        stripeInvoice = event
        subscriptionMetadata = stripeInvoice['subscription_details']['metadata']
        if not Invoice.objects.filter(receipt__id=stripeInvoice['id']).exists():
            serializer = InvoiceSerializer(
                data={'payment': subscriptionMetadata['paymethod'],
                    'subscription': subscriptionMetadata['subscription'],
                    'status': stripeInvoice['status'],
                    'receipt': stripeInvoice}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
            subs = Subscription.objects.filter(id=subscriptionMetadata['subscription']).first()
            subs.paystatus = stripeInvoice['status']
            subs.start_date = timezone.make_aware(datetime.datetime.fromtimestamp(stripeInvoice['lines']['data'][0]['period']['start']))
            subs.expire_date = timezone.make_aware(datetime.datetime.fromtimestamp(stripeInvoice['lines']['data'][0]['period']['end']))
            subs.save()
        data= ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Invoice payment acknowledged.', data=stripeInvoice)
        return Response(data, status=data['status'])
            
    def handle_invoice_creation(self, event):
        # print ('INVOICE UPDATE')
        stripeInvoice = event
        subscriptionMetadata = stripeInvoice['subscription_details']['metadata']
        if not Invoice.objects.filter(receipt__id=stripeInvoice['id']).exists():
            serializer = InvoiceSerializer(
                data={'payment': subscriptionMetadata['paymethod'],
                    'subscription': subscriptionMetadata['subscription'],
                    'status': stripeInvoice['status'],
                    'receipt': stripeInvoice}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
            subs = Subscription.objects.filter(id=subscriptionMetadata['subscription']).first()
            subs.paystatus = 'invoiced'
            subs.save()
            
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Invoice creation acknowledged.', data=stripeInvoice)
        return Response(data, status=data['status'])
    
    def handle_successful_payment(self, event):
        """
        Handle the successful payment logic here.
        """
        #: implement duplicate event check
        #: branch condition -> update subscription pay status
        # print ('PAYMENT UPDATE')
        session = event
        session = session  # Checkout Session object
        order_id = session['metadata']['order_id']
        OrderSerializer().update(Order.objects.filter(id=order_id).first(), {'status':'processing'})
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Payment successful.', data=session)
        return Response(data, status=data['status'])
            

    def handle_failed_payment(self, event):
        """
        Handle the failed payment logic here.
        """
        #: implement duplicate event check
        # print ('PAYMENT UPDATE')
        payment_intent = event
        data = ViewUtils.gen_response(success=True, status=HTTP_200_OK, message='Payment failed. Forget something in your purchase?', data=payment_intent)
        return Response(data, status=data['status'])
            







