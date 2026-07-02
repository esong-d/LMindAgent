

import decimal
import math


def format_number(number: float | int, format: str = "0.00") -> str:
    """
    保留位数, 向上取整
    :param number:
    :param format: 格式化字符串，如 "0.00" 表示保留两位小数
    :return:
    """
    return decimal.Decimal(str(number)).quantize(decimal.Decimal(format), rounding=decimal.ROUND_UP)


def format_number_ceil(number: float | int, format: int = 2) -> str:
    """
    保留位数, 向上取整
    :param number: 
    :param format: 保留位数
    :return:
    """
    return math.ceil(number * 10 ** format) / 10 ** format