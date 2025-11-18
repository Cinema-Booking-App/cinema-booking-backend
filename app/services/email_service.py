from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
import random
import string
import ssl
import qrcode
import json
from io import BytesIO
import base64
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

    def generate_ticket_qr_bytes(self, ticket_info: dict) -> bytes:
        """Tạo QR code và trả về raw PNG bytes (không base64).

        Tương tự với generate_ticket_qr: dùng 'seats' nếu có, hỗ trợ 'seat' đơn.
        Trả về bytes ảnh PNG của QR chứa JSON payload + text_vn.
        """

        # Normalize seats into list[str]
        seats = []
        if 'seats' in ticket_info and isinstance(ticket_info['seats'], list):
            for s in ticket_info['seats']:
                if isinstance(s, dict):
                    code = s.get('seat') or s.get('seat_code') or None
                    seats.append(str(code) if code is not None else str(s))
                else:
                    seats.append(str(s))
        elif ticket_info.get('seat'):
            seats = [str(ticket_info.get('seat'))]

        seats_display = ', '.join(seats) if seats else ''

        qr_data = f"""
Mã đặt vé: {ticket_info.get('booking_id')}
Khách hàng: {ticket_info.get('customer_name')}
Phim: {ticket_info.get('movie_name')}
Suất chiếu: {ticket_info.get('showtime')}
Ghế: {seats_display}
"""

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def send_ticket_email(self, to_email: str, ticket_info: dict) -> bool:
        """
        Gửi email kèm 1 mã QR duy nhất cho toàn bộ vé (danh sách ghế).
        QR này sẽ chứa toàn bộ thông tin khách hàng và danh sách ghế.
        """
        if not to_email:
            print("send_ticket_email: missing to_email, skip sending")
            return False

        # Normalize seats into a list of seat codes (strings).
        # Accepts: ticket_info['seats'] as list[str] or list[dict], or single 'seat' string.
        seats_codes = []
        if 'seats' in ticket_info and isinstance(ticket_info['seats'], list):
            for item in ticket_info['seats']:
                if isinstance(item, dict):
                    # common dict shapes: {'seat': 'A1'} or {'seat_code': 'A1'}
                    code = item.get('seat') or item.get('seat_code') or None
                    if code is None:
                        # fallback to string representation
                        code = str(item)
                else:
                    code = str(item)
                seats_codes.append(code)
        elif ticket_info.get('seat'):
            seats_codes = [str(ticket_info.get('seat'))]

        try:
            msg_root = MIMEMultipart('related')
            msg_root['From'] = formataddr((self.sender_name, self.username))
            msg_root['To'] = to_email
            msg_root['Subject'] = f"Thông tin vé - {ticket_info.get('booking_id', '')}"

            msg_alternative = MIMEMultipart('alternative')
            msg_root.attach(msg_alternative)

            # Plain summary text
            seats_display = ', '.join(seats_codes) if seats_codes else ''
            plain_lines = [
                f"Mã đặt vé: {ticket_info.get('booking_id', '')}",
                f"Khách hàng: {ticket_info.get('customer_name', '')}",
                f"Phim: {ticket_info.get('movie_name', '')}",
                f"Suất chiếu: {ticket_info.get('showtime', '')}",
                f"Ghế: {seats_display}"
            ]
            plain_text = "\n".join(plain_lines)
            msg_alternative.attach(MIMEText(plain_text, 'plain', 'utf-8'))

            # Tạo 1 mã QR duy nhất cho toàn bộ vé (seats as list of strings)
            qr_ticket_info = dict(ticket_info)
            if seats_codes:
                qr_ticket_info['seats'] = seats_codes
            img_bytes = self.generate_ticket_qr_bytes(qr_ticket_info)

            # HTML email
            html_template = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Thông tin vé xem phim</h2>
                <p><strong>Mã đặt vé:</strong> {ticket_info.get('booking_id', '')}</p>
                <p><strong>Khách hàng:</strong> {ticket_info.get('customer_name', '')}</p>
                <p><strong>Phim:</strong> {ticket_info.get('movie_name', '')}</p>
                <p><strong>Suất chiếu:</strong> {ticket_info.get('showtime', '')}</p>
                <p><strong>Ghế:</strong> {seats_display}</p>
                <div style="margin:18px 0; text-align:center;">
                    <img src="cid:ticket_qr" alt="QR toàn bộ vé" style="width:180px; height:180px;"/>
                </div>
            </body>
            </html>
            """
            msg_alternative.attach(MIMEText(html_template, 'html', 'utf-8'))

            # Đính kèm QR code (inline và attachment)
            mime_img = MIMEImage(img_bytes, _subtype='png')
            mime_img.add_header('Content-ID', '<ticket_qr>')
            mime_img.add_header('Content-Disposition', 'inline', filename='ticket_qr.png')
            msg_root.attach(mime_img)

            attachment = MIMEImage(img_bytes, _subtype='png')
            attachment.add_header('Content-Disposition', 'attachment', filename='ticket_qr.png')
            msg_root.attach(attachment)

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.username, to_email, msg_root.as_string())

            return True

        except Exception as e:
            print(f"Lỗi khi gửi email vé: {str(e)}")
            return False