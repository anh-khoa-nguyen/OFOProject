const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://127.0.0.1:5000', // <-- THAY BẰNG ĐỊA CHỈ SERVER CỦA BẠN
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
});