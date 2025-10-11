import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PaymentModal = ({ isOpen, onClose, onSuccess, requestData }) => {
  const [step, setStep] = useState(1); // 1: Details, 2: Payment Form, 3: Processing, 4: Success/Error
  const [pricing, setPricing] = useState(null);
  const [paymentIntent, setPaymentIntent] = useState(null);
  const [paymentForm, setPaymentForm] = useState({
    payment_method: 'credit_card',
    card_number: '',
    card_expiry: '',
    card_cvc: '',
    cardholder_name: ''
  });
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [paymentResult, setPaymentResult] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchPricing();
    }
  }, [isOpen]);

  const fetchPricing = async () => {
    try {
      const response = await axios.get(`${API}/payments/pricing`);
      setPricing(response.data);
    } catch (error) {
      console.error('Error fetching pricing:', error);
      setError('Failed to load pricing information');
    }
  };

  const createPaymentIntent = async () => {
    try {
      const paymentData = {
        transcript_count: 1,
        university_from: requestData.university_from,
        university_to: requestData.university_to,
        document_type: requestData.document_type || 'transcript'
      };

      const response = await axios.post(`${API}/payments/create-intent`, paymentData, {
        withCredentials: true
      });

      setPaymentIntent(response.data);
      setStep(2);
    } catch (error) {
      console.error('Error creating payment intent:', error);
      setError('Failed to create payment. Please try again.');
    }
  };

  const processPayment = async () => {
    if (!paymentIntent) return;
    
    setProcessing(true);
    setError(null);
    setStep(3);

    try {
      const paymentRequest = {
        payment_id: paymentIntent.payment_id,
        payment_method: paymentForm.payment_method,
        card_number: paymentForm.card_number,
        card_expiry: paymentForm.card_expiry,
        card_cvc: paymentForm.card_cvc,
        card_brand: getCardBrand(paymentForm.card_number),
        cardholder_name: paymentForm.cardholder_name
      };

      const response = await axios.post(`${API}/payments/process`, paymentRequest, {
        withCredentials: true
      });

      setPaymentResult(response.data);
      
      if (response.data.success) {
        setStep(4);
        // Call success callback with payment ID
        setTimeout(() => {
          onSuccess(paymentIntent.payment_id);
        }, 2000);
      } else {
        setError(response.data.error || 'Payment failed');
        setStep(2); // Go back to payment form
      }
    } catch (error) {
      console.error('Payment processing error:', error);
      setError(error.response?.data?.detail || 'Payment processing failed');
      setStep(2);
    } finally {
      setProcessing(false);
    }
  };

  const getCardBrand = (cardNumber) => {
    const number = cardNumber.replace(/\s/g, '');
    if (number.startsWith('4')) return 'visa';
    if (number.startsWith('5')) return 'mastercard';
    if (number.startsWith('3')) return 'amex';
    return 'visa';
  };

  const formatCardNumber = (value) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = matches && matches[0] || '';
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }
    if (parts.length) {
      return parts.join(' ');
    } else {
      return v;
    }
  };

  const formatExpiry = (value) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    if (v.length >= 2) {
      return v.substring(0, 2) + '/' + v.substring(2, 4);
    }
    return v;
  };

  const handleCardNumberChange = (e) => {
    const formatted = formatCardNumber(e.target.value);
    setPaymentForm({ ...paymentForm, card_number: formatted });
  };

  const handleExpiryChange = (e) => {
    const formatted = formatExpiry(e.target.value);
    setPaymentForm({ ...paymentForm, card_expiry: formatted });
  };

  const resetModal = () => {
    setStep(1);
    setPaymentIntent(null);
    setPaymentForm({
      payment_method: 'credit_card',
      card_number: '',
      card_expiry: '',
      card_cvc: '',
      cardholder_name: ''
    });
    setProcessing(false);
    setError(null);
    setPaymentResult(null);
  };

  const handleClose = () => {
    resetModal();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-lg w-full mx-4 max-h-screen overflow-y-auto">
        
        {/* Step 1: Payment Details */}
        {step === 1 && (
          <>
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-900">Payment Required</h3>
              <button onClick={handleClose} className="text-gray-400 hover:text-gray-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4 mb-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">Transcript Request Details</h4>
                <div className="text-sm text-blue-800 space-y-1">
                  <p><strong>From:</strong> {requestData.university_from}</p>
                  <p><strong>To:</strong> {requestData.university_to}</p>
                  <p><strong>Document Type:</strong> {requestData.document_type}</p>
                </div>
              </div>

              {pricing && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-3">Payment Breakdown</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Transcript Fee:</span>
                      <span>${pricing.transcript_fee.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Processing Fee:</span>
                      <span>${pricing.processing_fee.toFixed(2)}</span>
                    </div>
                    <hr className="my-2" />
                    <div className="flex justify-between font-semibold">
                      <span>Total:</span>
                      <span>${pricing.total_per_transcript.toFixed(2)} {pricing.currency}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="text-xs text-gray-500">
                <p>• Payment is required before your transcript request is sent to the issuing university</p>
                <p>• Secure payment processing with 256-bit encryption</p>
                <p>• Refunds available if request is cancelled before processing</p>
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={handleClose}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg font-medium transition duration-200"
              >
                Cancel
              </button>
              <button
                onClick={createPaymentIntent}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition duration-200"
              >
                Continue to Payment
              </button>
            </div>
          </>
        )}

        {/* Step 2: Payment Form */}
        {step === 2 && (
          <>
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-900">Payment Information</h3>
              <button onClick={handleClose} className="text-gray-400 hover:text-gray-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            )}

            <form onSubmit={(e) => { e.preventDefault(); processPayment(); }} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cardholder Name
                </label>
                <input
                  type="text"
                  required
                  value={paymentForm.cardholder_name}
                  onChange={(e) => setPaymentForm({...paymentForm, cardholder_name: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Card Number
                </label>
                <input
                  type="text"
                  required
                  maxLength="19"
                  value={paymentForm.card_number}
                  onChange={handleCardNumberChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="1234 5678 9012 3456"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Expiry Date
                  </label>
                  <input
                    type="text"
                    required
                    maxLength="5"
                    value={paymentForm.card_expiry}
                    onChange={handleExpiryChange}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="MM/YY"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    CVC
                  </label>
                  <input
                    type="text"
                    required
                    maxLength="4"
                    value={paymentForm.card_cvc}
                    onChange={(e) => setPaymentForm({...paymentForm, card_cvc: e.target.value.replace(/\D/g, '')})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="123"
                  />
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-600">
                <div className="flex items-center mb-1">
                  <svg className="w-4 h-4 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  Secure Payment
                </div>
                <p>Your payment information is encrypted and secure. Total: ${paymentIntent?.amount_details?.total_amount}</p>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg font-medium transition duration-200"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={processing}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition duration-200 disabled:opacity-50"
                >
                  {processing ? 'Processing...' : `Pay $${paymentIntent?.amount_details?.total_amount}`}
                </button>
              </div>
            </form>
          </>
        )}

        {/* Step 3: Processing */}
        {step === 3 && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Processing Payment</h3>
            <p className="text-gray-600">Please wait while we process your payment...</p>
            <p className="text-sm text-gray-500 mt-2">This may take a few seconds</p>
          </div>
        )}

        {/* Step 4: Success/Error */}
        {step === 4 && (
          <div className="text-center py-8">
            {paymentResult?.success ? (
              <>
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-green-900 mb-2">Payment Successful!</h3>
                <p className="text-gray-600 mb-4">Your payment has been processed successfully.</p>
                <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm">
                  <p><strong>Transaction ID:</strong> {paymentResult.transaction_id}</p>
                  <p><strong>Amount:</strong> ${paymentResult.amount_paid} {paymentResult.currency}</p>
                </div>
                <p className="text-sm text-gray-500 mt-4">
                  You will now be redirected to create your transcript request...
                </p>
              </>
            ) : (
              <>
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-red-900 mb-2">Payment Failed</h3>
                <p className="text-gray-600 mb-4">{error}</p>
                <button
                  onClick={() => setStep(2)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition duration-200"
                >
                  Try Again
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentModal;