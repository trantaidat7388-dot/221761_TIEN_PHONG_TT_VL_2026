import { test, expect } from '@playwright/test'

const adminAuthResponse = {
  id: 9,
  username: 'admin',
  email: 'admin@word2latex.local',
  role: 'admin',
  plan_type: 'premium',
  token_balance: 25000,
}

test('admin dang nhap tu /dang-nhap duoc chuyen vao /quan-tri', async ({ page }) => {
  await page.route('**/api/auth/me', async (route) => {
    const auth = route.request().headers()['authorization'] || ''
    if (auth.includes('admin-token')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(adminAuthResponse),
      })
      return
    }
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'Unauthorized' }),
    })
  })

  await page.route('**/api/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'admin-token',
        token_type: 'bearer',
        user: adminAuthResponse,
      }),
    })
  })

  await page.route('**/api/admin/overview', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        tong_nguoi_dung: 1,
        tong_admin: 1,
        tong_premium: 1,
        tong_ban_ghi_lich_su: 0,
      }),
    })
  })

  await page.route('**/api/admin/users', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ danh_sach: [] }),
    })
  })

  await page.route('**/api/admin/history?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ danh_sach: [] }),
    })
  })

  await page.route('**/api/admin/audit-logs?*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ danh_sach: [] }),
    })
  })

  await page.route('**/api/admin/templates', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ danh_sach: [] }),
      })
      return
    }
    await route.continue()
  })

  await page.goto('/dang-nhap')

  await page.getByPlaceholder('Địa chỉ Email').fill('admin@word2latex.local')
  await page.getByPlaceholder('Mật khẩu').fill('Admin@123456')
  await page.getByRole('button', { name: 'Bắt đầu ngay' }).click()

  await expect(page).toHaveURL(/\/quan-tri$/)
  await expect(page.getByRole('heading', { name: 'Trang quản trị' })).toBeVisible()
})
