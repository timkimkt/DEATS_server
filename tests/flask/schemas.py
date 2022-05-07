from os import getenv
from marshmallow import Schema, fields, EXCLUDE, RAISE

# Set at global level since the server is restarted whenever the EXCLUDE_UNKNOWN configuration value changes
UNKNOWN_VALUE = EXCLUDE if getenv("EXCLUDE_UNKNOWN").lower() == "yes".lower() == "yes" else RAISE
print("Unknown field behavior:", UNKNOWN_VALUE)


class UserIdSchema(Schema):
    user_id = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class CreateAccUserInfoSchema(Schema):
    email = fields.Str(required=True)
    name = fields.Str(load_only=True)
    phone_num = fields.Str(load_only=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class CreateAccSchema(Schema):
    user_info = fields.Nested(CreateAccUserInfoSchema(), required=True)
    password = fields.Field(required=True)
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
    user = fields.Nested(UpdateAccUserSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class EmailSchema(Schema):
    email = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class LoginSchema(Schema):
    user_info = fields.Nested(EmailSchema(), required=True)
    password = fields.Field(required=True)

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
    order = fields.Nested(OrderDelInfoSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UpdateCoordinatesSchema(Schema):
    lat = fields.Float(load_only=True)
    long = fields.Float(load_only=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UpdateLocationSchema(Schema):
    name = fields.Str(load_only=True)
    coordinates = fields.Nested(UpdateCoordinatesSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UpdateOrderInfoSchema(Schema):
    order_id = fields.Str(required=True)
    pickup_loc = fields.Nested(UpdateLocationSchema(), load_only=True)
    drop_loc = fields.Nested(UpdateLocationSchema(), load_only=True)
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


class UserInfoSchema(Schema):
    email = fields.Str(required=True)
    name = fields.Str(required=True)
    phone_num = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UserSchema(Schema):
    user_id = fields.Str(required=True)
    user_info = fields.Nested(UserInfoSchema(), required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class MatchOrderSchema(Schema):
    user = fields.Nested(UserSchema(), required=True)
    order_id = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


class UnmatchOrderSchema(Schema):
    order_id = fields.Str(required=True)

    class Meta:
        unknown = UNKNOWN_VALUE


