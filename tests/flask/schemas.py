from os import getenv
from marshmallow import Schema, fields, EXCLUDE, RAISE

# Set at global level since the server is restarted whenever the EXCLUDE_UNKNOWN configuration value changes
UNKNOWN_VALUE = EXCLUDE if getenv("EXCLUDE_UNKNOWN").lower() == "yes".lower() == "yes" else RAISE
print("Unknown field behavior:", UNKNOWN_VALUE)


class UserIdSchema(Schema):
    user_id = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class CreateAccUserInfoInputSchema(Schema):
    email = fields.Str(required=True)
    name = fields.Str(load_only=True)
    phone_num = fields.Str(load_only=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UserInfoInputSchema(Schema):
    email = fields.Str(load_only=True)
    name = fields.Str(load_only=True)
    phone_num = fields.Str(load_only=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class CreateAccSchema(Schema):
    user_info = fields.Nested(CreateAccUserInfoInputSchema(), required=True)
    password = fields.Str(required=True)
    test = fields.Bool(missing=False)

    class Meta:
        unknown = UNKNOWN_VALUE


class UpdateAccUserInfoSchema(Schema):
    name = fields.Str(load_only=True)
    phone_num = fields.Str(load_only=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UpdateAccUserSchema(Schema):
    user_id = fields.Str(required=True)
    user_info = fields.Nested(UpdateAccUserInfoSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UpdateAccSchema(Schema):
    user_info = fields.Nested(UpdateAccUserInfoSchema(), load_only=True)
    password = fields.Str(load_only=True)
    test = fields.Bool(missing=False)

    class Meta:
        unknown = UNKNOWN_VALUE


class EmailSchema(Schema):
    email = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class LoginSchema(Schema):
    user_info = fields.Nested(EmailSchema(), required=True)
    password = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class CoordinatesSchema(Schema):
    lat = fields.Float(required=True)
    long = fields.Float(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class LocationSchema(Schema):
    name = fields.Str(required=True)
    coordinates = fields.Nested(CoordinatesSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class OrderDelInfoSchema(Schema):
    pickup_loc = fields.Nested(LocationSchema(), required=True)
    drop_loc = fields.Nested(LocationSchema(), required=True)
    GET_code = fields.Str(missing=None)

    class Meta:
        unknown = UNKNOWN_VALUE


class OrderDelSchema(Schema):
    user_id = fields.Str(required=True)
    user_info = fields.Nested(UserInfoInputSchema(), load_only=True)
    order = fields.Nested(OrderDelInfoSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UpdateOrderInfoSchema(Schema):
    order_id = fields.Str(required=True)
    pickup_loc = fields.Nested(LocationSchema(), load_only=True)
    drop_loc = fields.Nested(LocationSchema(), load_only=True)
    GET_code = fields.Str(load_only=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UpdateOrderSchema(Schema):
    user_id = fields.Str(required=True)
    order = fields.Nested(UpdateOrderInfoSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class MakeDelInfoSchema(Schema):
    leaving_from = fields.Nested(LocationSchema(), required=True)
    destination = fields.Nested(LocationSchema(), required=True)
    num_deliveries = fields.Int(missing=999)

    class Meta:
        unknown = UNKNOWN_VALUE


class MakeDelSchema(Schema):
    user_id = fields.Str(required=True)
    delivery = fields.Nested(MakeDelInfoSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class OrderIdSchema(Schema):
    order_id = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UserIdOrderIdSchema(Schema):
    user_id = fields.Str(required=True)
    order_id = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class MatchOrderSchema(Schema):
    user_info = fields.Nested(UserInfoInputSchema(), load_only=True)
    order_id = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UnmatchOrderSchema(Schema):
    order_id = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


# Response schemas
class UserInfoResponseSchema(Schema):
    email = fields.Str(required=True)
    name = fields.Str(required=True)
    username = fields.Str(required=True)
    phone_num = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UserResponseSchema(Schema):
    user_id = fields.Str(required=True)
    acc_active = fields.Bool(required=True)
    user_info = fields.Nested(UserInfoResponseSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UserResponseSchemaWithActiveStatus(Schema):
    user_id = fields.Str(required=True)
    acc_active = fields.Bool(required=True)
    user_info = fields.Nested(UserInfoResponseSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UserInfoResponse(Schema):
    user_id = fields.Str(required=True)
    user_info = fields.Nested(UserInfoResponseSchema(), required=True)
    acc_active = fields.Bool(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class CreateAccResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)
    user = fields.Nested(UserInfoResponse(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class LoginResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)
    user = fields.Nested(UserResponseSchemaWithActiveStatus(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class SSOLoginResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)
    is_new_login = fields.Str(required=True)
    authentication_date = fields.Str(required=True)
    user = fields.Nested(UserResponseSchemaWithActiveStatus(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class OrderDelResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)
    order = fields.Nested(OrderIdSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class StartDelResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)
    unmatched_users = fields.List(fields.Field, required=True)  # temporarily use Field for List eles; add details later

    class Meta:
        unknown = UNKNOWN_VALUE


class GetDelivererResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)
    # can use UserResponseSchema; acc_active won't matter since it's not passed to the response json
    deliverer = fields.Nested(UserResponseSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class OrderStatusSchema(Schema):
    order_status = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class GetOrderStatusResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)
    order = fields.Nested(OrderStatusSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class GETCodeSchema(Schema):
    GET_code = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class GETCodeResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)
    order = fields.Nested(GETCodeSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class MatchResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)
    matched_customer = fields.Nested(UserResponseSchemaWithActiveStatus(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class OrdersResponse(Schema):
    _id = fields.Str(required=True)
    customer = fields.Nested(UserResponseSchema(), required=True)
    deliverer = fields.Nested(UserResponseSchema(), required=True)
    pickup_loc = fields.Nested(LocationSchema(), required=True)
    drop_loc = fields.Nested(LocationSchema(), required=True)
    GET_code = fields.Str(required=True)
    order_date = fields.DateTime(required=True)
    order_status = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class GetOrdersResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)
    orders = fields.List(fields.Nested(OrdersResponse()), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class GetDeliveriesResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)
    deliveries = fields.List(fields.Nested(OrdersResponse()), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class SuccessResponseSchema(Schema):
    succeeded = fields.Int(required=True)
    msg = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE
