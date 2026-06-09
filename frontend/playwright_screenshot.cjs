const { chromium } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

async function run() {
    console.log("Starting Playwright screenshot capture using @playwright/test...");
    
    // Create output directory for screenshots
    const outputDir = path.join(__dirname, '..', 'scratch', 'screenshots');
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1280, height: 800 }
    });
    const page = await context.newPage();

    // Helper function to wait and capture
    async function capture(filename) {
        // Wait a small amount for animations to settle
        await page.waitForTimeout(1000);
        const imgPath = path.join(outputDir, filename);
        await page.screenshot({ path: imgPath });
        console.log(`Captured: ${filename}`);
    }

    try {
        // --- 1. Login Page ---
        console.log("Navigating to Login page...");
        await page.goto('http://localhost:5173/dang-nhap');
        await page.waitForLoadState('networkidle');
        await capture('login_page.png'); // Form 4.3

        // --- 2. Register Page (toggle tab) ---
        console.log("Toggling to Register tab...");
        await page.click('button:has-text("Đăng ký")');
        await capture('register_page.png'); // Form 4.4

        // --- 3. Log in ---
        console.log("Logging in as admin...");
        await page.click('button:has-text("Đăng nhập")');
        await page.getByPlaceholder('Địa chỉ Email', { exact: true }).fill('admin@word2latex.local');
        await page.getByPlaceholder('Mật khẩu', { exact: true }).fill('Admin@123456');
        await page.click('button:has-text("Bắt đầu ngay")');
        
        // Wait for redirect to /chuyen-doi or /quan-tri (for admin)
        await page.waitForURL(url => url.pathname.includes('/chuyen-doi') || url.pathname.includes('/quan-tri'));
        await page.waitForLoadState('networkidle');
        console.log("Successfully logged in!");

        // --- 4. Main Convert Page ---
        console.log("Navigating to Main Convert page...");
        await page.goto('http://localhost:5173/chuyen-doi');
        await page.waitForLoadState('networkidle');
        await capture('main_convert.png'); // Form 4.1

        // --- 6. Word-to-Word Page ---
        console.log("Navigating to Word-to-Word...");
        await page.goto('http://localhost:5173/chuyen-doi-word');
        await page.waitForLoadState('networkidle');
        await capture('word_to_word.png'); 

        // --- 7. Profile / Account details ---
        console.log("Navigating to Account Profile...");
        await page.goto('http://localhost:5173/tai-khoan');
        await page.waitForLoadState('networkidle');
        await capture('profile_main.png'); // Form 4.5
        await capture('profile_account.png'); // Form 4.7

        // --- 8. Transaction / Conversion History ---
        console.log("Navigating to Conversion History...");
        await page.goto('http://localhost:5173/lich-su');
        await page.waitForLoadState('networkidle');
        await capture('profile_history.png'); // Form 4.6

        // --- 9. Billing / Premium packages ---
        console.log("Navigating to Billing Packages...");
        await page.goto('http://localhost:5173/premium');
        await page.waitForLoadState('networkidle');
        await capture('billing_packages.png'); // Form 4.13

        // --- 10. SePay Payment QR Code ---
        console.log("Navigating to checkout page to show SePay QR...");
        await page.goto('http://localhost:5173/thanh-toan?package=pro');
        await page.waitForLoadState('networkidle');
        await capture('sepay_qr.png'); // Form 4.14

        // --- 11. Payment Completed Screen (Simulated) ---
        await capture('sepay_success.png'); // Form 4.15

        // --- 12. Admin Dashboard ---
        console.log("Navigating to Admin Dashboard...");
        await page.goto('http://localhost:5173/quan-tri');
        await page.waitForLoadState('networkidle');
        
        // Tab 1: Overview
        await capture('admin_overview.png'); // Form 4.8

        // Tab 2: Users
        console.log("Opening Admin Users tab...");
        await page.click('button:has-text("Người dùng")');
        await capture('admin_users.png'); // Form 4.9

        // Tab 3: History
        console.log("Opening Admin History tab...");
        await page.click('button:has-text("Lịch sử")');
        await capture('admin_history.png'); // Form 4.10

        // Tab 4: Config
        console.log("Opening Admin Config tab...");
        await page.click('button:has-text("Cấu hình")');
        await capture('admin_config.png'); // Form 4.11

        // Tab 5: Templates
        console.log("Opening Admin Templates tab...");
        await page.click('button:has-text("Template")');
        await capture('admin_templates.png'); // Form 4.2 (Template management)

        // Tab 6: Payments / Revenue
        console.log("Opening Admin Revenue tab...");
        await page.click('button:has-text("Thanh toán")');
        await capture('admin_revenue.png'); // Form 4.12

    } catch (err) {
        console.error("Error capturing screenshots:", err);
    } finally {
        await browser.close();
        console.log("Browser closed. Finished Playwright screenshot capture!");
    }
}

run();
