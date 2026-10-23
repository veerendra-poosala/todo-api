def test_equal_or_not_equal():
    assert 3==3
    assert 3!=4
    assert 3==1

def test_greater_or_less_than():
    assert 3>2
    assert 2<3

def test_greater_or_equal_or_less_than_or_equal():
    assert 3>=3
    assert 3<=3

def test_is_or_is_not():
    validated = True
    assert validated is True
    assert validated is not False

def test_in_or_not_in():
    assert 3 in [1, 2, 3]
    assert 4 not in [1, 2, 3]

def test_string_equality():
    assert ('hello' == 'hello')
    assert ('hello' == 'world')

def test_string_inequality():
    assert ('hello' != 'world')
    assert ('hello' != 'hello')

def test_string_greater_or_less_than():
    assert ('hello' > 'world')
    assert ('hello' < 'world')


def is_palindrome(s):
    return s == s[::-1]

def test_is_palindrome():
    assert is_palindrome("racecar") == True
    assert is_palindrome("hello") == False
    assert is_palindrome("A man a plan a canal Panama") == False
    assert is_palindrome("") == True
    assert is_palindrome("a") == True

def test_assert_type():
    assert isinstance(3, int)
    assert isinstance("hello", str)
    assert isinstance([1, 2, 3], list)
    assert isinstance((1, 2, 3), tuple)
    assert isinstance({"key": "value"}, dict)