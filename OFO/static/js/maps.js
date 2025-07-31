
  document.addEventListener('DOMContentLoaded', function () {
    // --- PHẦN 1: KHAI BÁO BIẾN VÀ HÀM TÁI SỬ DỤNG ---
    const goongApiKey = 'Tsvr8oOdFQgjgZnhXAp5Xm0es9BF6inVU9mHNY50';

    /**
     * HÀM TÁI SỬ DỤNG: Gửi địa chỉ và tọa độ lên server để lưu vào session.
     * @param {string} address - Địa chỉ dạng văn bản.
     * @param {object} lngLat - Đối tượng chứa {lng, lat}.
     * @param {HTMLElement} button - Nút đã được click để vô hiệu hóa.
     */
    function saveAddressToServer(address, lngLat, button) {
        if (!address || !lngLat) {
            alert("Vui lòng chọn một địa chỉ hợp lệ.");
            return;
        }

        if (button) button.disabled = true;

        fetch('/api/set-address', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                address: address,
                lat: lngLat.lat,
                lng: lngLat.lng
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                window.location.href = SEARCH_URL;
            } else {
                alert('Lỗi: ' + data.message);
                if (button) button.disabled = false;
            }
        })
        .catch(err => {
            console.log(err);
            alert("Lỗi mạng. Vui lòng thử lại.");
            if (button) button.disabled = false;
        });
    }

    // --- PHẦN 2: XỬ LÝ GEOCODER CHÍNH (NẾU TỒN TẠI) ---
    const geocoderContainer = document.getElementById('geocoder-container');
    console.log(geocoderContainer)
    const confirmButton = document.getElementById('confirm-address-btn');

    if (geocoderContainer && confirmButton) {
        let selectedAddress = null;
        let selectedLngLat = null;

        const geocoder = new GoongGeocoder({
          accessToken: goongApiKey,
          proximity: { longitude: 106.660172, latitude: 10.762622 },
          countries: 'vn',
          placeholder: 'Nhập địa chỉ của bạn...',
          debounceSearch: 500
        });
        geocoder.addTo('#geocoder-container');

        geocoder.on('result', function(e) {
            if (e.result && e.result.result) {
                const resultData = e.result.result;
                selectedAddress = resultData.formatted_address;
                if (resultData.geometry && resultData.geometry.location) {
                    selectedLngLat = {
                        lat: resultData.geometry.location.lat,
                        lng: resultData.geometry.location.lng
                    };
                }
            }
        });
        geocoder.on('clear', () => { selectedAddress = null; selectedLngLat = null; });

        confirmButton.addEventListener('click', function() {
            saveAddressToServer(selectedAddress, selectedLngLat, this);
        });
    }

    // --- PHẦN 3: XỬ LÝ MAP MODAL (LUÔN TỒN TẠI) ---
    const mapModal = document.getElementById('mapModal');
    if (mapModal) {
        let map = null;
        let mapInitialized = false;
        let mapSelectedAddress = null;
        let mapSelectedLngLat = null;
        const selectFromMapBtn = document.getElementById('select-address-from-map-btn');
        const coordinatesDisplay = document.getElementById('coordinates');

        async function reverseGeocode(lngLat) {
            selectFromMapBtn.disabled = true;
            selectFromMapBtn.textContent = 'Đang tìm địa chỉ...';
            try {
                const response = await fetch(`https://rsapi.goong.io/Geocode?latlng=${lngLat.lat},${lngLat.lng}&api_key=${goongApiKey}`);
                const data = await response.json();
                if (data.status === "OK" && data.results.length > 0) {
                    return data.results[0].formatted_address;
                } else {
                    throw new Error('Không tìm thấy địa chỉ cho vị trí này.');
                }
            } catch (error) {
                console.error(error);
                alert(error.message);
                return null;
            }
        }

        mapModal.addEventListener('show.bs.modal', function () {
            if (!mapInitialized) {
                goongjs.accessToken = 'xhiqMbwYAeMTkmNmS5n1EB2yGAWk9YGDOFVPfpne';
                map = new goongjs.Map({
                    container: 'map-modal-container',
                    style: 'https://tiles.goong.io/assets/goong_map_web.json',
                    center: [106.660172, 10.762622],
                    zoom: 13
                });

                const geolocate = new goongjs.GeolocateControl({
                    positionOptions: { enableHighAccuracy: true },
                    trackUserLocation: true
                });
                map.addControl(geolocate);

                const marker = new goongjs.Marker({ draggable: true })
                    .setLngLat([106.660172, 10.762622])
                    .addTo(map);

                const mapGeocoder = new GoongGeocoder({
                    accessToken: 'PxNaGKg1NIWUJsFT3DMBkqaDspx5VvdW9CePVHq1',
                    goongjs: goongjs
                });
                map.addControl(mapGeocoder);

                async function updateAddressFromLngLat(lngLat) {
                    coordinatesDisplay.innerHTML = `Kinh độ: ${lngLat.lng.toFixed(6)}<br />Vĩ độ: ${lngLat.lat.toFixed(6)}`;
                    const address = await reverseGeocode(lngLat);
                    if (address) {
                        mapSelectedAddress = address;
                        mapSelectedLngLat = lngLat;
                        selectFromMapBtn.disabled = false;
                        selectFromMapBtn.textContent = `Chọn: ${address.substring(0, 25)}...`;
                    }
                }

                marker.on('dragend', () => updateAddressFromLngLat(marker.getLngLat()));
                geolocate.on('geolocate', (e) => {
                    const coords = { lng: e.coords.longitude, lat: e.coords.latitude };
                    marker.setLngLat([coords.lng, coords.lat]);
                    updateAddressFromLngLat(coords);
                });
                mapGeocoder.on('result', (e) => {
                    if (e.result && e.result.result && e.result.result.geometry && e.result.result.geometry.location) {
                        const resultData = e.result.result;
                        const coords = {
                            lat: resultData.geometry.location.lat,
                            lng: resultData.geometry.location.lng
                        };
                        marker.setLngLat([coords.lng, coords.lat]);
                        updateAddressFromLngLat(coords);
                    }
                });
                mapInitialized = true;
            }
        });

        mapModal.addEventListener('shown.bs.modal', () => { if (map) map.resize(); });

        selectFromMapBtn.addEventListener('click', function() {
            saveAddressToServer(mapSelectedAddress, mapSelectedLngLat, this);
        });
    }
  });
