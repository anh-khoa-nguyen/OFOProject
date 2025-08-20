// cypress/e2e/chatbot-live-api.cy.js

describe('Chatbot Functionality with LIVE API', () => {

  beforeEach(() => {
    cy.visit('/');

    // QUAN TRỌNG: Chúng ta vẫn dùng cy.intercept, nhưng KHÔNG phải để mock.
    // Lần này, chúng ta dùng nó chỉ để "lắng nghe" request mạng thật
    // và gán cho nó một bí danh. Điều này cho phép chúng ta dùng cy.wait()
    // để chờ cho đến khi API thật trả lời xong.
    cy.intercept('POST', '/api/chat').as('realChatApiCall');
  });

  /**
   * KỊCH BẢN: Gửi tin nhắn và nhận phản hồi thật từ AI
   */
  it('should send a message and receive a valid, non-empty response from the real AI', () => {
    // 1. Mở cửa sổ chat
    cy.get('#chat-fab-toggle').click();
    cy.get('#chat-widget').should('be.visible');

    // 2. Gõ một câu hỏi thực tế
    cy.get('#chat-input').type('Gợi ý cho tôi một món ăn cho bữa tối?', { delay: 50 });

    // 3. Bấm nút gửi
    cy.get('#chat-send-btn').click();

    // 4. KIỂM TRA QUAN TRỌNG: Tin nhắn của người dùng phải hiện ra
    cy.get('.chat-message.user').should('be.visible').and('contain', 'Gợi ý cho tôi một món ăn');

    // 5. CHỜ ĐỢI QUAN TRỌNG: Chờ cho API thật hoàn thành.
    // Tăng thời gian chờ mặc định lên 30 giây (30000ms) vì AI có thể mất nhiều thời gian.
    cy.wait('@realChatApiCall', { timeout: 30000 });

    // 6. KIỂM TRA KẾT QUẢ:
    // Chúng ta không biết AI sẽ trả lời gì, nhưng chúng ta có thể kiểm tra những điều sau:
    cy.get('.chat-message.assistant').last()
      .should('be.visible') // a) Phải có một tin nhắn trả lời hiện ra.
      .and('not.be.empty') // b) Nội dung của nó không được rỗng.
      .and('not.contain', 'Rất xin lỗi, đã có lỗi xảy ra'); // c) Nó không được chứa tin nhắn báo lỗi.

    cy.log('Received a real response from the AI assistant!');
  });

  /**
   * KỊCH BẢN: Bấm vào gợi ý và nhận phản hồi thật
   */
  it('should click a suggestion and receive a valid response from the real AI', () => {
    // 1. Mở cửa sổ chat
    cy.get('#chat-fab-toggle').click();
    cy.get('#chat-widget').should('be.visible');

    // 2. Click vào chip gợi ý
    cy.get('.suggestion-chip').contains('Ưu đãi hot').should('be.visible').click();

    // 3. Chờ API thật hoàn thành
    cy.wait('@realChatApiCall', { timeout: 30000 });

    // 4. Kiểm tra tin nhắn của người dùng (từ chip)
    cy.get('.chat-message.user').should('be.visible').and('contain', 'Ưu đãi hot');

    // 5. Kiểm tra phản hồi thật từ AI
    cy.get('.chat-message.assistant').last()
      .should('be.visible')
      .and('not.be.empty')
      .and('not.contain', 'Rất xin lỗi, đã có lỗi xảy ra');
  });

});