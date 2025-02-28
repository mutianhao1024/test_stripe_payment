# 基础模型类 - 实现自动去除字符串前后空格功能
from datetime import datetime
from typing import Optional, Literal, Dict, List, Any

from pydantic import BaseModel, Field, EmailStr, model_validator


class BaseModelWithTrim(BaseModel):
    @model_validator(mode="before")
    def trim_strings(cls, values):
        for key, value in values.items():
            if isinstance(value, str):
                values[key] = value.strip()
        return values


class DeviceInfoSchema(BaseModelWithTrim):
    color_depth: Optional[int] = Field(None, description="用户浏览器的色彩深度")
    screen_height: Optional[int] = Field(None, description="用户设备的屏幕高度")
    screen_width: Optional[int] = Field(None, description="用户设备的屏幕宽度")
    time_zone_offset: Optional[int] = Field(None, description="UTC 时间与用户浏览器本地时间的时差")
    device_token_id: Optional[str] = Field(None, max_length=256, description="设备的令牌标识")
    device_language: Optional[str] = Field(None, max_length=32, description="用户下单设备的语言")


class BrowserInfoSchema(BaseModelWithTrim):
    user_agent: str = Field(..., max_length=2048, description="用户的浏览器用户代理")
    accept_header: Optional[str] = Field(None, max_length=2048, description="用户浏览器的请求头信息")
    java_enabled: Optional[bool] = Field(False, description="用户浏览器是否支持运行 Java")
    java_script_enabled: Optional[bool] = Field(False, description="用户浏览器是否支持运行 JavaScript")
    language: Optional[str] = Field(None, max_length=32, description="用户浏览器的语言")

    @model_validator(mode="before")
    def validate_required_fields(cls, values):
        required_fields = ["user_agent"]
        for field in required_fields:
            if not values.get(field) or not str(values[field]).strip():
                raise ValueError(f"{field} 不能为空或空字符串")
        return values


class EnvSchema(BaseModelWithTrim):
    terminal_type: Literal["WEB", "MOBILE", "APP", "MINI_APP"] = Field(..., description="商户服务适用的终端类型")
    client_ip: str = Field(..., max_length=45, description="客户 IP 地址（支持 IPv4 和 IPv6）")
    browser_info: BrowserInfoSchema = Field(..., description="浏览器环境信息")
    device_info: Optional[DeviceInfoSchema] = Field(None, description="设备信息，包括屏幕分辨率、语言等")

    @model_validator(mode="before")
    def validate_required_fields(cls, values):
        if not values.get("terminal_type") or not values.get("client_ip"):
            raise ValueError("terminal_type 和 client_ip 为必填字段")
        return values


class GoodsSchema(BaseModelWithTrim):
    goods_id: str = Field(..., max_length=64, description="商品唯一标识")
    goods_name: str = Field(..., max_length=256, description="商品名称")
    goods_category: str = Field(..., max_length=64, description="商品分类")
    goods_quantity: int = Field(..., description="商品数量")
    goods_url: str = Field(..., max_length=2048, description="商品链接")
    goods_img_url: Optional[str] = Field(None, max_length=2048, description="商品图片链接")
    goods_price: int = Field(..., description="商品单价，最小货币单位")
    delivery_method_type: Literal['PHYSICAL', 'DIGITAL'] = Field(..., description="商品的配送方式")

    @model_validator(mode="before")
    def validate_required_fields(cls, values):
        required_fields = ["goods_id", "goods_name", "goods_category", "goods_url", "delivery_method_type",
                           "goods_price", "goods_quantity"]
        for field in required_fields:
            if not values.get(field) or not str(values[field]).strip():
                raise ValueError(f"{field} 不能为空或空字符串")
        return values


class ShippingAddressSchema(BaseModelWithTrim):
    country: str = Field(..., max_length=2, description="国家代码")
    state: str = Field(..., max_length=32, description="州/省")
    city: str = Field(..., max_length=32, description="城市")
    address1: str = Field(..., max_length=256, description="地址1")
    address2: Optional[str] = Field(None, max_length=256, description="地址2")
    zip_code: str = Field(..., max_length=32, description="邮政编码")


class ShippingNameSchema(BaseModelWithTrim):
    first_name: str = Field(..., max_length=32, description="名字")
    last_name: str = Field(..., max_length=32, description="姓")
    full_name: str = Field(..., max_length=128, description="全名")


class ShippingSchema(BaseModelWithTrim):
    shipping_name: ShippingNameSchema
    shipping_address: ShippingAddressSchema
    email: EmailStr = Field(..., max_length=64, description="客户电子邮件")
    phone: str = Field(..., max_length=25, description="客户手机号")
    carrier: Optional[str] = Field(None, max_length=50, description="物流服务提供商")


class PaymentDataSchema(BaseModelWithTrim):
    card_number: str = Field(..., description="银行卡号", pattern=r"^\d{13,19}$")
    expiry_year: str = Field(..., max_length=2, description="银行卡的到期年份 (两位数字，如 '24')", pattern=r"^\d{2}$")
    expiry_month: str = Field(..., max_length=2, description="银行卡的过期月份 (01-12)", pattern=r"^(0[1-9]|1[0-2])$")
    cvv: str = Field(..., min_length=3, max_length=4, description="银行卡的 CVV 码（3-4 位）", pattern=r"^\d{3,4}$")
    requires_3ds: Optional[bool] = Field(None, description="是否需要 3DS 验证")
    country: str = Field(..., max_length=2, description="订单国家")
    card_holder_name: ShippingNameSchema
    billing_address: ShippingAddressSchema

    @model_validator(mode="before")
    def validate_expiry_date(cls, values):
        if "expiry_year" in values and "expiry_month" in values:
            try:
                expiry_year = int("20" + values["expiry_year"])
                expiry_month = int(values["expiry_month"])
                now = datetime.now()
                if expiry_year < now.year or (expiry_year == now.year and expiry_month < now.month):
                    raise ValueError("银行卡已过期！")
            except ValueError:
                raise ValueError("无效的到期年月！")
        return values


class PaymentMethodSchema(BaseModelWithTrim):
    payment_type: str = Field(..., description="支付方式类型")
    payment_data: PaymentDataSchema


class PaymentAmountSchema(BaseModelWithTrim):
    currency: str = Field(..., max_length=3, description="币种代码")
    value: int = Field(..., description="金额值，最小货币单位")


class OrderSchema(BaseModelWithTrim):
    merchant_order_id: str = Field(..., max_length=64, description="订单唯一标识")
    goods: Optional[list[GoodsSchema]] = Field(None, description="商品信息")
    shipping: ShippingSchema
    payment_amount: PaymentAmountSchema
    payment_method: PaymentMethodSchema
    metadata: Optional[Dict[str, str]] = Field(None, description="键值对形式的元数据")


class PaymentRequestSchema(BaseModelWithTrim):
    env: EnvSchema
    order: OrderSchema
    merchant_id: str = Field(..., description="商户唯一标识")
    redirect_url: str = Field(..., description="支付完成后的重定向链接")
    external_request_order_id: Optional[str] = Field(None, description="请求渠道时生成的订单号，唯一标识")
    system_order_id: Optional[str] = Field(None, description="系统生成的订单号，唯一标识")
    system_three_ds_redirect_url: Optional[str] = Field(None, description="系统3DS跳转地址")
    system_three_ds_return_url: Optional[str] = Field(None, description="系统3DS返回地址")


class ChannelPaymentResponseSchema(BaseModel):
    channel_order_id: Optional[str] = Field(None, description="支付网关返回的订单 ID")
    status: str = Field(..., description="支付状态，例如 'pending'、'success'、'failed'")
    redirect_url: Optional[str] = Field(None, description="支付重定向 URL，3D Secure 场景可能会返回")
    detail: Optional[Dict[str, str]] = Field(None, description="包含详细错误信息的字典（如错误码、错误消息）")


# 退款相关 Schema
class RefundRequestSchema(BaseModelWithTrim):
    channel_order_id: str = Field(..., description="PaymentIntent ID")
    refund_amount: Optional[int] = Field(None, description="退款金额（单位：分），为空则全额退款")
    system_order_id: str = Field(..., description="系统订单 ID")
    external_refund_id: str = Field(..., description="外部退款 ID，用于幂等性")
    refund_request_id: str = Field(..., description="退款请求 ID")


class RefundResponseSchema(BaseModel):
    channel_refund_id: Optional[str] = Field(None, description="退款 ID")
    status: str = Field(..., description="退款状态")
    detail: Optional[Dict[str, str]] = Field(None, description="错误详情")


# 查询支付详情的响应 Schema
class PaymentDetailsResponseSchema(BaseModel):
    channel_order_id: str = Field(..., description="PaymentIntent ID")
    status: str = Field(..., description="支付状态")
    amount: int = Field(..., description="支付金额")
    currency: str = Field(..., description="货币")
    metadata: Dict[str, Any] = Field(..., description="支付元数据")
    payment_method: Dict[str, Any] = Field(..., description="支付方法详情")
    created: int = Field(..., description="创建时间戳")
    charges: list = Field(..., description="收费记录")
    refunds: list = Field(..., description="退款记录")


# 状态和错误映射
class GatewayPaymentStatus:
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"


class CardPaymentsResponseSchema(BaseModel):
    payments: list[dict] = Field(..., description="与此卡关联的所有支付订单")
