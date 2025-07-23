"use client"

import type React from "react"
import { useState } from "react"
import { ShoppingBag, Ruler, Camera, Zap, Shield, Eye, EyeOff } from "lucide-react"
import { useRouter } from "next/navigation"

// Base URL for backend API
const API_BASE_URL = "https://shoeshopper.onrender.com" // [Walkthrough] Base URL for backend API

export default function LandingPage() {
  const router = useRouter() // Next.js router for navigation
  const [showLogin, setShowLogin] = useState(false) // Controls visibility of Login modal
  const [showSignup, setShowSignup] = useState(false) // Controls visibility of Signup modal
  const [showPassword, setShowPassword] = useState(false) // Toggles password field visibility
  const [showConfirmPassword, setShowConfirmPassword] = useState(false) // Toggles confirm password field visibility
  
  const [loginForm, setLoginForm] = useState({
    username: "",
    password: "",
  })

  const [signupForm, setSignupForm] = useState({
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    confirm_password: "",
  })

// Get CSRF token
const getCSRFToken = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/csrf_cookie/`, {
      credentials: "include",
    })
    if (!response.ok) {
      throw new Error("Failed to get CSRF token")
    }
  } catch (error) {
    console.error("Error getting CSRF token:", error)
  }
}

// Handle login form submission
const handleLoginSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  try {
    await getCSRFToken()

    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify(loginForm),
    })

    if (!response.ok) {
      throw new Error("Login failed")
    }

    setShowLogin(false)
    router.push("/dashboard")
  } catch (error) {
    console.error("Error logging in:", error)
  }
}

// Handle signup form submission
const handleSignupSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  try {
    await getCSRFToken()

    const response = await fetch(`${API_BASE_URL}/auth/signup/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify(signupForm),
    })

    if (!response.ok) {
      throw new Error("Signup failed")
    }

    setShowSignup(false)
    router.push("/dashboard")
  } catch (error) {
    console.error("Error signing up:", error)
  }
}

// UI render --------------------------------------------------------
return (
  <main className="flex min-h-screen flex-col items-center justify-center gap-16 p-8 md:p-24">
    {/* Hero Section */}
    <section className="flex flex-col items-center text-center gap-6 max-w-2xl">
      <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl">
        Find Shoes That <span className="text-primary">Actually Fit</span>
      </h1>
      <p className="text-lg text-muted-foreground">
        Upload a top-down photo of your foot on a piece of paper – we’ll handle the sizing and suggest shoes that fit like a glove.
      </p>
      <div className="flex gap-4">
        <button className="btn btn-primary" onClick={() => setShowSignup(true)}>
          Get Started
        </button>
        <button className="btn btn-outline" onClick={() => setShowLogin(true)}>
          Log In
        </button>
      </div>
    </section>

    {/* Feature Grid */}
    <section className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 max-w-4xl">
      <Feature icon={<Camera />} title="Photo Upload" description="Simple foot capture with your phone’s camera." />
      <Feature icon={<Ruler />} title="Accurate Sizing" description="ML-driven measurement down to the millimeter." />
      <Feature icon={<ShoppingBag />} title="Smart Recommendations" description="Find shoes from top brands that truly fit." />
      <Feature icon={<Shield />} title="Privacy First" description="Your photos never leave our secure servers." />
      <Feature icon={<Zap />} title="Fast Results" description="Get recommendations in under 10 seconds." />
    </section>

    {/* Login Modal */}
    {showLogin && (
      <Modal onClose={() => setShowLogin(false)} title="Log In">
        {/* Login Form */}
        <form className="space-y-4" onSubmit={handleLoginSubmit}>
          {/* Username */}
          <input
            type="text"
            placeholder="Username"
            className="input input-bordered w-full"
            value={loginForm.username}
            onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
            required
          />
          {/* Password */}
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              className="input input-bordered w-full pr-10"
              value={loginForm.password}
              onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
              required
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          </div>
          {/* Submit */}
          <button type="submit" className="btn btn-primary w-full">
            Log In
          </button>
        </form>
      </Modal>
    )}

    {/* Signup Modal */}
    {showSignup && (
      <Modal onClose={() => setShowSignup(false)} title="Sign Up">
        {/* Signup Form */}
        <form className="space-y-4" onSubmit={handleSignupSubmit}>
          <input
            type="text"
            placeholder="Username"
            className="input input-bordered w-full"
            value={signupForm.username}
            onChange={(e) => setSignupForm({ ...signupForm, username: e.target.value })}
            required
          />
          <input
            type="email"
            placeholder="Email"
            className="input input-bordered w-full"
            value={signupForm.email}
            onChange={(e) => setSignupForm({ ...signupForm, email: e.target.value })}
            required
          />
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="First Name"
              className="input input-bordered w-full"
              value={signupForm.first_name}
              onChange={(e) => setSignupForm({ ...signupForm, first_name: e.target.value })}
            />
            <input
              type="text"
              placeholder="Last Name"
              className="input input-bordered w-full"
              value={signupForm.last_name}
              onChange={(e) => setSignupForm({ ...signupForm, last_name: e.target.value })}
            />
          </div>
          <div className="flex gap-4">
            <div className="relative w-full">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Password"
                className="input input-bordered w-full pr-10"
                value={signupForm.password}
                onChange={(e) => setSignupForm({ ...signupForm, password: e.target.value })}
                required
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            <div className="relative w-full">
              <input
                type={showConfirmPassword ? "text" : "password"}
                placeholder="Confirm Password"
                className="input input-bordered w-full pr-10"
                value={signupForm.confirm_password}
                onChange={(e) => setSignupForm({ ...signupForm, confirm_password: e.target.value })}
                required
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>
          <button type="submit" className="btn btn-primary w-full">
            Sign Up
          </button>
        </form>
      </Modal>
    )}
  </main>
)
}

// -----------------------------------------------------------------------------
// Feature card component
function Feature({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="flex flex-col items-center gap-2 text-center p-4 border rounded-lg shadow-sm">
      <div className="p-2 bg-primary/10 rounded-full">{icon}</div>
      <h3 className="font-semibold">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  )
}

// Generic modal wrapper
function Modal({ onClose, title, children }: { onClose: () => void; title: string; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-zinc-900 p-6 rounded-lg w-full max-w-md shadow-lg relative">
        <button className="absolute top-3 right-3" onClick={onClose}>
          ✕
        </button>
        <h2 className="text-xl font-semibold mb-4">{title}</h2>
        {children}
      </div>
    </div>
  )
}
