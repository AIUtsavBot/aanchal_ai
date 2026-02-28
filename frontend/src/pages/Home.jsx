import React from 'react'
import motherImg from '../assets/mother-child.jpeg'
import doctorImg from '../assets/doctor.png'
import doctoeImg2 from '../assets/doctor2.png'
import dashboardImg from '../assets/dashboard.png'
import dashboardImg2 from '../assets/dashboard2.png'
import mermaidImg from '../assets/mermaid.png'
import { HeartPulse, FileText, Users, AlertTriangle, Pill, MessageSquare, PlayCircle, Building2, ShieldCheck, Workflow, BrainCircuit } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

function SectionTitle({ title, subtitle }) {
  return (
    <div className="text-center mb-8">
      <h2 className="text-3xl font-bold text-slate-800">{title}</h2>
      {subtitle && <p className="mt-2 text-slate-500">{subtitle}</p>}
    </div>
  )
}

function CTAButton({ children, variant = 'primary', href = '#' }) {
  const base = 'inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all focus:outline-none focus:ring-2 focus:ring-offset-2'
  const styles = variant === 'primary'
    ? 'bg-teal-600 text-white hover:bg-teal-700 focus:ring-teal-600 shadow-lg shadow-teal-600/25'
    : 'bg-white text-teal-700 hover:bg-teal-50 border border-teal-200 focus:ring-teal-600'
  return <a href={href} className={`${base} ${styles}`}>{children}</a>
}

function FeatureCard({ icon: Icon, title, desc }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 hover:shadow-lg hover:shadow-teal-600/8 hover:-translate-y-1 transition-all duration-300">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-lg bg-teal-50 flex items-center justify-center">
          <Icon className="w-5 h-5 text-teal-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
      <p className="text-slate-500 text-sm leading-relaxed">{desc}</p>
    </div>
  )
}

function DemoCard({ id, src, caption }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200 hover:shadow-lg transition-all duration-300">
      <img id={id} src={src} alt={caption} className="w-full h-56 object-cover rounded-md" />
      <p className="text-sm text-gray-700 mt-3">{caption}</p>
    </div>
  )
}

function AudienceCard({ title, desc, icon: Icon, color }) {
  const colorMap = {
    'text-pink-600': 'text-pink-500',
    'text-green-600': 'text-emerald-500',
    'text-teal-600': 'text-teal-500'
  }
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
      <div className="flex items-center gap-3 mb-2">
        <Icon className={`w-6 h-6 ${colorMap[color] || 'text-teal-500'}`} />
        <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
      </div>
      <p className="text-slate-500 text-sm leading-relaxed">{desc}</p>
    </div>
  )
}

function StatCard({ value, label }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 text-center hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
      <div className="text-3xl font-bold text-teal-600">{value}</div>
      <div className="text-sm text-gray-700 mt-2">{label}</div>
    </div>
  )
}

export default function Home() {
  const { i18n } = useTranslation()
  return (
    <main className="bg-gradient-to-b from-teal-50 via-white to-pink-50">
      <section className="max-w-7xl mx-auto px-6 pt-16 pb-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-teal-50 text-teal-700 text-sm font-medium mb-4 border border-teal-100">
              <HeartPulse className="w-4 h-4" /> AI-Powered Maternal Health
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 leading-tight">AI-Powered 24/7 Maternal Health Monitoring for Mothers in Low-Resource Settings.</h1>
            <p className="mt-4 text-lg text-gray-700">Aanchal AI automates maternal risk assessment, report analysis, and care coordination using multi-agent AI and chat-first interfaces—no app required.</p>
            <div className="mt-6 flex flex-wrap gap-4">
              <CTAButton href="https://t.me/aanchal_ai_bot">Start a Chat on Telegram</CTAButton>
              <CTAButton variant="secondary" href="/auth/login"><PlayCircle className="w-5 h-5" /> View Dashboard</CTAButton>
            </div>
          </div>
          <div>
            <div className="bg-white rounded-2xl shadow-xl shadow-teal-600/10 p-4 border border-gray-200">
              <img id="hero-visual" src={motherImg} alt="Telegram bot + dashboard screenshot" className="w-full h-80 object-cover rounded-lg" />
            </div>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-12">
        <SectionTitle title="The Problem" />
        <div className="bg-white rounded-xl shadow-sm p-8 border border-gray-200">
          <p className="text-gray-800">Every two minutes, a woman dies from preventable pregnancy complications. Frontline ASHA workers lack tools, real-time insights, and automated coordination, leading to late referrals and avoidable emergencies.</p>
          <ul className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3 text-gray-700">
            <li className="flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-red-600" /> Fragmented medical records</li>
            <li className="flex items-center gap-2"><FileText className="w-4 h-4 text-yellow-600" /> Reports are unanalyzed PDFs</li>
            <li className="flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-teal-600" /> No proactive alerts</li>
            <li className="flex items-center gap-2"><Users className="w-4 h-4 text-green-600" /> High workload for ASHAs</li>
          </ul>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-12">
        <SectionTitle title="The Solution – Aanchal AI" />
        <div className="glass-card-no-hover p-8">
          <p className="text-slate-600">A multi-agent AI platform that detects maternal risk early, analyzes medical documents instantly, and coordinates care across Telegram, WhatsApp, and web dashboards.</p>
          <div className="mt-6">
            <img id="flow-diagram" src={mermaidImg} alt="System flow diagram" className="w-full max-w-4xl mx-auto rounded-lg object-contain" />
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 py-12">
        <SectionTitle title="Key Features" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <FeatureCard icon={HeartPulse} title="AI Risk Agent" desc="Automatically scores pregnancy risk using 12+ clinical parameters and flags high-risk cases for urgent follow-up by doctors." />
          <FeatureCard icon={FileText} title="Document Analyzer" desc="Upload medical reports (PDF/Images) for instant AI-powered extraction of vitals, insights, and risk indicators." />
          <FeatureCard icon={Users} title="ASHA Dashboard" desc="Manage assigned mothers, track follow-ups, record postnatal assessments, and monitor child growth — all in one place." />
          <FeatureCard icon={AlertTriangle} title="Emergency Agent" desc="Detects urgent symptoms like bleeding, seizures, or severe pain and triggers real-time escalation to nearby facilities." />
          <FeatureCard icon={Pill} title="Nutrition & Medication" desc="Personalized trimester-specific diet plans, anaemia management, and pregnancy-safe medication guidance." />
          <FeatureCard icon={MessageSquare} title="No-App Adoption" desc="Mothers chat naturally on Telegram in Hindi, Marathi, or English — with voice notes, document sharing, and multi-profile support." />
        </div>
      </section>

      <section id="demo" className="max-w-7xl mx-auto px-6 py-12">
        <SectionTitle title="Demo / Screenshots" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <DemoCard id="demo-telegram" src={dashboardImg} caption="Telegram bot flow" />
          <DemoCard id="demo-risk-dashboard" src={dashboardImg2} caption="Risk dashboard" />
          <DemoCard id="demo-report-summary" src={doctoeImg2} caption="AI-generated report summary" />
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 py-12">
        <SectionTitle title="Who It's For" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <AudienceCard icon={MessageSquare} color="text-pink-600" title="Mothers & Families" desc="Get health reminders, medication alerts, AI-powered report summaries, and 24/7 care guidance — right on Telegram." />
          <AudienceCard icon={Users} color="text-green-600" title="ASHA Workers" desc="Automated risk scoring, task management, and simplified workflows so no mother is missed during field visits." />
          <AudienceCard icon={Building2} color="text-teal-600" title="Clinics & Govt Programs" desc="Population-level monitoring, high-risk dashboards, and data-driven insights for maternal health policy." />
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-12">
        <SectionTitle title="Impact Metrics" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard value="40%" label="reduction in manual risk evaluation time" />
          <StatCard value="5x" label="faster report processing" />
          <StatCard value="Low-bandwidth" label="deployment in rural India" />
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-12">
        <SectionTitle title="Why Aanchal AI Wins (Competitive Advantage)" />
        <div className="bg-white rounded-xl shadow-sm p-8 border border-gray-200">
          <ul className="space-y-2 text-gray-800">
            <li className="flex items-center gap-2"><Workflow className="w-4 h-4 text-teal-600" /> Multi-agent orchestration</li>
            <li className="flex items-center gap-2"><BrainCircuit className="w-4 h-4 text-pink-600" /> Report intelligence powered by Gemini</li>
            <li className="flex items-center gap-2"><MessageSquare className="w-4 h-4 text-green-600" /> Chat-first UX lowers literacy barriers</li>
            <li className="flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-teal-600" /> Designed for Bharat-scale healthcare systems</li>
          </ul>
        </div>
      </section>

      <footer id="contact" className="bg-white/40 backdrop-blur-xl border-t border-teal-200/30">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex flex-col items-center text-center gap-4">
            <div className="flex items-center gap-2">
              <HeartPulse className="w-6 h-6 text-pink-500" />
              <span className="font-bold text-slate-700">Aanchal AI</span>
            </div>
            <div className="text-sm text-gray-700">
              <Link to="/" className="hover:underline hover:text-teal-600 transition-colors">Home</Link>
              <span className="mx-2">·</span>
              <Link to="/auth/login" className="hover:underline hover:text-teal-600 transition-colors">Login</Link>
              <span className="mx-2">·</span>
              <Link to="/auth/signup" className="hover:underline hover:text-teal-600 transition-colors">Signup</Link>
              <span className="mx-2">·</span>
              <a href="#privacy" className="hover:underline hover:text-teal-600 transition-colors">Privacy Policy</a>
              <span className="mx-2">·</span>
              <a href="#terms" className="hover:underline hover:text-teal-600 transition-colors">Terms</a>
            </div>
            <a href="https://t.me/aanchal_ai_bot" className="inline-flex items-center gap-2 px-5 py-2 bg-teal-600 text-white rounded-lg font-semibold hover:bg-teal-700 shadow-lg shadow-teal-600/25 transition-all">
              Start Chat on Telegram <span className="text-white/80">@aanchal_ai_bot</span>
            </a>
            <div className="text-xs text-gray-600">© {new Date().getFullYear()} Aanchal AI · React · FastAPI · Supabase · Gemini</div>
          </div>
        </div>
      </footer>
    </main>
  )
}
