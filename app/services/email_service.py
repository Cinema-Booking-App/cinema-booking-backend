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
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, sender_name: str):
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
            html_template_with_tailwind = f"""\
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                </style>
            </head>
            <body class="font-sans text-gray-800 bg-gray-100 p-0 m-0">
                <div class="max-w-xl mx-auto bg-white rounded-lg shadow-md overflow-hidden my-8">
                    <div class="bg-blue-600 text-white text-center py-4 px-6 rounded-t-lg">
                        <h2 class="text-2xl font-bold">Xác nhận Tài khoản</h2>
                    </div>
                    <div class="p-6">
                        <p class="mb-4">Chào bạn,</p>
                        <p class="mb-4">Cảm ơn bạn đã đăng ký tài khoản tại website của chúng tôi. Để hoàn tất việc đăng ký, vui lòng sử dụng mã xác nhận bên dưới:</p>
                        <div class="block w-fit mx-auto my-5 p-4 bg-gray-200 rounded-md text-3xl font-bold text-blue-600 text-center border border-dashed border-gray-400">
                            {verification_code}
                        </div>
                        <p class="mb-4 text-sm text-gray-600">Mã này sẽ hết hạn sau <strong>15 phút</strong>.</p>
                        <p class="text-sm text-gray-600">Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email này.</p>
                        <p class="mt-8">Trân trọng,<br>Đội ngũ {self.sender_name}</p>
                    </div>
                    <div class="text-center text-xs text-gray-500 mt-8 py-3 px-6 border-t border-gray-200">
                        <p>Đây là email tự động, vui lòng không trả lời.</p>
                        <p>&copy; {datetime.now().year} {self.sender_name}. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Sử dụng Premailer để chuyển đổi CSS classes thành inline CSS
            html_body_inlined = transform(html_template_with_tailwind)

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
                <style>
                    /* Đảm bảo CSS Tailwind được đưa vào đây nếu bạn muốn Premailer xử lý */
                    body {{ font-family: Arial, sans-serif; }}
                </style>
            </head>
            <body class="font-sans text-gray-800 bg-gray-100 p-0 m-0">
                <div class="max-w-xl mx-auto bg-white rounded-lg shadow-md overflow-hidden my-8">
                    <div class="bg-green-600 text-white text-center py-4 px-6 rounded-t-lg">
                        <h2 class="text-2xl font-bold">Xác nhận Đặt Vé Thành Công</h2>
                    </div>
                    <div class="p-6">
                        <p class="mb-4">Chào bạn,</p>
                        <p class="mb-4">Cảm ơn bạn đã đặt vé tại website của chúng tôi. Dưới đây là thông tin đặt vé của bạn:</p>
                        <ul class="list-none p-0 mb-4">
                            <li class="mb-2"><strong>Mã đặt vé:</strong> {booking_details.get('booking_id', 'N/A')}</li>
                            <li class="mb-2"><strong>Họ và tên:</strong> {booking_details.get('customer_name', 'N/A')}</li>
                            <li class="mb-2"><strong>Ngày khởi hành:</strong> {booking_details.get('departure_date', 'N/A')}</li>
                            <li class="mb-2"><strong>Điểm đi:</strong> {booking_details.get('origin', 'N/A')}</li>
                            <li class="mb-2"><strong>Điểm đến:</strong> {booking_details.get('destination', 'N/A')}</li>
                            <li class="mb-2"><strong>Thời gian:</strong> {booking_details.get('time', 'N/A')}</li>
                            <li class="mb-2"><strong>Số lượng vé:</strong> {booking_details.get('ticket_count', 'N/A')}</li>
                        </ul>
                        <p>Vui lòng kiểm tra kỹ thông tin và liên hệ với chúng tôi nếu có bất kỳ câu hỏi nào.</p>
                        <p class="mt-8">Trân trọng,<br>Đội ngũ {self.sender_name}</p>
                    </div>
                    <div class="text-center text-xs text-gray-500 mt-8 py-3 px-6 border-t border-gray-200">
                        <p>Đây là email tự động, vui lòng không trả lời.</p>
                        <p>&copy; {datetime.now().year} {self.sender_name}. All rights reserved.</p>
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