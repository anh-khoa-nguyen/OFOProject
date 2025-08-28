// cypress/e2e/chatbot.cy.js

describe('Chatbot Functionality', () => {

  beforeEach(() => {
    cy.visit('/');
    cy.intercept('POST', '/api/chat').as('chatApiCall');
  });

  /**
   * KỊCH BẢN 1: KIỂM TRA MỞ VÀ ĐÓNG CỬA SỔ CHAT
   */
  it('should open and close the chat widget', () => {
    // Ban đầu, cửa sổ chat phải đang ẩn
    cy.get('#chat-widget').should('not.be.visible');

    // Mở chat
    cy.get('#chat-fab-toggle').click();

    // CHỜ THÔNG MINH: Chờ cho đến khi cửa sổ chat THỰC SỰ HIỂN THỊ
    cy.get('#chat-widget').should('be.visible');

    // Đóng chat
    cy.get('#chat-widget-close').click();

    // CHỜ THÔNG MINH: Chờ cho đến khi cửa sổ chat THỰC SỰ BIẾN MẤT
    cy.get('#chat-widget').should('not.be.visible');
  });

  /**
   * KỊCH BẢN 2: GỬI TIN NHẮN BẰNG CÁCH GÕ VÀ BẤM NÚT GỬI
   */
  it('should send a message by typing and clicking the send button', () => {
    cy.intercept('POST', '/api/chat', {
      body: { reply: 'Đây là câu trả lời tự động từ Cypress.' }
    }).as('chatApiCall');

    cy.get('#chat-fab-toggle').click();
    cy.get('#chat-widget').should('be.visible');

    // LÀM CHẬM THAO TÁC: Gõ chậm lại để giống người thật hơn
    cy.get('#chat-input').type('Xin chào trợ lý ảo', { delay: 50 });

    cy.get('#chat-send-btn').click();

    // CHỜ API: Đây là bước chờ quan trọng nhất
    cy.wait('@chatApiCall');

    // CHỜ GIAO DIỆN: Kiểm tra xem tin nhắn của người dùng đã hiện ra chưa
    cy.get('.chat-message.user').should('be.visible').and('contain', 'Xin chào trợ lý ảo');

    // CHỜ GIAO DIỆN: Kiểm tra xem câu trả lời của trợ lý ảo đã hiện ra chưa
    cy.get('.chat-message.assistant').last().should('be.visible').and('contain', 'Đây là câu trả lời tự động');
  });

  /**
   * KỊCH BẢN 3: GỬI TIN NHẮN BẰNG CÁCH BẤM VÀO GỢI Ý
   */
  it('should send a message by clicking a suggestion chip', () => {
    cy.intercept('POST', '/api/chat', {
      body: { reply: 'Bạn muốn ăn gì, để Kymie gợi ý nhé!' }
    }).as('chatApiCall');

    cy.get('#chat-fab-toggle').click();
    cy.get('#chat-widget').should('be.visible');

    // CHỜ GIAO DIỆN: Chờ cho nút gợi ý hiện ra trước khi click
    cy.get('.suggestion-chip').contains('Ăn gì hôm nay?').should('be.visible').click();

    // CHỜ API
    cy.wait('@chatApiCall');

    // CHỜ GIAO DIỆN
    cy.get('.chat-message.user').should('be.visible').and('contain', 'Ăn gì hôm nay?');
    cy.get('.chat-message.assistant').last().should('be.visible').and('contain', 'Bạn muốn ăn gì');
  });

  /**
   * KỊCH BẢN 4: KIỂM TRA HIỂN THỊ LỖI KHI API GẶP SỰ CỐ
   */
  it('should display an error message when the API fails', () => {
    cy.intercept('POST', '/api/chat', { forceNetworkError: true }).as('chatApiCall');

    cy.get('#chat-fab-toggle').click();
    cy.get('#chat-widget').should('be.visible');

    cy.get('#chat-input').type('Một tin nhắn sẽ gây lỗi', { delay: 50 });
    cy.get('#chat-send-btn').click();

    // CHỜ API (bị lỗi)
    cy.wait('@chatApiCall');

    // CHỜ GIAO DIỆN
    cy.get('.chat-message.assistant').last().should('be.visible').and('contain', 'Rất xin lỗi, đã có lỗi xảy ra');
  });

  /**
   * KỊCH BẢN 5: KIỂM TRA VIỆC RENDER MARKDOWN (IN ĐẬM VÀ XUỐNG DÒNG)
   */
  it('should correctly render markdown for bold text and newlines', () => {
    const markdownReply = 'Đây là chữ **in đậm**.\nVà đây là một dòng mới.';
    cy.intercept('POST', '/api/chat', {
      body: { reply: markdownReply }
    }).as('chatApiCall');

    cy.get('#chat-fab-toggle').click();
    cy.get('#chat-widget').should('be.visible');
    cy.get('#chat-input').type('Test markdown', { delay: 50 });
    cy.get('#chat-send-btn').click();
    cy.wait('@chatApiCall');

    // SỬ DỤNG .within() ĐỂ THỰC HIỆN CÁC KIỂM TRA BÊN TRONG TIN NHẮN
    cy.get('.chat-message.assistant').last().should('be.visible').within(() => {
      // Bây giờ, tất cả các lệnh cy.get() hoặc .find() bên trong khối này
      // sẽ tự động tìm kiếm bên trong tin nhắn của trợ lý ảo.

      // 1. Tìm thẻ <strong> và kiểm tra nội dung
      cy.get('strong').should('have.text', 'in đậm');

      // 2. Tìm thẻ <br> và kiểm tra sự tồn tại
      cy.get('br').should('exist');
    });
  });
});