import password_strength
from password_strength import PasswordPolicy

policy = PasswordPolicy.from_names(
    length=8,  # min length: 8
    uppercase=1,  # min uppercase letters: 1
    numbers=1,  # min numbers: 1
    special=1,  # min special characters: 1
    nonletters=2,  # min non-letter characters (digits, specials, anything): 2
    strength=0.66,  # min password strength: 0.66
)


def validate_password(password):
    result = policy.test(password)

    if result:
        error_msg = "The provided password lacks: "
        i = 0
        for failed_test in result:
            error_msg += "\n   " + str(i) + ") " + map_failed_test_to_error_msg(type(failed_test))
            i += 1

        raise ValueError(error_msg)


switcher = {
    password_strength.tests.Length: "a minimum of 8 characters",
    password_strength.tests.Uppercase: "at least one uppercase",
    password_strength.tests.Numbers: "at least 1 number",
    password_strength.tests.Special: "at least 1 special character",
    password_strength.tests.NonLetters: "at least 2 non-letters",
    password_strength.tests.Strength: "good strength",
}


def map_failed_test_to_error_msg(failed_test):
    print(failed_test)
    print(switcher.get(failed_test))
    return switcher.get(failed_test)