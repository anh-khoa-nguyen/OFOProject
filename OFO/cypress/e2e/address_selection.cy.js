// cypress/e2e/address_selection.cy.js

const ADDRESS_SELECTION_PAGE_URL = '/';
const SEARCH_RESULTS_PAGE_URL = '/search';

describe('Address Selection Flow with Real API Calls', () => {

  beforeEach(() => {
    cy.visit(ADDRESS_SELECTION_PAGE_URL);
  });

  /**
   * KỊCH BẢN 1: TÌM KIẾM BẰNG Ô INPUT CHÍNH
   * Đã sửa lỗi race condition.
   */
  it('should allow user to search, select, and confirm an address using the main geocoder', () => {
    const userAddressInput = '33 Sơn Hà';

    // 1. Lắng nghe TẤT CẢ các API call quan trọng
    cy.intercept('GET', '**/place/autocomplete*').as('goongAutocomplete');
    // THÊM MỚI: Lắng nghe API lấy chi tiết địa điểm
    cy.intercept('GET', '**/place/detail*').as('goongDetail');
    cy.intercept('POST', '/api/set-address').as('setAddressApiCall');

    // 2. Gõ địa chỉ vào ô input
    cy.get('#geocoder-container > .mapboxgl-ctrl-geocoder > .mapboxgl-ctrl-geocoder--input')
      .type(userAddressInput, { delay: 100 });

    // 3. Chờ API autocomplete hoàn thành
    cy.wait('@goongAutocomplete');

    // 4. Click vào kết quả đầu tiên
    cy.get('#geocoder-container .suggestions li > a')
      .first()
      .should('be.visible')
      .click();

    // 5. THÊM BƯỚC CHỜ QUAN TRỌNG NHẤT
    // Chờ cho đến khi API lấy chi tiết địa điểm hoàn thành.
    // Điều này đảm bảo JS đã có đủ thời gian để cập nhật tọa độ.
    cy.wait('@goongDetail');

    // 6. Bây giờ mới click vào nút "Xác nhận địa chỉ"
    cy.get('#confirm-address-btn').click();

    // 7. Chờ API backend được gọi
    cy.wait('@setAddressApiCall');

    // 8. Kiểm tra chuyển hướng
    cy.url().should('include', SEARCH_RESULTS_PAGE_URL);
  });

  /**
   * KỊCH BẢN 2: KÉO-THẢ MARKER TRÊN BẢN ĐỒ (Giữ nguyên, đã đúng)
   */
  it('should allow user to open map, drag the marker, and confirm address', () => {
    cy.intercept('GET', '**/Geocode?latlng=*').as('goongReverseGeocode'); // Lưu ý: API này khác với autocomplete
    cy.intercept('POST', '/api/set-address').as('setAddressApiCall');

    cy.get('button[data-bs-target="#mapModal"]').click();
    cy.get('#map-modal-container').should('be.visible');
    cy.wait(1000);

    const marker = cy.get('.mapboxgl-marker[aria-label="Map marker"]');
    marker.should('be.visible');

    marker
      .trigger('mousedown', { which: 1, force: true })
      .trigger('mousemove', { clientX: 100, clientY: 50, force: true })
      .trigger('mouseup', { force: true });

    cy.wait('@goongReverseGeocode');

    const selectButton = cy.get('#select-address-from-map-btn');
    selectButton.should('not.be.disabled');
    selectButton.click();

    cy.wait('@setAddressApiCall');
    cy.url().should('include', SEARCH_RESULTS_PAGE_URL);
  });
});