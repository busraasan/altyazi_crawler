import re

def contains_only_turkish_characters(input_string):
    turkish_regex = re.compile(r'^[  a-zA-ZğĞıİöÖçÇşŞüÜ!.,;:?"≡&#{}@Â\-<>$\d*"\'()wx%]\d*|$')
    return bool(turkish_regex.match(input_string))

# Example usage
test_string = """bize hastalık bulaştıran insanların
peşine düşüp..."""
if contains_only_turkish_characters(test_string):
    print("String contains only Turkish characters.")
else:
    print("String contains non-Turkish characters.")