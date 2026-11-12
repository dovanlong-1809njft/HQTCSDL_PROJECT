"""Gói domain identity.

Không nạp router tại đây. app/core/security.py nạp identity.models, nên nếu
__init__ nạp sẵn router thì chuỗi security -> identity -> core.dependencies ->
security tạo thành vòng import và backend không khởi động được khi một domain
khác (community, events, heritage...) được nạp trước identity.
Các domain còn lại cũng không có __init__ nạp router, nên bỏ đi là thống nhất.
"""
