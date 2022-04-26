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


class OrderDelSchema(Schema):
    user_id = fields.Str(required=True)
    pickup_loc = fields.Field(required=True)
    drop_loc = fields.Field(required=True)
    GET_code = fields.Str(load_only=True)


class UpdateOrderSchema(Schema):
    user_id = fields.Str(required=True)
    pickup_loc = fields.Str(load_only=True)
    drop_loc = fields.Str(load_only=True)
    GET_code = fields.DateTime(load_only=True)


class MakeDelSchema(Schema):
    user_id = fields.Str(required=True)
    leaving_from = fields.Field(required=True)
    destination = fields.Field(required=True)
    num_deliveries = fields.Int(Missing=999)


class MatchUnmatchOrderInfo(Schema):
    user_id = fields.Str(required=True)
    order_id = fields.Str(required=True)


class OrdersDeliveriesSchema(Schema):
    user_id = fields.Str(required=True)
    order_id = fields.Str(required=True)




