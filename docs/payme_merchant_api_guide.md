# Payme Merchant API Integration Guide

## Overview

Payme Business interacts with a merchant's billing system using
**JSON-RPC 2.0** over **HTTP POST** requests secured with **TLS
(HTTPS)**.

-   Protocol: JSON-RPC 2.0
-   Transport: HTTP 1.1 POST
-   Security: TLS (HTTPS recommended)
-   Parameters: Named parameters only
-   All responses must return **HTTP Status 200**

If the server returns any status other than **200**, Payme treats it as
RPC error **-32400**.

Supported TLS versions: - TLS v1 - TLS v1.1 - TLS v1.2

------------------------------------------------------------------------

# Merchant API Methods

## 1. CheckPerformTransaction

This method checks whether a transaction **can be performed**.

### Request

``` json
{
  "method": "CheckPerformTransaction",
  "params": {
    "amount": 500000,
    "account": {
      "phone": "903595731"
    }
  }
}
```

### Response

``` json
{
  "result": {
    "allow": true
  }
}
```

### Possible Errors

  Code                Description
  ------------------- ----------------------------
  -31001              Invalid amount
  -31050 --- -31099   Invalid account parameters

### Optional Additional Data

``` json
{
  "result": {
    "allow": true,
    "additional": {
      "balance": 5000000
    }
  }
}
```

### Optional Fiscal Data

``` json
{
  "result": {
    "allow": true,
    "detail": {
      "receipt_type": 0,
      "items": [
        {
          "title": "Tomatoes",
          "price": 505000,
          "count": 2,
          "code": "00702001001000001",
          "vat_percent": 15,
          "package_code": "123456"
        }
      ]
    }
  }
}
```

------------------------------------------------------------------------

# 2. CreateTransaction

Creates a transaction in the merchant system.

### Requirements

The implementation must:

-   Store transactions in **persistent storage**
-   Validate account existence
-   Validate payment amount
-   Lock order until payment or cancellation
-   Mark order status as **"waiting for payment"**
-   Prevent order modification

### Timeout Cancellation

Transactions are automatically canceled after **12 hours**.

Timeout reason code: **4**

### Request

``` json
{
  "method": "CreateTransaction",
  "params": {
    "id": "5305e3bab097f420a62ced0b",
    "time": 1399114284039,
    "amount": 500000,
    "account": {
      "phone": "903595731"
    }
  }
}
```

### Response

``` json
{
  "result": {
    "create_time": 1399114284039,
    "transaction": "5123",
    "state": 1
  }
}
```

### Chain Payment Example

``` json
{
  "result": {
    "create_time": 1399114284039,
    "transaction": "5123",
    "state": 1,
    "receivers": [
      {
        "id": "receiver1",
        "amount": 200000
      },
      {
        "id": "receiver2",
        "amount": 300000
      }
    ]
  }
}
```

### Errors

  Code                Description
  ------------------- -------------------------------
  -31001              Invalid amount
  -31008              Operation cannot be performed
  -31050 --- -31099   Invalid account data

------------------------------------------------------------------------

# 3. PerformTransaction

Final step confirming the payment.

### Request

``` json
{
  "method": "PerformTransaction",
  "params": {
    "id": "5305e3bab097f420a62ced0b"
  }
}
```

### Response

``` json
{
  "result": {
    "transaction": "5123",
    "perform_time": 1399114284039,
    "state": 2
  }
}
```

### Errors

  Code     Description
  -------- -------------------------------
  -31003   Transaction not found
  -31008   Operation cannot be performed

------------------------------------------------------------------------

# 4. CancelTransaction

Cancels a transaction (created or completed).

### Request

``` json
{
  "method": "CancelTransaction",
  "params": {
    "id": "5305e3bab097f420a62ced0b",
    "reason": 1
  }
}
```

### Response

``` json
{
  "result": {
    "transaction": "5123",
    "cancel_time": 1399114284039,
    "state": -2
  }
}
```

### Errors

  Code     Description
  -------- -------------------------
  -31003   Transaction not found
  -31007   Order already completed

Refunds are processed through the **merchant cabinet** if
CancelTransaction is implemented.

------------------------------------------------------------------------

# 5. CheckTransaction

Checks transaction status.

### Request

``` json
{
  "method": "CheckTransaction",
  "params": {
    "id": "5305e3bab097f420a62ced0b"
  }
}
```

### Response

``` json
{
  "result": {
    "create_time": 1399114284039,
    "perform_time": 1399114285002,
    "cancel_time": 0,
    "transaction": "5123",
    "state": 2,
    "reason": null
  }
}
```

### Errors

  Code     Description
  -------- -----------------------
  -31003   Transaction not found

------------------------------------------------------------------------

# 6. GetStatement

Returns a list of transactions for reconciliation.

Implementation is **mandatory**.

### Requirements

Transactions must:

-   Be searched by **creation time**
-   Be sorted **ascending by creation time**
-   Include only successfully created transactions

### Request

``` json
{
  "method": "GetStatement",
  "params": {
    "from": 1399114284039,
    "to": 1399120284000
  }
}
```

### Response

``` json
{
  "result": {
    "transactions": []
  }
}
```

Example:

``` json
{
  "result": {
    "transactions": [
      {
        "id": "5305e3bab097f420a62ced0b",
        "time": 1399114284039,
        "amount": 500000,
        "account": {
          "phone": "903595731"
        },
        "create_time": 1399114284039,
        "perform_time": 1399114285002,
        "cancel_time": 0,
        "transaction": "5123",
        "state": 2,
        "reason": null
      }
    ]
  }
}
```

------------------------------------------------------------------------

# Payment Initialization (Redirect)

Payments can be initiated using **POST or GET redirect**.

------------------------------------------------------------------------

# POST Method

Example HTML form:

``` html
<form method="POST" action="https://test.paycom.uz">
<input type="hidden" name="merchant" value="{Merchant ID}"/>
<input type="hidden" name="amount" value="{amount in tiyin}"/>
<input type="hidden" name="account[phone]" value="903595731"/>
<input type="hidden" name="lang" value="ru"/>
<input type="hidden" name="callback" value="https://your-service.uz/paycom/:transaction"/>
<button type="submit">Pay with Payme</button>
</form>
```

Optional parameters:

  Parameter          Description
  ------------------ ------------------------------------------
  lang               ru / uz / en
  callback           Return URL
  callback_timeout   Redirect delay
  description        Payment description
  detail             Base64 encoded JSON with receipt details

------------------------------------------------------------------------

# GET Method

Format:

    https://checkout.paycom.uz/base64(params)

Parameters are encoded using Base64.

Example parameters:

    m=merchant_id
    ac.order_id=197
    a=500

Encoded URL example:

    https://checkout.paycom.uz/bT01ODdmNzJjNzJjYWMwZDE2MmM3MjJhZTI7YWMub3JkZXJfaWQ9MTk3O2E9NTAw

------------------------------------------------------------------------

# Typical Payment Flow

1.  User clicks **Pay with Payme**
2.  Merchant redirects user to Payme checkout
3.  Payme calls merchant API methods:

```{=html}
<!-- -->
```
    CheckPerformTransaction
    CreateTransaction
    PerformTransaction

4.  Merchant confirms payment
5.  Payme redirects user back to merchant callback URL

------------------------------------------------------------------------

# Important Notes

-   Always return **HTTP 200**
-   Store transactions persistently
-   Handle transaction timeout (12 hours)
-   Validate account data carefully
-   Implement **GetStatement** method

------------------------------------------------------------------------

# End of Documentation
