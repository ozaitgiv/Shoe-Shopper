"use client"
import { useState, useEffect } from "react"
import {
  ShoppingBag,
  User,
  LogOut,
  ChevronDown,
  ArrowLeft,
  Trash2,
  AlertTriangle,
  Eye,
  EyeOff,
  Ruler,
  Calendar,
  UserCircle,
  Camera,
} from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"

// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface AppUser {
  id: number
  username: string
  email: string
}

interface MeasurementResult {
  id: number
  length_inches: number
  width_inches: number
  created_at: string
  status: "processing" | "complete" | "error"
}

export default function AccountPage() {
  const router = useRouter()
  const [user, setUser] = useState<AppUser | null>(null)
  const [showDropdown, setShowDropdown] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false)
  const [deleteConfirmationText, setDeleteConfirmationText] = useState("")
  const [isDeletingAccount, setIsDeletingAccount] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [deletePassword, setDeletePassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [latestMeasurement, setLatestMeasurement] = useState<MeasurementResult | null>(null)

  // Check authentication and get user info
  useEffect(() => {
    checkAuth()
  }, [])

  // Load measurements when user is authenticated
  useEffect(() => {
    if (user) {
      loadLatestMeasurement()
    }
  }, [user])

  const checkAuth = async () => {
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/")
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/user/`, {
        headers: {
          Authorization: `Token ${token}`,
        },
      })
      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        localStorage.removeItem("token")
        router.push("/")
      }
    } catch (error) {
      console.error("Auth check failed:", error)
      localStorage.removeItem("token")
      router.push("/")
    } finally {
      setIsLoading(false)
    }
  }

  const loadLatestMeasurement = async () => {
    // For now, we'll use mock data since we don't have a measurements endpoint
    // TODO: Implement backend endpoint GET /api/measurements/latest/

    // Mock data for demonstration
    const mockMeasurement: MeasurementResult = {
      id: 1,
      length_inches: 10.5,
      width_inches: 4.2,
      created_at: "2024-01-15T14:30:00Z",
      status: "complete",
    }

    setLatestMeasurement(mockMeasurement)
  }

  const handleLogout = async () => {
    const token = localStorage.getItem("token")

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/logout/`, {
        method: "POST",
        headers: {
          Authorization: `Token ${token}`,
        },
      })

      if (response.ok) {
        localStorage.removeItem("token")
        router.push("/")
      } else {
        console.error("Logout failed")
      }
    } catch (error) {
      console.error("Logout failed:", error)
    }
  }

  const handleDeleteAccount = async () => {
    if (!user) return

    // Validate confirmation text
    if (deleteConfirmationText !== user.username) {
      setError("Please type your username exactly as shown to confirm account deletion.")
      return
    }

    // Validate password
    if (!deletePassword.trim()) {
      setError("Please enter your password to confirm account deletion.")
      return
    }

    setIsDeletingAccount(true)
    setError(null)

    try {
      // For demo purposes, we'll just simulate account deletion
      // TODO: Implement backend endpoint DELETE /api/auth/account/

      // Simulate API call delay
      await new Promise((resolve) => setTimeout(resolve, 2000))

      // Mock successful deletion
      localStorage.removeItem("token")
      router.push("/")
    } catch (error) {
      console.error("Account deletion failed:", error)
      setError("Failed to delete account. Please try again.")
    } finally {
      setIsDeletingAccount(false)
    }
  }

  const resetDeleteConfirmation = () => {
    setShowDeleteConfirmation(false)
    setDeleteConfirmationText("")
    setDeletePassword("")
    setError(null)
  }

  // Get user initials for avatar
  const getUserInitials = () => {
    if (!user) return "U"
    return user.username[0].toUpperCase()
  }

  // Format relative date
  const formatRelativeDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      const now = new Date()
      const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))

      if (diffInDays === 0) return "Today"
      if (diffInDays === 1) return "Yesterday"
      if (diffInDays < 7) return `${diffInDays} days ago`
      if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`
      return `${Math.floor(diffInDays / 30)} months ago`
    } catch {
      return "Unknown"
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading account information...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <ShoppingBag className="h-8 w-8 text-blue-600" />
                <h1 className="text-xl font-bold text-gray-900">Shoe Shopper</h1>
              </div>
            </div>

            {/* User Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="flex items-center space-x-2 p-2 rounded-full hover:bg-gray-100 transition-colors"
                aria-label="User menu"
              >
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  {getUserInitials()}
                </div>
                <ChevronDown className="h-4 w-4 text-gray-500" />
              </button>

              {showDropdown && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">{user?.username}</p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                  </div>
                  <div className="py-1">
                    <button className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 bg-gray-50">
                      <User className="mr-2 h-4 w-4" />
                      Account
                    </button>
                    <hr className="my-1" />
                    <button
                      onClick={handleLogout}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <LogOut className="mr-2 h-4 w-4" />
                      Log out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header with back button */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <Link
              href="/upload"
              className="flex items-center space-x-2 text-blue-600 hover:text-blue-700 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Dashboard</span>
            </Link>
          </div>

          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Account</h2>
            <p className="text-gray-600">Your account information and latest measurement.</p>
          </div>
        </div>

        <div className="space-y-6">
          {/* Account Information */}
          <div className="bg-white rounded-lg shadow border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                <UserCircle className="h-5 w-5" />
                <h3 className="text-lg font-semibold text-gray-900">Account Information</h3>
              </div>
            </div>
            <div className="p-6">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white text-lg font-medium">
                  {getUserInitials()}
                </div>
                <div>
                  <h4 className="text-lg font-medium text-gray-900">{user?.username}</h4>
                  <p className="text-sm text-gray-600">{user?.email}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Latest Measurement */}
          {latestMeasurement ? (
            <div className="bg-white rounded-lg shadow border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Ruler className="h-5 w-5" />
                    <h3 className="text-lg font-semibold text-gray-900">Latest Measurement</h3>
                  </div>
                  <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">Mock Data</span>
                </div>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-blue-600">{latestMeasurement.length_inches}"</div>
                    <div className="text-sm text-gray-600">Length</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-green-600">{latestMeasurement.width_inches}"</div>
                    <div className="text-sm text-gray-600">Width</div>
                  </div>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <Calendar className="h-4 w-4" />
                  <span>Measured {formatRelativeDate(latestMeasurement.created_at)}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center space-x-2">
                  <Ruler className="h-5 w-5" />
                  <h3 className="text-lg font-semibold text-gray-900">Measurements</h3>
                </div>
              </div>
              <div className="p-6">
                <div className="text-center py-8">
                  <Camera className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">No measurements yet</h4>
                  <p className="text-gray-600 mb-4">Upload your first foot photo to get started.</p>
                  <Link
                    href="/upload"
                    className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
                  >
                    <Camera className="h-4 w-4" />
                    <span>Take Measurement</span>
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* Danger Zone */}
          <div className="bg-white rounded-lg shadow border border-red-200">
            <div className="px-6 py-4 border-b border-red-200">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <h3 className="text-lg font-semibold text-red-900">Delete Account</h3>
              </div>
            </div>
            <div className="p-6">
              <p className="text-sm text-gray-600 mb-4">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
              <button
                onClick={() => setShowDeleteConfirmation(true)}
                className="flex items-center space-x-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
              >
                <Trash2 className="h-4 w-4" />
                <span>Delete Account</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirmation && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ backgroundColor: "rgba(0, 0, 0, 0.5)" }}
        >
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">Delete Account</h2>
                <p className="text-sm text-gray-600">This action cannot be undone</p>
              </div>
            </div>

            <div className="mb-6">
              <p className="text-gray-700 mb-4">
                Are you sure you want to delete your account? This will permanently remove all your data.
              </p>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">{error}</div>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="confirm-username" className="block text-sm font-medium text-gray-700 mb-1">
                  Type your username <span className="font-bold">{user?.username}</span> to confirm:
                </label>
                <input
                  type="text"
                  id="confirm-username"
                  value={deleteConfirmationText}
                  onChange={(e) => setDeleteConfirmationText(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 text-black"
                  placeholder={user?.username}
                  disabled={isDeletingAccount}
                />
              </div>

              <div>
                <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700 mb-1">
                  Enter your password to confirm:
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    id="confirm-password"
                    value={deletePassword}
                    onChange={(e) => setDeletePassword(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 pr-10 text-black"
                    placeholder="Enter your password"
                    disabled={isDeletingAccount}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                    disabled={isDeletingAccount}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={resetDeleteConfirmation}
                className="flex-1 border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isDeletingAccount}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isDeletingAccount || deleteConfirmationText !== user?.username || !deletePassword.trim()}
              >
                {isDeletingAccount ? "Deleting..." : "Delete Account"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
