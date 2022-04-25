from marshmallow import Schema, fields


class CreateAccSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Field(required=True)
    name = fields.Str(missing=None)
    phone_num = fields.Str(missing=None)
    test = fields.Bool(missing=False)


class ManipulateAccSchema(Schema):
    user_id = fields.Str(required=True)
    name = fields.Str(load_only=True)
    phone_num = fields.Str(load_only=True)


class LoginSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True)


class OrderDelSchema(Schema):
    user_id = fields.Int(required=True)
    pickup_loc = fields.Str(required=True)
    drop_loc = fields.Str(required=True)
    GET_code = fields.DateTime(required=True)


class UpdateOrderSchema(Schema):
    user_id = fields.Int(required=True)
    pickup_loc = fields.Str(load_only=True)
    drop_loc = fields.Str(load_only=True)
    GET_code = fields.DateTime(load_only=True)


class MakeDelSchema(Schema):
    user_id = fields.Str(required=True)
    start_point = fields.Str(required=True)
    destination = fields.Str(required=True)
    num_deliveries = fields.Int(required=True)


class MatchUnmatchOrderInfo(Schema):
    user_id = fields.Str(required=True)
    order_id = fields.Str(required=True)


class OrdersDeliveriesSchema(Schema):
    user_id = fields.Str(required=True)




