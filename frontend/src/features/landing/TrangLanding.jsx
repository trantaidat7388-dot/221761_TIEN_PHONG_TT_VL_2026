import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import * as LucideIcons from 'lucide-react'
import { motion } from 'framer-motion'
import { dungXacThuc } from '../../context/AuthContext'
import { layNoiDungLandingPublic } from '../../services/api'

const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: { opacity: 1, y: 0 } }
const stagger = { visible: { transition: { staggerChildren: 0.08 } } }

const DynamicIcon = ({ name, className }) => {
  const IconComponent = LucideIcons[name] || LucideIcons.Circle
  return <IconComponent className={className} />
}

const TrangLanding = () => {
  const { nguoiDung } = dungXacThuc()
  const [faqMo, setFaqMo] = useState(0)
  const [landingData, setLandingData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const fetchLanding = async () => {
    setLoading(true)
    setError(false)
    try {
      const res = await layNoiDungLandingPublic()
      if (res.thanhCong && res.content) {
        setLandingData(res.content)
      } else {
        setError(true)
      }
    } catch (err) {
      console.error('Lỗi tải Landing:', err)
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLanding()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <LucideIcons.Loader2 className="w-10 h-10 text-primary-500 animate-spin" />
          <p className="text-white/40 text-sm animate-pulse font-medium">Đang tải tài nguyên...</p>
        </div>
      </div>
    )
  }

  if (error || !landingData) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
        <div className="relative mb-8">
          <div className="absolute inset-0 bg-primary-500/20 blur-[60px] rounded-full" />
          <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-slate-900 border border-white/10 shadow-2xl">
            <LucideIcons.Unplug className="h-10 w-10 text-primary-400" />
          </div>
        </div>
        
        <h2 className="text-2xl font-bold text-white mb-3">Hệ thống đang bận khởi động</h2>
        <p className="text-white/50 mb-8 max-w-md leading-relaxed">
          Chúng tôi đang chuẩn bị dữ liệu cho phiên làm việc mới. Quá trình này có thể mất vài giây nếu máy chủ vừa được khởi chạy.
        </p>
        
        <button 
          onClick={fetchLanding}
          className="btn-primary inline-flex items-center gap-2.5 px-8 py-3 rounded-xl shadow-lg shadow-primary-500/20 hover:scale-105 active:scale-95 transition-all"
        >
          <LucideIcons.RefreshCw className="w-4.5 h-4.5" /> Thử lại ngay
        </button>
        
        <p className="mt-6 text-xs text-white/20 font-mono">Status: ECONNREFUSED_OR_ASYNC_BOOT</p>
      </div>
    )
  }

  const ctaPath = nguoiDung ? '/chuyen-doi' : '/dang-nhap'
  const ctaLabel = nguoiDung ? 'Vào hệ thống' : (landingData.hero?.cta_primary || 'Bắt đầu miễn phí')
  const sectionOrder = landingData.section_order || ['hero', 'tinh_nang', 'buoc_su_dung', 'mau_template', 'goi_premium', 'thanh_toan', 'so_sanh', 'faq', 'cta_bottom']

  const renderSection = (secId) => {
    switch (secId) {
      case 'hero':
        const hero = landingData.hero || {}
        return (
          <section key="hero" className="mx-auto max-w-7xl px-4 pb-20 pt-20 sm:px-8 sm:pt-28 lg:pt-36">
            <div className="grid gap-14 lg:grid-cols-[1.1fr,0.9fr] lg:items-center">
              <div>
                <motion.div initial="hidden" animate="visible" variants={fadeUp} transition={{ duration: 0.6 }}>
                  <span className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary-400/30 bg-primary-500/10 px-3.5 py-1.5 text-xs font-semibold text-primary-300">
                    <LucideIcons.Sparkles className="h-3.5 w-3.5" /> {hero.badge}
                  </span>
                </motion.div>
                <motion.h1 initial="hidden" animate="visible" variants={fadeUp} transition={{ duration: 0.6, delay: 0.1 }} className="mt-5 font-heading text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl lg:text-[3.5rem]">
                  {hero.title}{' '}
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-300 via-primary-400 to-purple-400">
                    {hero.title_highlight}
                  </span>
                </motion.h1>
                <motion.p initial="hidden" animate="visible" variants={fadeUp} transition={{ duration: 0.6, delay: 0.2 }} className="mt-6 max-w-xl text-lg leading-relaxed text-white/60">
                  {hero.description}
                </motion.p>
                <motion.div initial="hidden" animate="visible" variants={fadeUp} transition={{ duration: 0.6, delay: 0.3 }} className="mt-8 flex flex-wrap gap-3">
                  <Link to={ctaPath} className="btn-primary inline-flex items-center gap-2">
                    {ctaLabel} <LucideIcons.ArrowRight className="h-4 w-4" />
                  </Link>
                  {hero.cta_secondary && (
                    <a href="/word2latex-app.apk" download="word2latex-app.apk" className="btn-glass inline-flex items-center gap-2 border-primary-500/30 bg-primary-500/10 hover:bg-primary-500/20">
                      <LucideIcons.Download className="h-4 w-4" /> {hero.cta_secondary}
                    </a>
                  )}
                  <a href="#tinh-nang" className="btn-glass inline-flex items-center gap-2">
                    Khám phá <LucideIcons.ChevronDown className="h-4 w-4" />
                  </a>
                </motion.div>
                <motion.div initial="hidden" animate="visible" variants={fadeUp} transition={{ duration: 0.6, delay: 0.4 }} className="mt-12 grid grid-cols-4 gap-5 border-t border-white/10 pt-7">
                  {hero.stats && hero.stats.map((s, i) => (
                    <div key={i}>
                      <p className="text-2xl font-extrabold text-primary-300">{s.val}</p>
                      <p className="text-xs text-white/40 mt-0.5">{s.sub}</p>
                    </div>
                  ))}
                </motion.div>
              </div>
              <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.3 }} className="glass-card p-6 shadow-2xl">
                <div className="mb-4 flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-red-400/80" />
                  <div className="h-3 w-3 rounded-full bg-amber-400/80" />
                  <div className="h-3 w-3 rounded-full bg-emerald-400/80" />
                  <span className="ml-2 text-xs text-white/30 font-mono">output.tex</span>
                </div>
                <div className="space-y-1.5 font-mono text-[13px] leading-relaxed text-white/70">
                  <p><span className="text-primary-400">\documentclass</span>[conference]{'{IEEEtran}'}</p>
                  <p><span className="text-purple-400">\usepackage</span>{'{amsmath, graphicx}'}</p>
                  <p><span className="text-primary-400">\title</span>{'{Chuyển đổi tự động Word sang LaTeX}'}</p>
                  <p><span className="text-emerald-400">\author</span>{'{Nguyễn Văn A}'}</p>
                  <p className="text-white/30">%</p>
                  <p><span className="text-amber-400">\begin</span>{'{document}'}</p>
                  <p className="pl-4"><span className="text-primary-400">\maketitle</span></p>
                  <p className="pl-4"><span className="text-primary-400">\section</span>{'{Giới thiệu}'}</p>
                  <p className="pl-4 text-white/40">Hệ thống Word2LaTeX cho phép...</p>
                  <p><span className="text-amber-400">\end</span>{'{document}'}</p>
                </div>
                <div className="mt-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 px-3 py-2 text-center text-xs font-semibold text-emerald-300">
                  <LucideIcons.CheckCircle2 className="inline h-3.5 w-3.5 mr-1.5" /> Biên dịch thành công — 0 lỗi
                </div>
              </motion.div>
            </div>
          </section>
        )

      case 'tinh_nang':
        return (
          <section key="tinh_nang" id="tinh-nang" className="py-24 border-t border-white/5">
            <div className="mx-auto max-w-7xl px-4 sm:px-8">
              <SectionHeader badge="Tính năng" title="Mọi thứ bạn cần" desc="Hệ thống tích hợp đầy đủ để chuyển đổi tài liệu học thuật một cách chuyên nghiệp." />
              <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {landingData.tinh_nang?.map((f, i) => (
                  <motion.div key={i} variants={fadeUp} transition={{ duration: 0.4 }} className="glass-card-hover p-6 group">
                    <div className="mb-4 inline-flex rounded-xl bg-primary-500/15 p-2.5 text-primary-400 group-hover:bg-primary-500/25 transition">
                      <DynamicIcon name={f.icon} className="h-5 w-5" />
                    </div>
                    <h3 className="mb-2 text-sm font-bold text-white">{f.title}</h3>
                    <p className="text-sm leading-relaxed text-white/50">{f.desc}</p>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          </section>
        )

      case 'buoc_su_dung':
        return (
          <section key="buoc_su_dung" className="py-24 border-t border-white/5">
            <div className="mx-auto max-w-7xl px-4 sm:px-8">
              <SectionHeader badge="Hướng dẫn" title="3 bước đơn giản" desc="Từ file Word đến LaTeX chuẩn xuất bản chỉ trong vài phút." />
              <div className="mt-14 grid gap-10 md:grid-cols-3">
                {landingData.buoc_su_dung?.map((b, i) => (
                  <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} transition={{ duration: 0.5, delay: i * 0.12 }} className="relative text-center">
                    <div className="relative mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl glass-card shadow-lg">
                      <DynamicIcon name={b.icon} className="h-7 w-7 text-primary-300" />
                      <div className="absolute -top-2.5 -right-2.5 flex h-7 w-7 items-center justify-center rounded-full bg-primary-600 text-xs font-bold text-white shadow-lg shadow-primary-500/30">{b.step}</div>
                    </div>
                    <h3 className="mb-2 text-base font-bold">{b.title}</h3>
                    <p className="text-sm text-white/50">{b.desc}</p>
                    {i < (landingData.buoc_su_dung?.length - 1 || 2) && (
                      <div className="absolute right-0 top-8 hidden md:flex items-center justify-center">
                        <LucideIcons.ChevronRight className="h-5 w-5 text-white/10" />
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          </section>
        )

      case 'mau_template':
        return (
          <section key="mau_template" className="py-24 border-t border-white/5">
            <div className="mx-auto max-w-7xl px-4 sm:px-8">
              <SectionHeader badge="Template" title="6+ mẫu LaTeX có sẵn" desc="Hỗ trợ các nhà xuất bản phổ biến nhất. Người dùng cũng có thể tự tải mẫu lên." />
              <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mt-14 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {landingData.mau_template?.map((t, i) => (
                  <motion.div key={i} variants={fadeUp} transition={{ duration: 0.4 }} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-4 hover:bg-white/[0.08] hover:border-primary-500/30 transition-all group">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-500/10 text-primary-400 group-hover:bg-primary-500/20 transition">
                        <LucideIcons.FileText className="h-4.5 w-4.5" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-semibold text-sm text-white truncate">{t.name}</p>
                        <p className="text-xs text-white/40 font-mono">{t.cls}</p>
                      </div>
                    </div>
                    <LucideIcons.ArrowUpRight className="h-4 w-4 text-white/20 group-hover:text-primary-400 transition shrink-0" />
                  </motion.div>
                ))}
              </motion.div>
            </div>
          </section>
        )

      case 'goi_premium':
        return (
          <section key="goi_premium" className="py-24 border-t border-white/5">
            <div className="mx-auto max-w-7xl px-4 sm:px-8">
              <SectionHeader badge="Premium" title="Nâng cấp tài khoản" desc="Chọn gói phù hợp để mở khóa toàn bộ tính năng chuyển đổi." />
              <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={stagger} className="mt-14 grid gap-6 md:grid-cols-3 lg:gap-8">
                {landingData.goi_premium?.map((g, i) => {
                  const isPopular = !!g.badge
                  return (
                    <motion.div key={i} variants={fadeUp} transition={{ duration: 0.5 }} className={`relative rounded-2xl p-6 transition-all ${isPopular ? 'border-2 border-primary-500/40 bg-primary-500/[0.08] shadow-xl shadow-primary-500/10 md:-translate-y-2' : 'border border-white/10 bg-white/[0.03] hover:border-white/20'}`}>
                      {g.badge && (
                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-primary-600 to-primary-500 px-3 py-1 text-xs font-bold text-white shadow-lg shadow-primary-500/25">
                          <LucideIcons.Star className="mr-1 inline h-3 w-3" /> {g.badge}
                        </div>
                      )}
                      <p className="text-xs font-semibold text-white/40 uppercase tracking-wider">{g.name}</p>
                      <div className="my-4">
                        <span className="text-3xl font-extrabold">{g.price}</span>
                        <span className="text-base text-white/30 ml-1">VND</span>
                      </div>
                      <p className="text-sm text-white/50 mb-5">{g.days} ngày sử dụng Premium</p>
                      <ul className="space-y-2.5 text-sm text-white/60 mb-6">
                        <li className="flex items-center gap-2"><LucideIcons.CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" /> Không giới hạn chuyển đổi</li>
                        <li className="flex items-center gap-2"><LucideIcons.CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" /> Hỗ trợ công thức phức tạp</li>
                        <li className="flex items-center gap-2"><LucideIcons.CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" /> Ưu tiên hàng đợi xử lý</li>
                      </ul>
                      <Link to={nguoiDung ? '/premium' : '/dang-nhap'} className={`block rounded-xl py-2.5 text-center text-sm font-bold transition ${isPopular ? 'btn-primary !w-full' : 'border border-white/15 bg-white/5 text-white/80 hover:bg-white/10'}`}>Chọn gói này</Link>
                    </motion.div>
                  )
                })}
              </motion.div>
            </div>
          </section>
        )

      case 'thanh_toan':
        return (
          <section key="thanh_toan" className="py-24 border-t border-white/5">
            <div className="mx-auto max-w-7xl px-4 sm:px-8">
              <SectionHeader badge="Thanh toán" title="Thanh toán đơn giản" desc="Thanh toán nhanh, minh bạch và an toàn cho tài khoản của bạn." />
              <div className="mt-14 grid gap-6 lg:grid-cols-2">
                <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} transition={{ duration: 0.6 }} className="glass-card p-6">
                  <h3 className="mb-5 font-bold flex items-center gap-2"><LucideIcons.Workflow className="h-5 w-5 text-primary-400" /> Quy trình người dùng</h3>
                  <div className="space-y-3">
                    {[
                      { n: '1', t: 'Chọn gói phù hợp với nhu cầu' },
                      { n: '2', t: 'Thanh toán qua kênh được hỗ trợ' },
                      { n: '3', t: 'Tài khoản được kích hoạt nhanh chóng' },
                    ].map((step, idx) => (
                      <div key={idx} className="flex items-start gap-3">
                        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary-500/15 text-xs font-bold text-primary-300">{step.n}</div>
                        <p className="text-sm text-white/70 leading-relaxed">{step.t}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
                <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} transition={{ duration: 0.6, delay: 0.1 }} className="glass-card p-6">
                  <h3 className="mb-5 font-bold flex items-center gap-2"><LucideIcons.ShieldCheck className="h-5 w-5 text-primary-400" /> Vì sao dễ sử dụng</h3>
                  <div className="mt-1 space-y-2.5">
                    <div className="flex items-center gap-2.5 text-sm"><LucideIcons.CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" /><span className="text-white/60">Giao diện đơn giản, thao tác nhanh</span></div>
                    <div className="flex items-center gap-2.5 text-sm"><LucideIcons.Timer className="h-4 w-4 shrink-0 text-amber-400" /><span className="text-white/60">Xác nhận nhanh và rõ ràng</span></div>
                    <div className="flex items-center gap-2.5 text-sm"><LucideIcons.Globe className="h-4 w-4 shrink-0 text-primary-400" /><span className="text-white/60">Hỗ trợ nhiều kênh thanh toán</span></div>
                    <div className="flex items-center gap-2.5 text-sm"><LucideIcons.CreditCard className="h-4 w-4 shrink-0 text-cyan-400" /><span className="text-white/60">Lịch sử giao dịch lưu trữ đầy đủ</span></div>
                  </div>
                </motion.div>
              </div>
            </div>
          </section>
        )

      case 'so_sanh':
        const so_sanh = landingData.so_sanh || {}
        return (
          <section key="so_sanh" className="py-24 border-t border-white/5">
            <div className="mx-auto max-w-7xl px-4 sm:px-8">
              <SectionHeader badge="So sánh" title="Từ thao tác thủ công đến tự động" desc="Một góc nhìn trực quan về khác biệt trước và sau khi dùng Word2LaTeX." />
              <div className="mt-14 grid gap-6 lg:grid-cols-2">
                <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} className="rounded-2xl border border-rose-400/20 bg-rose-500/5 p-6">
                  <p className="text-xs font-semibold uppercase tracking-wider text-rose-300">Trước khi dùng</p>
                  <h3 className="mt-2 font-heading text-2xl font-bold text-white">{so_sanh.truoc?.title}</h3>
                  <ul className="mt-4 space-y-3 text-sm text-white/70">
                    {so_sanh.truoc?.items?.map((item, id) => (
                      <li key={id} className="flex items-start gap-2"><span className="mt-1 h-1.5 w-1.5 rounded-full bg-rose-300 shrink-0" /> {item}</li>
                    ))}
                  </ul>
                </motion.div>
                <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} transition={{ delay: 0.1 }} className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 p-6">
                  <p className="text-xs font-semibold uppercase tracking-wider text-emerald-300">Sau khi dùng</p>
                  <h3 className="mt-2 font-heading text-2xl font-bold text-white">{so_sanh.sau?.title}</h3>
                  <ul className="mt-4 space-y-3 text-sm text-white/80">
                    {so_sanh.sau?.items?.map((item, id) => (
                      <li key={id} className="flex items-start gap-2"><LucideIcons.CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" /> {item}</li>
                    ))}
                  </ul>
                </motion.div>
              </div>
            </div>
          </section>
        )

      case 'faq':
        return (
          <section key="faq" className="py-20 border-t border-white/5">
            <div className="mx-auto max-w-4xl px-4 sm:px-8">
              <SectionHeader badge="FAQ" title="Câu hỏi thường gặp" desc="Những câu hỏi phổ biến nhất từ người dùng của chúng tôi." />
              <div className="mt-10 space-y-3">
                {landingData.faq?.map((item, idx) => {
                  const isOpen = faqMo === idx
                  return (
                    <button key={idx} onClick={() => setFaqMo(isOpen ? -1 : idx)} className="w-full rounded-xl border border-white/10 bg-white/[0.03] p-4 text-left transition hover:border-cyan-400/30">
                      <div className="flex items-center justify-between gap-4">
                        <span className="inline-flex items-center gap-2 font-semibold text-white"><LucideIcons.HelpCircle className="h-4 w-4 text-cyan-300" /> {item.q}</span>
                        <LucideIcons.ChevronDown className={`h-4 w-4 shrink-0 text-white/50 transition ${isOpen ? 'rotate-180' : ''}`} />
                      </div>
                      {isOpen && <p className="mt-3 text-sm leading-relaxed text-white/65">{item.a}</p>}
                    </button>
                  )
                })}
              </div>
            </div>
          </section>
        )

      case 'cta_bottom':
        const cta = landingData.cta_bottom || {}
        return (
          <section key="cta_bottom" className="py-20 border-t border-white/5">
            <div className="mx-auto max-w-3xl px-4 text-center sm:px-8">
              <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} transition={{ duration: 0.6 }}>
                <h2 className="text-3xl font-extrabold sm:text-4xl">{cta.title}</h2>
                <p className="mt-4 text-white/50 text-lg">{cta.description}</p>
                <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
                  <Link to={ctaPath} className="btn-primary inline-flex items-center gap-2 !text-base">
                    {ctaLabel} <LucideIcons.ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </motion.div>
            </div>
          </section>
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-animated text-white overflow-x-hidden">
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute -top-40 left-1/2 h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-primary-600/20 blur-[140px]" />
        <div className="absolute bottom-0 right-0 h-[400px] w-[400px] rounded-full bg-primary-800/15 blur-[120px]" />
        <div className="absolute left-0 top-1/2 h-[350px] w-[350px] rounded-full bg-purple-700/10 blur-[120px]" />
      </div>

      <div className="relative z-10">
        {/* HEADER */}
        <header className="sticky top-0 z-50 border-b border-white/5 bg-slate-950/70 backdrop-blur-xl">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-8">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 shadow-lg shadow-primary-500/20">
                <LucideIcons.FileText className="h-4.5 w-4.5 text-white" />
              </div>
              <span className="text-lg font-bold tracking-tight group-hover:text-primary-300 transition-colors">Word2LaTeX</span>
            </Link>
            <nav className="flex items-center gap-3">
              <Link to={ctaPath} className="btn-primary !py-2 !px-4 !text-sm !rounded-lg inline-flex items-center gap-1.5">
                {nguoiDung ? 'Dashboard' : 'Đăng nhập'} <LucideIcons.ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </nav>
          </div>
        </header>

        {sectionOrder.map(secId => renderSection(secId))}

        {/* FOOTER */}
        <footer className="border-t border-white/5 py-8">
          <div className="mx-auto max-w-7xl px-4 sm:px-8">
            <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 text-[10px] font-bold">
                  <LucideIcons.FileText className="h-3.5 w-3.5" />
                </div>
                <span className="text-sm font-semibold">Word2LaTeX</span>
              </div>
              <div className="flex flex-wrap gap-5 text-sm text-white/40">
                <Link to="/dang-nhap" className="hover:text-white/80 transition">Đăng nhập</Link>
                <Link to="/premium" className="hover:text-white/80 transition">Premium</Link>
              </div>
              <p className="text-xs text-white/25">© 2026 Word2LaTeX — Nền tảng thương mại</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}

const SectionHeader = ({ badge, title, desc }) => (
  <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeUp} transition={{ duration: 0.5 }} className="text-center">
    <span className="mb-3 inline-block rounded-full bg-primary-500/10 border border-primary-500/20 px-3 py-1 text-xs font-semibold text-primary-300">{badge}</span>
    <h2 className="font-heading text-3xl font-extrabold sm:text-4xl">{title}</h2>
    <p className="mx-auto mt-3 max-w-2xl text-white/50">{desc}</p>
  </motion.div>
)

export default TrangLanding
