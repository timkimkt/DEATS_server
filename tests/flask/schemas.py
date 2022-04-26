from marshmallow import Schema, fields


class CreateAccSchema(Schema):
    user_info = fields.Field(required=True)
    password = fields.Field(required=True)
    test = fields.Bool(missing=False)


class UpdateAccSchema(Schema):
    user_id = fields.Str(required=True)
    user_info = fields.Field(load_only=True)
    password = fields.Field(load_only=True)


class ManipulateAccSchema(Schema):
    user_id = fields.Str(required=True)


class LoginSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Field(required=True)


class LogoutSchema(Schema):
    user_id = fields.Str(required=True)


class CoordinatesSchema(Schema):
    lat = fields.Float(required=True)
    long = fields.Float(required=True)


class OrderDelSchema(Schema):
    user_id = fields.Str(required=True)
    pickup_loc = fields.Nested(CoordinatesSchema)
    drop_loc = fields.Nested(CoordinatesSchema)
    GET_code = fields.Str(load_only=True)


class UpdateOrderSchema(Schema):
    user_id = fields.Str(required=True)
    pickup_loc = fields.Str(load_only=True)
    drop_loc = fields.Str(load_only=True)
    GET_code = fields.DateTime(load_only=True)


class MakeDelSchema(Schema):
    user_id = fields.Str(required=True)
    leaving_from = fields.Nested(CoordinatesSchema)
    destination = fields.Nested(CoordinatesSchema)
    num_deliveries = fields.Int(Missing=999)


class UserInfoSchema(Schema):
    email = fields.Str(required=True)
    name = fields.Str(required=True)
    phone_num = fields.Str(required=True)


class UserSchema(Schema):
    user_id = fields.Str(required=True)
    user_info = fields.Nested(UserInfoSchema)


class MatchOrderSchema(Schema):
    user = fields.Nested(UserSchema)
    order_id = fields.Str(required=True)


class UnmatchOrderSchema(Schema):
    order_id = fields.Str(required=True)


class OrderInfo(Schema):
    user_id = fields.Str(required=True)
    order_id = fields.Str(required=True)


class OrdersDeliveriesSchema(Schema):
    user_id = fields.Str(required=True)
    order_id = fields.Str(required=True)




