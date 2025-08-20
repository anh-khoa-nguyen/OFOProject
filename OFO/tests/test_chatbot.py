# OFO/tests/test_chatbot.py

import unittest
from unittest.mock import patch, MagicMock
from __init__ import create_app

# Import hàm cần test
from dao import call_gemini_api

class ChatbotTestCase(unittest.TestCase):
    def setUp(self):
        """Thiết lập môi trường test."""
        self.app = create_app('testing')
        # Cấu hình API key giả để test
        self.app.config['GOOGLE_API_KEY'] = 'fake-api-key-for-testing'
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Dọn dẹp môi trường test."""
        self.app_context.pop()

    # =================================================================
    # ===== CÁC BÀI TEST CHO CHỨC NĂNG CHATBOT (GEMINI API) ==========
    # =================================================================

    # Sử dụng patch để thay thế thư viện google.generativeai bằng một đối tượng giả (MagicMock)
    @patch('dao.genai')
    def test_call_gemini_api_success(self, mock_genai):
        """(CHATBOT) Kiểm tra gọi API thành công và trả về phản hồi mong đợi."""
        print(f"\n--- Mục đích: {self.test_call_gemini_api_success.__doc__} ---")

        # --- Dựng "sân khấu" cho Mock ---
        # 1. Tạo một đối tượng giả cho cuộc trò chuyện (convo)
        mock_convo = MagicMock()
        # 2. Cấu hình để thuộc tính 'last.text' của convo giả sẽ trả về câu trả lời mong muốn
        mock_convo.last.text = "Chào bạn, tôi có thể giúp gì cho bạn?"
        # 3. Cấu hình để model giả khi gọi start_chat() sẽ trả về convo giả ở trên
        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_convo
        # 4. Cấu hình để genai.GenerativeModel() giả sẽ trả về model giả ở trên
        mock_genai.GenerativeModel.return_value = mock_model
        # --- Kết thúc dựng sân khấu ---

        user_message = "Xin chào"
        response = call_gemini_api(user_message)

        # Kiểm tra xem hàm có trả về đúng nội dung đã được giả lập không
        self.assertEqual(response, "Chào bạn, tôi có thể giúp gì cho bạn?")

        # Kiểm tra xem các hàm của thư viện giả đã được gọi đúng cách chưa
        mock_genai.configure.assert_called_once_with(api_key='fake-api-key-for-testing')
        mock_model.start_chat.assert_called_once()
        mock_convo.send_message.assert_called_once_with(user_message)

        print(">>> Kết quả: ĐÚNG - Hàm trả về đúng phản hồi giả lập.")

    def test_call_gemini_api_no_key(self):
        """(CHATBOT) Kiểm tra hàm trả về lỗi khi không có API key."""
        print(f"\n--- Mục đích: {self.test_call_gemini_api_no_key.__doc__} ---")
        # Ghi đè config để không có API key
        self.app.config['GOOGLE_API_KEY'] = None

        response = call_gemini_api("test")
        self.assertEqual(response, "Lỗi: API Key của Google chưa được cấu hình.")
        print(">>> Kết quả: ĐÚNG - Trả về thông báo lỗi thiếu API key.")

    @patch('dao.genai.GenerativeModel')
    def test_call_gemini_api_exception(self, mock_generative_model):
        """(CHATBOT) Kiểm tra hàm trả về thông báo lỗi chung khi API gặp sự cố."""
        print(f"\n--- Mục đích: {self.test_call_gemini_api_exception.__doc__} ---")
        # Cấu hình để việc gọi hàm send_message sẽ ném ra một Exception
        mock_generative_model.side_effect = Exception("Lỗi kết nối mạng")

        response = call_gemini_api("test")
        self.assertEqual(response, "Xin lỗi, trợ lý ảo đang gặp sự cố. Vui lòng thử lại sau.")
        print(">>> Kết quả: ĐÚNG - Trả về thông báo lỗi chung cho người dùng.")

if __name__ == '__main__':
    unittest.main()