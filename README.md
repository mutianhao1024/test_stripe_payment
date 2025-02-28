# test_stripe_payment
使用FastAPI进行对接Stripe支付平台的测试
test_stripe_payment 是一个基于 FastAPI 的 Stripe 支付测试项目，支持发起支付、取消支付、退款和查询支付详情等功能。项目使用 Pydantic 模型进行数据验证，适用于测试环境下的支付流程模拟。

# test_stripe_payment

使用 FastAPI 进行对接 Stripe 支付平台的测试。

## 项目简介
### 前提条件
Python: 3.11。  
Stripe 账户: 需要从 Stripe Dashboard 获取测试密钥 (sk_test_xxx)。
Git: 用于克隆项目。
本项目是一个集成了 Stripe 支付功能的示例应用，使用 FastAPI 框架实现了对 Stripe 的基本支付和退款操作的接口。适用于需要集成 Stripe 支付功能的开发者作为参考。

## 安装和配置

### 1. 克隆项目

首先克隆本项目到本地：

```bash
git clone https://github.com/mutianhao1024/test_stripe_payment.git
cd test_stripe_payment
```

### 2. 创建并激活虚拟环境
创建虚拟环境并激活：
```bash
# 对于 Linux/Mac
python3 -m venv venv
source venv/bin/activate

# 对于 Windows
python -m venv venv
.\venv\Scripts\activate
```
### 3. 安装依赖
安装项目所需的所有依赖：

```bash
pip install -r requirements.txt
```
### 4. 配置环境变量
确保在项目根目录中创建一个 .env 文件，并填入你的 Stripe API 密钥和其他配置：
```env
STRIPE_SECRET_KEY=your_secret_key_here
STRIPE_ACCOUNT_ID=your_account_id_here
```

### 5. 启动 FastAPI 项目
运行 FastAPI 项目：
```bash
uvicorn main:app --reload
```

默认情况下，应用将运行在 http://127.0.0.1:8000。

## 使用示例
### 发起支付
```json
{
    "env": {
        "terminal_type": "WEB",
        "client_ip": "<ip>",
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
            "device_token_id": "abcd-efg-1234-5678",
            "screen_width": 768,
            "screen_height": 1024,
            "color_depth": 41
        }
    },
    "order": {
        "merchant_order_id": "test_order_123",
        "goods": [
            {
                "goods_id": "9876-5432-1234-5678",
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
                "zip_code": "<post_code>"
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
                    "zip_code": "<post_code>"
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
    "external_request_order_id": "ext_test_123_20250227",
    "system_order_id": "sys_test_123",
    "system_three_ds_return_url": "https://example.com/3ds-return"
}
```
### 响应
```json
{
  "channel_order_id": "pi_3QxTest123",
  "status": "success",
  "redirect_url": "",
  "detail": null
}
```
### 发起退款
使用支付成功的 channel_order_id：
```json
{
    "channel_order_id": "pi_3QxTest123",
    "refund_amount": 1000,
    "system_order_id": "sys_test_123",
    "external_refund_id": "refund_ext_123_20250227",
    "refund_request_id": "req_refund_123"
}
```
### 响应
```json
{
  "channel_refund_id": "re_xxx",
  "status": "succeeded"
}
```