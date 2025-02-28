# 配置日志
import logging
import os
import stripe
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from backend.schema import PaymentRequestSchema, ChannelPaymentResponseSchema, GatewayPaymentStatus, \
    PaymentDetailsResponseSchema, RefundResponseSchema, RefundRequestSchema, CardPaymentsResponseSchema

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()
logger.info(f"STRIPE_SECRET_KEY: {os.getenv('STRIPE_SECRET_KEY')}")
logger.info(f"STRIPE_ACCOUNT_ID: {os.getenv('STRIPE_ACCOUNT_ID')}")

app = FastAPI(
    title="Stripe Payment API",
    description="使用 FastAPI 和 Stripe 实现的支付与退款服务",
    version="1.0.0",
)

# 调用Stripe API 所需的密钥
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
# 账户ID
account_id = os.getenv("STRIPE_ACCOUNT_ID")

"""
示例输入：
{
    "env": {
        "terminal_type": "WEB",
        "client_ip": "<ip address>",
        "browser_info": {
            "user_agent": "Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/5.1)",
            "accept_header": "laborum elit et",
            "java_enabled": true,
            "java_script_enabled": false,
            "language": "en_US"
        },
        "device_info": {
            "time_zone_offset": -120,
            "device_language": "en_US",
            "device_token_id": "9c4c83e6-ced7-4753-9719-6c32b5c83a66",
            "screen_width": 768,
            "screen_height": 1024,
            "color_depth": 41
        }
    },
    "order": {
        "merchant_order_id": "test_order_123",
        "goods": [
            {
                "goods_id": "d339561d-121d-4dcb-9981-10f71ada21fe",
                "goods_name": "Product 1",
                "goods_category": "food",
                "goods_quantity": 1,
                "goods_price": 5000,
                "goods_url": "https://example.com/product/food",
                "delivery_method_type": "PHYSICAL",
                "goods_img_url": "https://example.com/product/food.png"
            }
        ],
        "shipping": {
            "shipping_name": {
                "first_name": "Demo",
                "last_name": "Demo",
                "full_name": "DemoDemo"
            },
            "shipping_address": {
                "country": "US",
                "state": "CA",
                "city": "Fresno",
                "address1": "<address1>",
                "address2": "<address2>",
                "zip_code": "93706"
            },
            "email": "example@example.org",
            "phone": "<phone>",
            "carrier": "USPS"
        },
        "payment_amount": {
            "currency": "USD",
            "value": 10000
        },
        "payment_method": {
            "payment_type": "CARD",
            "payment_data": {
                "country": "US",
                "card_number": "<card_number>",
                "expiry_year": "<expiry_year>",
                "expiry_month": "<expiry_month>",
                "cvv": "<cvv>",
                "card_holder_name": {
                    "first_name": "Demo",
                    "last_name": "Demo",
                    "full_name": "DemoDemo"
                },
                "billing_address": {
                    "country": "US",
                    "state": "CA",
                    "city": "Fresno",
                    "address1": "<address1>",
                    "address2": "<address2>",
                    "zip_code": "<邮编>"
                },
                "requires_3ds": false
            }
        },
        "metadata": {
            "shop": "happy",
            "domain": "example.com"
        }
    },
    "merchant_id": "1",
    "redirect_url": "https://example.com/return",
    "external_request_order_id": "ext_test_123_208",
    "system_order_id": "sys_test_123",
    "system_three_ds_return_url": "https://example.com/3ds-return"
}
"""


@app.post("/create-payment", response_model=ChannelPaymentResponseSchema,
          summary="创建并发起 Stripe 支付")
async def create_payment(data: PaymentRequestSchema):
    """
    输出：
    {
      "channel_order_id": "pi_xxxxx",
      "status": "success",
      "redirect_url": "",
      "detail": null
    }
    :param data:
    :return:
    """
    try:
        billing_address = data.order.payment_method.payment_data.billing_address
        stripe_address = {
            "line1": billing_address.address1,
            "line2": billing_address.address2,
            "city": billing_address.city,
            "state": billing_address.state,
            "postal_code": billing_address.zip_code,
            "country": billing_address.country,
        }

        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": data.order.payment_method.payment_data.card_number,
                "exp_month": int(data.order.payment_method.payment_data.expiry_month),
                "exp_year": int("20" + data.order.payment_method.payment_data.expiry_year),
                "cvc": data.order.payment_method.payment_data.cvv,
            },
            billing_details={
                "name": data.order.payment_method.payment_data.card_holder_name.full_name,
                "email": data.order.shipping.email,
                "address": stripe_address,
            },
            stripe_account=account_id,
        )

        payment_intent = stripe.PaymentIntent.create(
            amount=data.order.payment_amount.value,
            currency=data.order.payment_amount.currency,
            payment_method=payment_method.id,
            confirmation_method="automatic",
            confirm=True,
            stripe_account=account_id,
            return_url=data.system_three_ds_return_url,  # 确保正确传递 return_url
            payment_method_options={
                "card": {
                    "request_three_d_secure": "challenge" if data.order.payment_method.payment_data.requires_3ds else "automatic"
                }
            },
            metadata={
                "system_order_id": data.system_order_id,
                "merchant_order_id": data.order.merchant_order_id,
                "external_request_order_id": data.external_request_order_id,
                "source": "DD",
                "merchant_id": data.merchant_id,
            },
            idempotency_key=data.external_request_order_id,
        )

        status_map = {
            "succeeded": GatewayPaymentStatus.SUCCESS,
            "requires_action": GatewayPaymentStatus.PENDING,
        }
        payment_status = status_map.get(payment_intent.status, GatewayPaymentStatus.FAILED)

        logger.info(f"Payment initiated: {payment_intent.id}, status: {payment_status}")
        return ChannelPaymentResponseSchema(
            channel_order_id=payment_intent.id,
            status=payment_status,
            redirect_url=getattr(payment_intent.next_action, "redirect_to_url", {}).get("url", ""),
            detail=None,
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe Error: {str(e)}")
        return ChannelPaymentResponseSchema(
            channel_order_id=None,
            status=GatewayPaymentStatus.FAILED,
            detail={"message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# 退款接口
@app.post("/refund", response_model=RefundResponseSchema, summary="执行 Stripe 退款")
async def refund_payment(data: RefundRequestSchema):
    """
    执行退款。

    - **channel_order_id**: PaymentIntent ID
    - **refund_amount**: 退款金额（单位：分），为空则全额退款
    - **system_order_id**: 系统订单 ID
    - **external_refund_id**: 外部退款 ID，用于幂等性
    - **refund_request_id**: 退款请求 ID

    {
        "channel_order_id": "PaymentIntent ID",
        "refund_amount": 1000,
        "system_order_id": "sys_test_123", # 标识系统内的订单，建议保持与创建订单一致
        "external_refund_id": "refund_ext_1234", # 退款接口所需的幂等性键，完全由你自行定义
        "refund_request_id": "req_refund_124" # 退款请求的自定义标识，由你手动指定，建议唯一
    }
    """
    try:
        refund = stripe.Refund.create(
            payment_intent=data.channel_order_id,
            amount=data.refund_amount,
            stripe_account=account_id,
            metadata={
                "system_order_id": data.system_order_id,
                "external_refund_id": data.external_refund_id,
                "refund_request_id": data.refund_request_id
            },
            idempotency_key=data.external_refund_id
        )

        status_map = {
            "succeeded": GatewayPaymentStatus.SUCCESS,
            "pending": GatewayPaymentStatus.PENDING,
        }
        refund_status = status_map.get(refund.status, GatewayPaymentStatus.FAILED)

        logger.info(f"Refund processed: {refund.id}, status: {refund_status}")
        return RefundResponseSchema(
            channel_refund_id=refund.id,
            status=refund_status
        )

    except stripe.error.IdempotencyError as e:
        logger.warning(f"Idempotency Error: {str(e)}. Checking existing refund...")
        try:
            refunds = stripe.Refund.list(
                payment_intent=data.channel_order_id,
                limit=10,
                stripe_account=account_id
            )
            for refund in refunds.data:
                if refund.metadata.get("external_refund_id") == data.external_refund_id:
                    status_map = {
                        "succeeded": GatewayPaymentStatus.SUCCESS,
                        "pending": GatewayPaymentStatus.PENDING,
                    }
                    refund_status = status_map.get(refund.status, GatewayPaymentStatus.FAILED)
                    logger.info(f"Found existing refund: {refund.id}, status: {refund_status}")
                    return RefundResponseSchema(
                        channel_refund_id=refund.id,
                        status=refund_status
                    )
            return RefundResponseSchema(
                channel_refund_id=None,
                status=GatewayPaymentStatus.FAILED,
                detail={"message": "Idempotency key used with different parameters. Use a new key."}
            )
        except stripe.error.StripeError as inner_e:
            logger.error(f"Error retrieving refund: {str(inner_e)}")
            return RefundResponseSchema(
                channel_refund_id=None,
                status=GatewayPaymentStatus.FAILED,
                detail={"message": f"Failed to check existing refund: {str(inner_e)}"}
            )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe Refund Error: {str(e)}")
        return RefundResponseSchema(
            channel_refund_id=None,
            status=GatewayPaymentStatus.FAILED,
            detail={"message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected Refund Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


# 查询支付详情接口
@app.get("/payment/{payment_id}", response_model=PaymentDetailsResponseSchema, summary="查询支付详情")
async def get_payment_details(payment_id: str):
    """
    :param payment_id: 示例：pi_3QxN7c2KnFw7QuKu1CW304Ak
    :return:
    """
    try:
        payment_intent = stripe.PaymentIntent.retrieve(
            payment_id,
            stripe_account=account_id,
            expand=['charges.data', 'payment_method']
        )

        charges = []
        refunds = []
        if hasattr(payment_intent, 'charges') and payment_intent.charges and payment_intent.charges.data:
            charges = [charge.to_dict() for charge in payment_intent.charges.data]
            for charge in payment_intent.charges.data:
                if hasattr(charge, 'refunds') and charge.refunds and charge.refunds.data:
                    refunds.extend([refund.to_dict() for refund in charge.refunds.data])
        else:
            logger.warning(f"No charges data found for PaymentIntent: {payment_id}")

        payment_method_details = {}
        if hasattr(payment_intent, 'payment_method') and payment_intent.payment_method:
            payment_method = payment_intent.payment_method if isinstance(payment_intent.payment_method,
                                                                         dict) else payment_intent.payment_method.to_dict()
            payment_method_details = payment_method
        else:
            logger.warning(f"No payment_method available for PaymentIntent: {payment_id}")

        logger.info(f"Payment details retrieved: {payment_intent.id}")
        return PaymentDetailsResponseSchema(
            channel_order_id=payment_intent.id,
            status=payment_intent.status,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
            metadata=payment_intent.metadata,
            payment_method=payment_method_details,
            created=payment_intent.created,
            charges=charges,
            refunds=refunds
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe Error retrieving payment: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe 错误: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@app.get("/card-payments/{payment_method_id}", response_model=CardPaymentsResponseSchema,
         summary="查询此卡的所有支付订单")
async def get_card_payments(payment_method_id: str):
    """
    查询指定支付卡的所有支付订单。

    - **payment_method_id**: PaymentMethod ID (例如 'pm_1QxN7b2KnFw7QuKuaeU7hPeN')
    """
    try:
        # 验证 PaymentMethod 存在
        stripe.PaymentMethod.retrieve(payment_method_id, stripe_account=account_id)

        # 查询所有 Charge（无法直接按 payment_method 过滤）
        charges = stripe.Charge.list(
            stripe_account=account_id,
            limit=100,  # 可调整分页大小
            expand=['data.payment_intent']  # 扩展 PaymentIntent 数据
        )

        payments = []
        seen_intents = set()  # 避免重复
        for charge in charges.data:
            if charge.payment_method == payment_method_id and charge.payment_intent and charge.payment_intent.id not in seen_intents:
                intent = charge.payment_intent
                payments.append({
                    "channel_order_id": intent.id,
                    "status": intent.status,
                    "amount": intent.amount,
                    "currency": intent.currency,
                    "created": intent.created,
                    "metadata": intent.metadata,
                    "charges": [charge.to_dict()]
                })
                seen_intents.add(intent.id)

        logger.info(f"Retrieved {len(payments)} payments for PaymentMethod: {payment_method_id}")
        return CardPaymentsResponseSchema(payments=payments)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe Error retrieving card payments: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe 错误: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@app.post("/cancel-payment/{payment_id}", response_model=ChannelPaymentResponseSchema, summary="取消支付")
async def cancel_payment(payment_id: str):
    """
    取消未完成的支付。
    测试取消支付接口需要先发起一个支付，然后在支付未完成如状态为
    requires_action、requires_payment_method 或 requires_confirmation时取消它
    使用需要 3DS 验证的测试卡，以确保支付状态停留在 requires_action，而不是立即 succeeded。
    - **payment_id**: PaymentIntent ID (例如 'pi_xxx')
    """
    try:
        payment_intent = stripe.PaymentIntent.cancel(payment_id=payment_id, stripe_account=account_id)
        logger.info(f"Payment canceled: {payment_id}")
        return ChannelPaymentResponseSchema(
            channel_order_id=payment_intent.id,
            status=payment_intent.status,  # 通常为 "canceled"
            redirect_url=None,
            detail=None
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe Error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe 错误: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
