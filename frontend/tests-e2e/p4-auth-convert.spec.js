import { test, expect } from '@playwright/test'

const SSE_GIA_LAP = [
  'data: {"step":1,"msg":"Nhan file"}\n\n',
  'data: {"step":3,"msg":"Dang render"}\n\n',
  'data: {"step":5,"msg":"Hoan tat","done":true,"tex_content":"\\\\documentclass{article}","job_id":"job-e2e-001","ten_file_zip":"output.zip","ten_file_latex":"main.tex","metadata":{"so_trang":2,"so_cong_thuc":3,"so_hinh_anh":1,"so_bang":1,"thoi_gian_xu_ly_giay":4}}\n\n'
].join('')

test.beforeEach(async ({ page }) => {
  await page.route('**/api/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'header.payload.signature',
        user: {
          uid: 1,
          username: 'tester',
          email: 'tester@example.com',
        },
      }),
    })
  })

  await page.route('**/api/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ uid: 1, username: 'tester', email: 'tester@example.com' }),
    })
  })

  await page.route('**/api/templates', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        templates: [
          { id: 'ieee_conference', ten: 'IEEE Conference', loai: 'mac_dinh' },
        ],
      }),
    })
  })

  await page.route('**/api/chuyen-doi-stream*', async (route) => {
    await route.fulfill({
      status: 200,
      headers: {
        'content-type': 'text/event-stream; charset=utf-8',
        'cache-control': 'no-cache',
      },
      body: SSE_GIA_LAP,
    })
  })

  await page.route('**/api/download/job-e2e-001', async (route) => {
    await route.fulfill({
      status: 200,
      headers: {
        'content-type': 'application/zip',
        'content-disposition': 'attachment; filename="output.zip"',
      },
      body: 'zip-binary-content',
    })
  })

  await page.route('**/api/compile-pdf/job-e2e-001', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        thanh_cong: true,
        so_trang: 2,
        ten_file_pdf: 'output.pdf',
        pdf_url: '/api/tai-ve-pdf/job-e2e-001',
      }),
    })
  })

  await page.route('**/api/tai-ve-pdf/job-e2e-001', async (route) => {
    await route.fulfill({
      status: 200,
      headers: {
        'content-type': 'application/pdf',
        'content-disposition': 'attachment; filename="output.pdf"',
      },
      body: '%PDF-1.4\n%mock\n',
    })
  })
})

test('dang nhap va chuyen doi file thanh cong', async ({ page }) => {
  await page.goto('/dang-nhap')

  await page.getByPlaceholder('Email của bạn').fill('tester@example.com')
  await page.getByPlaceholder('Mật khẩu (ít nhất 6 ký tự)').fill('123456')
  await page.locator('form button[type="submit"]').click()

  await expect(page.getByRole('heading', { name: 'Chuyển đổi Word sang LaTeX' })).toBeVisible()

  const oNhapFile = page.locator('input[type="file"]').first()
  await oNhapFile.setInputFiles({
    name: 'tai-lieu.docx',
    mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    buffer: Buffer.from('fake-docx-content'),
  })

  await page.getByRole('button', { name: 'Bắt đầu chuyển đổi' }).click()

  await expect(page.getByText('Chuyển đổi thành công!')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Tải LaTeX Source (.zip)' })).toBeVisible()

  const doiTaiZip = page.waitForRequest('**/api/download/job-e2e-001')
  await page.getByRole('button', { name: 'Tải LaTeX Source (.zip)' }).click()
  await doiTaiZip

  const doiBienDichPdf = page.waitForRequest('**/api/compile-pdf/job-e2e-001')
  await page.getByRole('button', { name: 'Biên dịch PDF' }).click()
  await doiBienDichPdf
  await expect(page.getByRole('button', { name: 'Tải PDF (2 trang)' })).toBeVisible()

  const doiTaiPdf = page.waitForRequest('**/api/tai-ve-pdf/job-e2e-001')
  await page.getByRole('button', { name: 'Tải PDF (2 trang)' }).click()
  await doiTaiPdf
})
