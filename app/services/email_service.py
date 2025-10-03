from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import random
import string
import ssl
from email.utils import formataddr
from datetime import datetime

# Cài đặt premailer nếu bạn muốn tự động inline CSS từ style tag
# pip install premailer
from premailer import transform

class EmailService:
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, sender_name: str = "CinePlus"):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender_name = sender_name

    def generate_verification_code(self, length: int = 6) -> str:
        """Tạo mã xác nhận ngẫu nhiên."""
        return ''.join(random.choices(string.digits, k=length))

    def send_verification_email(self, to_email: str, verification_code: str) -> bool:
        """Gửi email xác nhận đến địa chỉ email đã chỉ định."""
        try:
            msg = MIMEMultipart('alternative') # Dùng 'alternative' để client chọn phiên bản phù hợp

            msg['From'] = formataddr((self.sender_name, self.username))
            msg['To'] = to_email
            msg['Subject'] = "Xác nhận đăng ký tài khoản của bạn"

            # Template HTML với các class Tailwind (cần được xử lý thành inline CSS)
            html_template = f"""\
            <html>
            <head>
            </head>
            <body style="font-family: Arial, Helvetica, sans-serif; background-color: #f3f4f6; margin: 0; padding: 0;">
                <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px;">
                    <tr>
                        <td style="background-color: #2563eb; color: #ffffff; text-align: center; padding: 20px; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                            <h2 style="font-size: 24px; font-weight: bold; margin: 0;">Xác nhận Tài khoản</h2>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px;">
                            <p style="margin: 0 0 16px;">Chào bạn,</p>
                            <p style="margin: 0 0 16px;">Cảm ơn bạn đã đăng ký tài khoản. Mã xác nhận của bạn là:</p>
                            <div style="width: fit-content; margin: 20px auto; padding: 16px; background-color: #e5e7eb; border-radius: 6px; font-size: 24px; font-weight: bold; text-align: center; border: 1px solid #9ca3af;">
                                {verification_code}
                            </div>
                            <p style="margin: 0 0 16px; font-size: 14px; color: #4b5563;">Mã này sẽ hết hạn sau <strong>15 phút</strong>.</p>
                            <p style="margin: 0 0 16px; font-size: 14px; color: #4b5563;">Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email này.</p>
                            <p style="margin: 32px 0 0;">Trân trọng,<br>{self.sender_name}</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align: center; font-size: 12px; color: #6b7280; padding: 16px; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 8px;">Đây là email tự động, vui lòng không trả lời.</p>
                            <p style="margin: 0;">&copy; {datetime.now().year} {self.sender_name}. All rights reserved.</p>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            html_body_inlined = transform(html_template)

            msg.attach(MIMEText(html_body_inlined, 'html', 'utf-8'))

            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.username, to_email, msg.as_string())

            return True

        except Exception as e:
            print(f"Lỗi khi gửi email xác nhận: {str(e)}")
            return False

    def send_booking_confirmation_email(self, to_email: str, booking_details: dict) -> bool:
        """Gửi email xác nhận đặt chỗ với chi tiết đặt chỗ."""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((self.sender_name, self.username))
            msg['To'] = to_email
            msg['Subject'] = "Xác nhận đặt vé thành công"

            html_template_with_tailwind_booking = f"""\
            <html>
            <head>
            </head>
            <body class="font-sans text-gray-800 bg-gray-100 p-0 m-0">
            <div class="max-w-xl mx-auto bg-white rounded-lg shadow-md overflow-hidden my-8">
            <div class="bg-red-600 text-white text-center py-6 px-6 rounded-t-lg">
            <h2 class="text-3xl font-bold tracking-tight">XÁC NHẬN ĐẶT VÉ THÀNH CÔNG</h2>
            </div>
            <div class="p-8">
            <p class="mb-6 text-lg">Xin chào,</p>
            <p class="mb-6">Cảm ơn bạn đã tin tưởng và đặt vé xem phim tại hệ thống của chúng tôi. Dưới đây là thông tin chi tiết về vé của bạn:</p>
            <div class="bg-gray-100 rounded-md p-6 mb-6 border border-gray-200">
            <ul class="list-none p-0">
            <li class="mb-3"><strong class="text-red-600">Mã đặt vé:</strong> <span class="font-semibold">{booking_details.get('booking_id', 'N/A')}</span></li>
            <li class="mb-3"><strong class="text-red-600">Họ và tên:</strong> <span class="font-semibold">{booking_details.get('customer_name', 'N/A')}</span></li>
            <li class="mb-3"><strong class="text-red-600">Ngày chiếu:</strong> <span class="font-semibold">{booking_details.get('departure_date', 'N/A')}</span></li>
            <li class="mb-3"><strong class="text-red-600">Phim:</strong> <span class="font-semibold">{booking_details.get('origin', 'N/A')}</span></li>
            <li class="mb-3"><strong class="text-red-600">Rạp:</strong> <span class="font-semibold">{booking_details.get('destination', 'N/A')}</span></li>
            <li class="mb-3"><strong class="text-red-600">Giờ chiếu:</strong> <span class="font-semibold">{booking_details.get('time', 'N/A')}</span></li>
            <li class="mb-3"><strong class="text-red-600">Số lượng vé:</strong> <span class="font-semibold">{booking_details.get('ticket_count', 'N/A')}</span></li>
            </ul>
            </div>
            <div class="text-center my-8">
            <p class="mb-4 text-lg">Vui lòng quét mã QR này để nhận vé tại quầy:</p>
            <div class="inline-block bg-white p-4 border border-red-300 rounded-md shadow-md">
            <img src="qr_code_image_url" alt="Mã QR nhận vé" class="w-48 h-48">
            </div>
            <p class="mt-4 text-sm text-gray-600">Hoặc cung cấp mã đặt vé trên cho nhân viên.</p>
            </div>
            <p class="text-sm text-gray-600 mb-6">Xin vui lòng kiểm tra kỹ thông tin đặt vé. Nếu có bất kỳ sai sót hoặc thắc mắc, đừng ngần ngại liên hệ với chúng tôi.</p>
            <p class="mt-8">Trân trọng,<br><strong class="text-red-600">{self.sender_name}</strong></p>
            </div>
            <div class="bg-gray-100 text-center text-xs text-gray-500 py-4 px-6 border-t border-gray-200 rounded-b-lg">
            <p class="mb-2">Đây là email tự động, vui lòng không phản hồi trực tiếp.</p>
            <p>&copy; {datetime.now().year} <strong class="text-red-600">{self.sender_name}</strong>. Mọi quyền được bảo lưu.</p>
            </div>
            </div>
            </body>
            </html>
            """

            html_body_inlined = transform(html_template_with_tailwind_booking)

            plain_text_body = f"""\
Xác nhận Đặt Vé Thành Công
--------------------------
Chào bạn,

Cảm ơn bạn đã đặt vé tại website của chúng tôi. Dưới đây là thông tin đặt vé của bạn:

Mã đặt vé: {booking_details.get('booking_id', 'N/A')}
Họ và tên: {booking_details.get('customer_name', 'N/A')}
Ngày khởi hành: {booking_details.get('departure_date', 'N/A')}
Điểm đi: {booking_details.get('origin', 'N/A')}
Điểm đến: {booking_details.get('destination', 'N/A')}
Thời gian: {booking_details.get('time', 'N/A')}
Số lượng vé: {booking_details.get('ticket_count', 'N/A')}

Vui lòng kiểm tra kỹ thông tin và liên hệ với chúng tôi nếu có bất kỳ câu hỏi nào.

Trân trọng,
Đội ngũ {self.sender_name}

---
Đây là email tự động, vui lòng không trả lời.
© {datetime.now().year} {self.sender_name}. All rights reserved.
            """

            msg.attach(MIMEText(plain_text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body_inlined, 'html', 'utf-8'))

            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.username, to_email, msg.as_string())

            return True

        except Exception as e:
            print(f"Lỗi khi gửi email xác nhận đặt chỗ: {str(e)}")
            return False