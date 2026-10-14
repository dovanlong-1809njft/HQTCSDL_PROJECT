"""Cấu hình ứng dụng — tạm thời dùng biến môi trường chuẩn."""
import os

APP_NAME = os.getenv("APP_NAME", "FamilyConnect")
DB_SERVER = os.getenv("DB_SERVER", "localhost")
DB_NAME = os.getenv("DB_NAME", "FamilyConnectDB")
# TODO: Đọc .env an toàn, xác thực cấu hình, tách môi trường dev/prod.
