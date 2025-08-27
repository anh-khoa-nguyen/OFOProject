/**
 * Gõ text vào một element. Nếu không thấy suggestionSelector xuất hiện sau một khoảng thời gian,
 * nó sẽ xóa đi và thử gõ lại. Lặp lại cho đến khi thành công hoặc hết số lần thử.
 *
 * @param {string} textToType - Đoạn text cần gõ vào.
 * @param {string} suggestionSelector - Selector của phần tử gợi ý cần chờ.
 * @param {object} options - Tùy chọn.
 * @param {number} options.retries - Số lần thử lại tối đa.
 * @param {number} options.interval - Thời gian chờ giữa các lần thử (ms).
 */
Cypress.Commands.add('typeAndRetryUntilSuggestionsAppear', { prevSubject: 'element' }, (subject, textToType, suggestionSelector, options = {}) => {
  const { retries = 5, interval = 7000 } = options; // Mặc định thử lại 2 lần, mỗi lần cách nhau 2s

  const attempt = (attemptNum) => {
    // Nếu hết số lần thử, báo lỗi
    if (attemptNum > retries) {
      throw new Error(`Element '${suggestionSelector}' did not appear after ${retries} retries.`);
    }

    cy.log(`Search attempt #${attemptNum + 1}`);

    // Ở lần thử lại (lần > 0), xóa sạch input để đảm bảo gõ lại từ đầu
    if (attemptNum > 0) {
      cy.wrap(subject).clear();
    }

    // Gõ text và cho nó một chút delay để giống người thật hơn
    cy.wrap(subject).type(textToType, { delay: 500 });

    // Đợi một khoảng thời gian cho cơ chế debouncing của app hoạt động
    cy.wait(interval);

    // Kiểm tra xem gợi ý đã xuất hiện chưa MÀ KHÔNG GÂY LỖI TEST
    // Đây là kỹ thuật quan trọng nhất
    cy.get('body').then($body => {
      if ($body.find(suggestionSelector).length === 0) {
        // Nếu không tìm thấy, gọi lại chính nó để thử lại
        cy.log(`Suggestions not found, retrying...`);
        attempt(attemptNum + 1);
      } else {
        // Nếu tìm thấy, log thành công và kết thúc
        cy.log('Suggestions found!');
      }
    });
  };

  attempt(0); // Bắt đầu lần thử đầu tiên
});
