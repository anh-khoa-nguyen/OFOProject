const ADDRESS_SELECTION_PAGE_URL = '/';
const SEARCH_RESULTS_PAGE_URL = '/search';

describe('Address Selection Flow with Real API Calls', () => {

  beforeEach(() => {
    cy.visit(ADDRESS_SELECTION_PAGE_URL);
  });

  it('should allow user to search, select, and confirm an address, retrying if suggestions dont appear', () => {
    const userAddressInput = '33 Sơn Hà';
    const geocoderInputSelector = '#geocoder-container > .mapboxgl-ctrl-geocoder > .mapboxgl-ctrl-geocoder--input';
    const suggestionsSelector = '#geocoder-container .suggestions li > a';

    // 1. Lắng nghe các API call
    cy.intercept('GET', '**/place/autocomplete*').as('goongAutocomplete');
    cy.intercept('GET', '**/place/detail*').as('goongDetail');
    cy.intercept('POST', '/api/set-address').as('setAddressApiCall');

    // 2. SỬ DỤNG CUSTOM COMMAND MỚI
    // Lệnh này sẽ tự động gõ, chờ, và thử lại nếu cần
    cy.get(geocoderInputSelector).typeAndRetryUntilSuggestionsAppear(
      userAddressInput,
      suggestionsSelector
    );

    // 3. Khi lệnh trên chạy xong, chúng ta chắc chắn rằng gợi ý ĐÃ HIỂN THỊ.
    // Giờ mới là lúc an toàn để wait API và click.
    cy.wait('@goongAutocomplete');
    cy.get(suggestionsSelector).first().click();

    // Các bước còn lại giữ nguyên
    cy.wait('@goongDetail');
    cy.get('#confirm-address-btn').click();
    cy.wait('@setAddressApiCall');
    cy.url().should('include', SEARCH_RESULTS_PAGE_URL);
  });
  
  // Kịch bản 2 giữ nguyên...
  it('should allow user to open map, drag the marker, and confirm address', () => {
    cy.intercept('GET', '**/Geocode?latlng=*').as('goongReverseGeocode'); 
    cy.intercept('POST', '/api/set-address').as('setAddressApiCall');

    cy.get('button[data-bs-target="#mapModal"]').click();
    cy.get('#map-modal-container').should('be.visible');
    cy.wait(3000);

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
