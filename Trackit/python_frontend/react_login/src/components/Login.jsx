import React, { useState } from 'react'

function IconEmail(){
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6.75C3 5.23122 4.23122 4 5.75 4h12.5C19.7688 4 21 5.23122 21 6.75v10.5C21 18.7688 19.7688 20 18.25 20H5.75C4.23122 20 3 18.7688 3 17.25V6.75z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/><path d="M21 6.75L12 12.5 3 6.75" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/></svg>
  )
}

function IconLock(){
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="11" width="18" height="10" rx="2" stroke="currentColor" strokeWidth="1.2"/><path d="M7 11V8a5 5 0 0110 0v3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/></svg>
  )
}

function IconEye({open}){
  return (
    open ? (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" stroke="currentColor" strokeWidth="1.2"/><circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.2"/></svg>
    ):(
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 3l18 18" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/><path d="M10.3 10.3A3 3 0 0113.7 13.7" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/><path d="M2 12s4-7 10-7c2.2 0 4.2.6 6 1.6" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>
    )
  )
}

export default function Login(){
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [remember, setRemember] = useState(false)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState({})
  const [dark, setDark] = useState(false)

  function validate(){
    const e = {}
    if(!email) e.email = 'Email is required'
    else if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = 'Enter a valid email'
    if(!password) e.password = 'Password is required'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  async function onSubmit(ev){
    ev.preventDefault()
    if(!validate()) return
    setLoading(true)
    setErrors({})
    // mock auth delay
    await new Promise(r=>setTimeout(r, 1100))
    setLoading(false)
    // in a real app: call API, handle response
    alert('Logged in (mock) — ' + email)
  }

  React.useEffect(()=>{
    if(dark) document.documentElement.classList.add('dark')
    else document.documentElement.classList.remove('dark')
  },[dark])

  return (
    <div className="relative w-full max-w-md p-6 sm:p-10">
      {/* background decorative blobs (subtle) */}
      <div aria-hidden className="absolute -inset-6 rounded-3xl bg-gradient-to-tr from-pink-50 via-white to-purple-50 opacity-40 blur-3xl transform -translate-y-4"></div>

      <div className="relative backdrop-blur-md bg-white/60 dark:bg-slate-900/60 rounded-2xl p-6 sm:p-8 shadow-2xl border border-white/20">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-brand2 to-accent flex items-center justify-center text-white font-bold">TI</div>
            <div>
              <div className="text-lg font-semibold">TrackIt</div>
              <div className="text-xs text-gray-500">Welcome back — sign in</div>
            </div>
          </div>
          <button onClick={()=>setDark(!dark)} className="text-sm px-2 py-1 bg-white/30 dark:bg-white/10 rounded">{dark ? 'Light' : 'Dark'}</button>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <label className="block">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-700">Email</div>
            <div className="mt-2 relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><IconEmail /></span>
              <input value={email} onChange={e=>setEmail(e.target.value)} className="w-full pl-10 pr-3 py-3 rounded-xl border border-transparent focus:outline-none focus:ring-2 focus:ring-pink-300 transition" placeholder="you@company.com" />
            </div>
            {errors.email && <div className="text-xs text-red-500 mt-1">{errors.email}</div>}
          </label>

          <label className="block">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-700">Password</div>
            <div className="mt-2 relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"><IconLock/></span>
              <input value={password} onChange={e=>setPassword(e.target.value)} type={show? 'text' : 'password'} className="w-full pl-10 pr-10 py-3 rounded-xl border border-transparent focus:outline-none focus:ring-2 focus:ring-pink-300 transition" placeholder="Enter your password" />
              <button type="button" onClick={()=>setShow(s=>!s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600"><IconEye open={show} /></button>
            </div>
            {errors.password && <div className="text-xs text-red-500 mt-1">{errors.password}</div>}
          </label>

          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={remember} onChange={e=>setRemember(e.target.checked)} className="w-4 h-4" />
              <span className="text-gray-600">Remember me</span>
            </label>
            <a href="#" className="text-sm text-indigo-600">Forgot password?</a>
          </div>

          <div>
            <button disabled={loading} type="submit" className="w-full inline-flex items-center justify-center gap-3 py-3 rounded-xl text-white bg-gradient-to-r from-brand2 to-accent hover:scale-[1.02] transition transform disabled:opacity-60">
              {loading ? (<svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg>) : null}
              <span>Sign in</span>
            </button>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-[1px] bg-white/30"></div>
            <div className="text-xs text-gray-500">or continue with</div>
            <div className="flex-1 h-[1px] bg-white/30"></div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button type="button" className="py-2 rounded-xl bg-white/80 hover:bg-white/90 flex items-center justify-center gap-2">
              <svg width="16" height="16" viewBox="0 0 533.5 544.3" className="inline-block"><path fill="#4285f4" d="M533.5 278.4c0-17.4-1.4-34.3-4-50.7H272v95.9h147.1c-6.4 34.7-25.6 64.1-54.6 83.8v69.6h88.1c51.6-47.6 81.9-117.7 81.9-198.6z"/></svg>
              Google
            </button>
            <button type="button" className="py-2 rounded-xl bg-slate-800 text-white flex items-center justify-center gap-2 hover:opacity-95">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56 0-.28-.01-1.02-.02-2-3.2.7-3.88-1.54-3.88-1.54-.52-1.33-1.28-1.68-1.28-1.68-1.05-.72.08-.71.08-.71 1.17.08 1.79 1.2 1.79 1.2 1.03 1.76 2.7 1.25 3.36.96.1-.75.4-1.25.72-1.54-2.55-.29-5.23-1.28-5.23-5.7 0-1.26.45-2.29 1.2-3.1-.12-.3-.52-1.52.11-3.17 0 0 .98-.31 3.2 1.19a11.1 11.1 0 0 1 5.82 0c2.22-1.5 3.2-1.19 3.2-1.19.63 1.65.23 2.87.11 3.17.75.81 1.2 1.84 1.2 3.1 0 4.43-2.69 5.41-5.25 5.69.41.36.77 1.08.77 2.18 0 1.58-.01 2.85-.01 3.24 0 .31.21.68.8.56C20.71 21.39 24 17.08 24 12c0-6.35-5.15-11.5-11.5-11.5z"/></svg>
              GitHub
            </button>
          </div>

          <div className="text-center text-sm text-gray-600">Don't have an account? <a href="#" className="text-indigo-600">Sign up</a></div>
        </form>
      </div>
    </div>
  )
}
