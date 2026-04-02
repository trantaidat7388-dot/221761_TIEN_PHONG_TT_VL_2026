# Implementation Board - Premium Token Google

Ngay tao: 2026-04-03
Trang thai: Ready for execution

## 1. Quy tac van hanh board

- Moi ticket bat buoc co: owner role, estimate, dependency, acceptance criteria, test cases.
- Khong mo phase moi neu phase truoc chua dat gate.
- Moi ticket phai cap nhat trang thai: TODO -> IN PROGRESS -> REVIEW -> DONE.
- Moi thay doi schema bat buoc co rollback test.

Trang thai:
- TODO
- IN PROGRESS
- REVIEW
- DONE
- BLOCKED

## 2. Phase roadmap

1. DB-001 den DB-003
2. BE-001 den BE-005
3. BE-006 den BE-008 + FE-001 den FE-003
4. BE-009 den BE-010 + FE-004
5. SEC-001 den REL-001

---

## Phase A - Data Foundation

### DB-001 - Extend users for premium/token/google
- Owner role: Backend Engineer
- Estimate: 3 SP
- Dependency: none
- Scope:
  - Add plan_type (free/premium)
  - Add token_balance (int, non-null, default)
  - Add premium_started_at, premium_expires_at
  - Add auth_provider (local/google)
  - Add google_id (nullable, unique)
- Acceptance criteria:
  - Migration up/down works on fresh DB and existing DB
  - Existing users keep login capability
  - No null violations for required new columns
- Test cases:
  - Migrate up on populated users table
  - Migrate down and verify old schema restored
  - Auth me still returns valid user
- Status: IN PROGRESS

### DB-002 - Create token_ledger table
- Owner role: Backend Engineer
- Estimate: 3 SP
- Dependency: DB-001
- Scope:
  - Create token_ledger(id, user_id, delta_token, balance_after, reason, job_id, meta_json, created_at)
  - Add FK user_id -> users.id
  - Add index (user_id, created_at desc), index reason
- Acceptance criteria:
  - Ledger insert/read works with FK integrity
  - Query by user returns correct order and pagination
- Test cases:
  - Insert deduct/refund/grant entries
  - Query by user with page 1, page 2
  - FK reject invalid user_id
- Status: IN PROGRESS

### DB-003 - Extend conversion_history for token/page/error
- Owner role: Backend Engineer
- Estimate: 2 SP
- Dependency: DB-001
- Scope:
  - Add pages_count, token_cost, token_refunded
  - Add error_type, error_message
  - Backfill defaults for existing records
- Acceptance criteria:
  - Old history records remain readable
  - New records can store full conversion economics
- Test cases:
  - History API returns old + new rows without crash
  - Insert with error metadata and refunded flag
- Status: IN PROGRESS

Phase A gate:
- [ ] DB-001 DONE
- [ ] DB-002 DONE
- [ ] DB-003 DONE
- [ ] Migration rollback rehearsed

---

## Phase B - Token Engine in Conversion

### BE-001 - Implement token calculation service
- Owner role: Backend Engineer
- Estimate: 2 SP
- Dependency: DB-001
- Scope:
  - Function to compute token by pages (pre-release policy)
  - Config-driven multiplier and minimum charge
- Acceptance criteria:
  - Deterministic output for all page boundaries
- Test cases:
  - pages: 0, 1, 5, 6, 10, 100
- Status: IN PROGRESS

### BE-002 - Atomic token deduction before conversion
- Owner role: Backend Engineer
- Estimate: 3 SP
- Dependency: BE-001, DB-002
- Scope:
  - Lock/check balance
  - Deduct token in transaction
  - Write ledger reason convert_deduct
- Acceptance criteria:
  - No negative balance under concurrency
- Test cases:
  - Concurrent convert requests on same user
  - Not enough token -> blocked with clear error
- Status: IN PROGRESS

### BE-003 - Refund token on system failure
- Owner role: Backend Engineer
- Estimate: 2 SP
- Dependency: BE-002, DB-003
- Scope:
  - Refund flow for conversion failure
  - Ledger reason refund
  - Mark history token_refunded=true
- Acceptance criteria:
  - Failed conversion restores expected balance
- Test cases:
  - Force conversion failure -> verify refund amount
- Status: IN PROGRESS

### BE-004 - Return token/page metadata in convert APIs
- Owner role: Backend Engineer
- Estimate: 2 SP
- Dependency: BE-002, DB-003
- Scope:
  - Add token_used, balance_after, pages_count to responses
  - Cover both convert and SSE endpoints
- Acceptance criteria:
  - Frontend receives consistent fields across both endpoints
- Test cases:
  - Compare response schema between endpoints
- Status: IN PROGRESS

### BE-005 - Ensure history write consistency
- Owner role: Backend Engineer
- Estimate: 2 SP
- Dependency: BE-003, BE-004
- Scope:
  - Write history with token/page/error data for all conversion paths
- Acceptance criteria:
  - No new history record missing token_cost/pages_count
- Test cases:
  - Successful conversion history
  - Failed conversion history
- Status: IN PROGRESS

Phase B gate:
- [ ] BE-001 DONE
- [ ] BE-002 DONE
- [ ] BE-003 DONE
- [ ] BE-004 DONE
- [ ] BE-005 DONE
- [ ] Concurrency test pass

---

## Phase C - Premium Admin + User Admin UI

### BE-006 - Extend account me with premium and token
- Owner role: Backend Engineer
- Estimate: 1 SP
- Dependency: DB-001
- Scope:
  - Return plan_type, token_balance, premium_expires_at
- Acceptance criteria:
  - Auth me returns complete account economics
- Test cases:
  - Free user and premium user payloads
- Status: IN PROGRESS

### BE-007 - Admin APIs for premium management
- Owner role: Backend Engineer
- Estimate: 3 SP
- Dependency: BE-006
- Scope:
  - Set premium expiry
  - Activate/deactivate premium
- Acceptance criteria:
  - Admin can modify premium state safely
- Test cases:
  - Promote to premium
  - Expire premium
- Status: IN PROGRESS

### BE-008 - Admin APIs for manual token operations
- Owner role: Backend Engineer
- Estimate: 2 SP
- Dependency: DB-002
- Scope:
  - Grant token
  - Deduct token
  - Ledger write for admin actions
- Acceptance criteria:
  - balance_after equals user token_balance after each operation
- Test cases:
  - grant + deduct + boundary zero
- Status: IN PROGRESS

### FE-001 - Admin user table upgrade
- Owner role: Frontend Engineer
- Estimate: 3 SP
- Dependency: BE-006
- Scope:
  - Add columns plan_type, token_balance, premium_expires_at
  - Add search/filter
- Acceptance criteria:
  - Admin can quickly find premium users and low-balance users
- Test cases:
  - Filter by plan, sort by token
- Status: IN PROGRESS

### FE-002 - Admin user detail page
- Owner role: Frontend Engineer
- Estimate: 3 SP
- Dependency: BE-007, BE-008
- Scope:
  - Show profile, conversion history per user, token ledger per user
- Acceptance criteria:
  - One-click drill-down from user list
- Test cases:
  - Open detail, paginate ledger/history
- Status: IN PROGRESS

### FE-003 - Admin action panel
- Owner role: Frontend Engineer
- Estimate: 2 SP
- Dependency: FE-002
- Scope:
  - UI forms for premium set and token grant/deduct
- Acceptance criteria:
  - Successful actions refresh data without full reload
- Test cases:
  - Action success, action failure, validation
- Status: IN PROGRESS

Phase C gate:
- [ ] BE-006 DONE
- [ ] BE-007 DONE
- [ ] BE-008 DONE
- [ ] FE-001 DONE
- [ ] FE-002 DONE
- [ ] FE-003 DONE

---

## Phase D - Google Auth

### BE-009 - Verify Google ID token in backend
- Owner role: Backend Engineer
- Estimate: 3 SP
- Dependency: DB-001
- Scope:
  - Verify id_token signature/audience/issuer/expiry
  - Map claims to user profile fields
- Acceptance criteria:
  - Invalid or forged token is rejected
- Test cases:
  - Expired, wrong aud, malformed token
- Status: IN PROGRESS

### BE-010 - Link or create user from Google identity
- Owner role: Backend Engineer
- Estimate: 2 SP
- Dependency: BE-009
- Scope:
  - Existing email linking policy
  - New user create with provider google
- Acceptance criteria:
  - No duplicate users for same identity
- Test cases:
  - Existing local email case
  - New email case
- Status: IN PROGRESS

### FE-004 - Google sign-in button and flow
- Owner role: Frontend Engineer
- Estimate: 2 SP
- Dependency: BE-009, BE-010
- Scope:
  - Add Google button in auth page
  - Exchange id_token with backend and store session
- Acceptance criteria:
  - Login/register with Google works end-to-end
- Test cases:
  - Google success path
  - Google cancel/error path
- Status: TODO

Phase D gate:
- [ ] BE-009 DONE
- [ ] BE-010 DONE
- [ ] FE-004 DONE

---

## Phase E - Security to Release

### SEC-001 - Rate limiting for auth/convert/admin
- Owner role: Backend Engineer
- Estimate: 2 SP
- Dependency: Phase B and D complete
- Acceptance criteria:
  - High-frequency abuse requests are throttled
- Status: IN PROGRESS

### SEC-002 - Audit logging for admin sensitive actions
- Owner role: Backend Engineer
- Estimate: 2 SP
- Dependency: BE-007, BE-008
- Acceptance criteria:
  - Every admin action has actor, target, timestamp, payload summary
- Status: IN PROGRESS

### OPS-001 - Metrics and monitoring
- Owner role: DevOps Engineer
- Estimate: 2 SP
- Dependency: Phase B complete
- Acceptance criteria:
  - Dashboard for token usage, conversion failure rate, premium counts
- Status: TODO

### QA-001 - Unit test package
- Owner role: QA + Backend Engineer
- Estimate: 2 SP
- Dependency: Phases B, C, D
- Acceptance criteria:
  - Critical modules covered by unit tests
- Status: TODO

### QA-002 - Integration test package
- Owner role: QA Engineer
- Estimate: 2 SP
- Dependency: Phases B, C
- Acceptance criteria:
  - ledger/balance consistency tests pass
- Status: TODO

### QA-003 - E2E test package
- Owner role: QA Engineer
- Estimate: 2 SP
- Dependency: FE-003, FE-004
- Acceptance criteria:
  - user/admin/google critical flows pass on staging
- Status: TODO

### REL-001 - Release and rollback runbook
- Owner role: Tech Lead + DevOps
- Estimate: 1 SP
- Dependency: SEC/OPS/QA tickets
- Acceptance criteria:
  - One-command deploy and one-command rollback documented and tested
- Status: IN PROGRESS

Phase E gate:
- [ ] SEC-001 DONE
- [ ] SEC-002 DONE
- [ ] OPS-001 DONE
- [ ] QA-001 DONE
- [ ] QA-002 DONE
- [ ] QA-003 DONE
- [ ] REL-001 DONE

---

## 3. Daily tracking section

| Date | Ticket | Progress note | Next step | Owner |
|---|---|---|---|---|
| 2026-04-03 | Setup | Board created from approved sequence | Assign owners and start DB-001 |  |
| 2026-04-03 | DB-001/002/003 | Da them schema users premium/token/google, tao token_ledger, mo rong conversion_history va chay verify cot bang | Chot rollback script + bo sung test migration |  |
| 2026-04-03 | BE-001..005 | Da them token_service, tru/hoan token trong ca convert thuong va SSE, bo sung token metadata vao response, ghi history that bai/thanh cong co token/page | Chay test concurrency + bo sung test tu dong cho refund path |  |
| 2026-04-03 | BE-006..008 + FE-001..003 | Da mo rong admin API quan ly premium/token, xem history va ledger theo user; da nang cap UI admin de thao tac premium/token va xem chi tiet tung tai khoan | Bo sung UI filter/search va test e2e cho admin action panel |  |
| 2026-04-03 | BE-009..010 + FE-004 | Da them API /api/auth/google va nut Google Sign-In frontend (GIS), ho tro link account theo email | Kiem thu voi GOOGLE_CLIENT_ID that va bo sung test regression auth |  |
| 2026-04-03 | SEC-001/002 + REL-001 | Da them rate limiting middleware theo nhom endpoint, them admin audit logs + endpoint xem log, va tao release runbook rollback | Bo sung test cho auth/convert rate limit va danh dau DONE khi qua review van hanh |  |
| 2026-04-03 | QA security | Da them test_rate_limit_auth.py va chay cung test_admin_token_audit.py, ket qua 2 passed | Bo sung them test rate-limit cho convert endpoint o buoc tiep theo |  |
| 2026-04-03 | REL-001 | Da them script backend/run_schema_migration.py va cap nhat runbook cach chay migration thu cong | Chot quy trinh backup/restore trong tai lieu van hanh cua team |  |
| 2026-04-03 | QA security + integration | Da them test_rate_limit_convert_admin.py va test_token_deduct_refund.py, chay bo test moi: 6 passed | Co the danh dau SEC-001 va QA-002 sang REVIEW |  |
| 2026-04-03 | Google setup docs | Da them tai lieu lay Google Client ID va cau hinh env | Team ops cap key that de test FE-004 tren staging |  |

## 4. Risk watchlist

- Risk: Migration impacts existing auth flow
  - Mitigation: backup + dry run + rollback rehearsal
- Risk: Token race condition under concurrent conversion
  - Mitigation: transaction and row lock
- Risk: Google linking creates duplicate accounts
  - Mitigation: strict identity mapping and linking policy

## 5. Ready-to-start now

- [ ] Assign owner for DB-001
- [ ] Assign owner for DB-002
- [ ] Assign owner for DB-003
- [ ] Lock sprint window for Phase A
