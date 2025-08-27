// cypress/e2e/chatbot-live-api.cy.js

describe('Chatbot Functionality with LIVE API', () => {
  beforeEach(() => {
    // Luôn bắt đầu từ trang chủ và mở chat widget
    cy.visit('/');
    cy.get('#chat-fab-toggle').click();
    cy.get('#chat-widget').should('be.visible');
    
    // Đặt một alias cho API thật để dễ dàng chờ đợi
    cy.intercept('POST', '/api/chat').as('realChatApiCall');
  });

  /**
   * KỊCH BẢN 1: GỬI TIN NHẮN THÔNG THƯỜNG
   */
  it('should send a message and receive a valid, non-empty response from the real AI', () => {
    const userInput = 'Gợi ý cho tôi một món ăn cho bữa tối?';

    // 1. Gõ và gửi tin nhắn
    cy.get('#chat-input').type(userInput, { delay: 50 });
    cy.get('#chat-send-btn').click();
    
    // CHỜ API ĐỂ ĐẢM BẢO GIAO DIỆN CÓ THỜI GIAN CẬP NHẬT
    cy.wait('@realChatApiCall');

    // 2. Kiểm tra tin nhắn của người dùng đã xuất hiện
    // SỬA LỖI: Thêm .last() và .scrollIntoView()
    cy.get('.chat-message.user').last() // Lấy tin nhắn người dùng cuối cùng
      .scrollIntoView() // Cuộn đến nó
      .should('be.visible') // BÂY GIỜ mới kiểm tra
      .and('contain', 'Gợi ý cho tôi một món ăn');

    // 3. Kiểm tra phản hồi từ AI
    cy.get('.chat-message.assistant').last()
      .scrollIntoView() // Cuộn đến tin nhắn cuối cùng của assistant
      .should('be.visible') 
      .and('not.be.empty')
      .and('not.contain', 'Rất xin lỗi, đã có lỗi xảy ra');
  });

  /**
   * KỊCH BẢN 2: CLICK VÀO CHIP GỢI Ý (Đã đúng từ lần sửa trước)
   */
  it('should click a suggestion and receive a valid response from the real AI', () => {
    const suggestionText = 'Ưu đãi hot';

    // 1. Tìm và click vào chip gợi ý
    cy.get('.suggestion-chip').contains(suggestionText)
      .should('be.visible')
      .click();

    // 2. Chờ API call hoàn tất
    cy.wait('@realChatApiCall');

    // 3. Kiểm tra tin nhắn của người dùng (từ chip) đã xuất hiện
    cy.get('.chat-message.user').last() 
      .scrollIntoView()
      .should('be.visible')
      .and('contain', suggestionText);

    // 4. Kiểm tra phản hồi thật từ AI
    cy.get('.chat-message.assistant').last()
      .scrollIntoView()
      .should('be.visible')
      .and('not.be.empty');
  });
});
