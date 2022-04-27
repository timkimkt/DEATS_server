from marshmallow import Schema, fields


class UserIdSchema(Schema):
    user_id = fields.Str(required=True)


class CreateAccUserInfoSchema(Schema):
    email = fields.Str(required=True)
    name = fields.Str(load_only=True)
    phone_num = fields.Str(load_only=True)


class CreateAccSchema(Schema):
    user_info = fields.Nested(CreateAccUserInfoSchema(), required=True)
    password = fields.Field(required=True)
    test = fields.Bool(missing=False)


class UpdateAccUserInfoSchema(Schema):
    name = fields.Str(load_only=True)
    phone_num = fields.Str(load_only=True)


class UpdateAccUserSchema(Schema):
    user_id = fields.Str(required=True)
    user_info = fields.Nested(UpdateAccUserInfoSchema(), required=True)


class UpdateAccSchema(Schema):
    user = fields.Nested(UpdateAccUserSchema(), required=True)


class EmailSchema(Schema):
    email = fields.Str(required=True)


class LoginSchema(Schema):
    user_info = fields.Nested(EmailSchema(), required=True)
    password = fields.Field(required=True)


class CoordinatesSchema(Schema):
    lat = fields.Float(required=True)
    long = fields.Float(required=True)


class LocationSchema(Schema):
    name = fields.Str(required=True)
    coordinates = fields.Nested(CoordinatesSchema(), required=True)


class OrderDelInfoSchema(Schema):
    pickup_loc = fields.Nested(LocationSchema(), required=True)
    drop_loc = fields.Nested(LocationSchema(), required=True)
    GET_code = fields.Str(missing=None)


class OrderDelSchema(Schema):
    user_id = fields.Str(required=True)
    order = fields.Nested(OrderDelInfoSchema(), required=True)


class UpdateCoordinatesSchema(Schema):
    lat = fields.Float(load_only=True)
    long = fields.Float(load_only=True)


class UpdateLocationSchema(Schema):
    name = fields.Str(load_only=True)
    coordinates = fields.Nested(UpdateCoordinatesSchema(), required=True)


class UpdateOrderInfoSchema(Schema):
    order_id = fields.Str(required=True)
    pickup_loc = fields.Nested(UpdateLocationSchema(), load_only=True)
    drop_loc = fields.Nested(UpdateLocationSchema(), load_only=True)
    GET_code = fields.Str(load_only=True)


class UpdateOrderSchema(Schema):
    user_id = fields.Str(required=True)
    order = fields.Nested(UpdateOrderInfoSchema(), required=True)


class MakeDelInfoSchema(Schema):
    leaving_from = fields.Nested(LocationSchema(), required=True)
    destination = fields.Nested(LocationSchema(), required=True)
    num_deliveries = fields.Int(Missing=999)


class MakeDelSchema(Schema):
    user_id = fields.Str(required=True)
    delivery = fields.Nested(MakeDelInfoSchema(), required=True)


class OrderIdSchema(Schema):
    order_id = fields.Str(required=True)


class UserIdOrderIdSchema(Schema):
    user_id = fields.Str(required=True)
    order_id = fields.Str(required=True)


class UserInfoSchema(Schema):
    email = fields.Str(required=True)
    name = fields.Str(required=True)
    phone_num = fields.Str(required=True)


class UserSchema(Schema):
    user_id = fields.Str(required=True)
    user_info = fields.Nested(UserInfoSchema(), required=True)


class MatchOrderSchema(Schema):
    user = fields.Nested(UserSchema(), required=True)
    order_id = fields.Str(required=True)


class UnmatchOrderSchema(Schema):
    order_id = fields.Str(required=True)


