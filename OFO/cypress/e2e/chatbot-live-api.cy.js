// cypress/e2e/chatbot-live-api.cy.js

describe('Chatbot Functionality with LIVE API', () => {

  // !!! ĐÂY LÀ THAY ĐỔI QUAN TRỌNG NHẤT !!!
  // Selector đã được cập nhật dựa trên mã HTML bạn cung cấp.
  const SCROLLABLE_CONTAINER_SELECTOR = '#chat-widget-body'; 
  const obstructingElementSelector = '.status';

  beforeEach(() => {
    cy.visit('/');
    cy.get('#chat-fab-toggle').click();
    cy.get('#chat-widget').should('be.visible');
    cy.intercept('POST', '/api/chat').as('realChatApiCall');

    // Chờ phần tử che phủ xuất hiện rồi mới xóa nó
    cy.get(obstructingElementSelector, { timeout: 10000 }).should('be.visible').invoke('remove');
  });

  /**
   * KỊCH BẢN 1: GỬI TIN NHẮN THÔNG THƯỜNG
   */
  it('should send a message and receive a valid, non-empty response from the real AI', () => {
    const userInput = 'Gợi ý cho tôi một món ăn cho bữa tối?';

    cy.get('#chat-input').type(userInput);
    cy.get('#chat-send-btn').click();
    cy.wait('@realChatApiCall');

    // === Logic đã sửa hoàn chỉnh ===
    // 1. Chờ tin nhắn người dùng TỒN TẠI
    cy.get('.chat-message.user').last().should('exist');
    // 2. Cuộn ĐÚNG container 
    cy.get(SCROLLABLE_CONTAINER_SELECTOR).scrollTo('bottom', { ensureScrollable: false });
    // 3. Bây giờ mới kiểm tra HIỂN THỊ
    cy.get('.chat-message.user').last()
      .should('exist')
      .and('contain', 'Gợi ý cho tôi một món ăn');

    // Tương tự cho tin nhắn của AI
    cy.get('.chat-message.assistant').last().should('exist');
    cy.get(SCROLLABLE_CONTAINER_SELECTOR).scrollTo('bottom', { ensureScrollable: false });
    cy.get('.chat-message.assistant').last()
      .should('exist')
      .and('not.be.empty');
  });

  /**
   * KỊCH BẢN 2: CLICK VÀO CHIP GỢI Ý
   */
  it('should click a suggestion and receive a valid response from the real AI', () => {
    const suggestionText = 'Ưu đãi hot';

    cy.get('.suggestion-chip').contains(suggestionText).click();
    cy.wait('@realChatApiCall');

    // === Logic đã sửa hoàn chỉnh ===
    cy.get('.chat-message.user').last().should('exist');
    cy.get(SCROLLABLE_CONTAINER_SELECTOR).scrollTo('bottom', { ensureScrollable: false });
    cy.get('.chat-message.user').last()
      .should('exist')
      .and('contain', suggestionText);

    cy.get('.chat-message.assistant').last().should('exist');
    cy.get(SCROLLABLE_CONTAINER_SELECTOR).scrollTo('bottom', { ensureScrollable: false });
    cy.get('.chat-message.assistant').last()
      .should('exist')
      .and('not.be.empty');
  });
});
