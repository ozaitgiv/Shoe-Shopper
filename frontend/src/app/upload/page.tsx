"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Upload, Camera, Ruler, ShoppingBag, User, Settings, LogOut, ChevronDown, AlertCircle } from "lucide-react"
import Image from "next/image"
import { useRouter } from "next/navigation"

// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface AppUser {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
}

interface MeasurementResult {
  id: number
  length_inches: number
  width_inches: number
  created_at: string
  image_url: string
  status: "processing" | "complete" | "error"
}

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState<AppUser | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [measurementResult, setMeasurementResult] = useState<MeasurementResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)

  // Check authentication and get user info
  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    // TEMPORARY: Bypass authentication for testing
    // Remove this when the Django backend is ready
    setUser({
      id: 1,
      username: "testuser",
      first_name: "Test",
      last_name: "User",
      email: "test@example.com",
    })
    setIsLoading(false)
    return

    // Original auth code below (commented out for now)
    /*
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/user/`, {
        credentials: "include",
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // Not authenticated, redirect to landing page
        router.push("/")
      }
    } catch (error) {
      console.error("Auth check failed:", error)
      router.push("/")
    } finally {
      setIsLoading(false)
    }
    */
  }

  const handleLogout = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/logout/`, {
        method: "POST",
        credentials: "include",
      })

      if (response.ok) {
        router.push("/")
      } else {
        console.error("Logout failed")
      }
    } catch (error) {
      console.error("Logout failed:", error)
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const validateFile = (file: File): string | null => {
    // Check file type
    if (!file.type.startsWith("image/")) {
      return "Please upload an image file (JPG, PNG, HEIC)"
    }

    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024 // 10MB in bytes
    if (file.size > maxSize) {
      return "File size must be less than 10MB"
    }

    return null
  }

  const handleFile = async (file: File) => {
    // Reset previous states
    setError(null)
    setMeasurementResult(null)
    setUploadProgress(0)

    // Validate file
    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }

    // Show preview immediately
    const reader = new FileReader()
    reader.onload = (e) => {
      setUploadedImage(e.target?.result as string)
    }
    reader.readAsDataURL(file)

    // Start processing
    setIsProcessing(true)

    try {
      // Get CSRF token
      const csrfResponse = await fetch(`${API_BASE_URL}/api/csrf/`, {
        credentials: "include",
      })

      if (!csrfResponse.ok) {
        throw new Error("Failed to get CSRF token")
      }

      const { csrfToken } = await csrfResponse.json()

      // Upload image with progress tracking
      const formData = new FormData()
      formData.append("image", file)

      const uploadResponse = await fetch(`${API_BASE_URL}/api/measurements/upload/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
        credentials: "include",
        body: formData,
      })

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json().catch(() => ({}))
        throw new Error(errorData.error || `Upload failed with status ${uploadResponse.status}`)
      }

      const uploadData = await uploadResponse.json()
      const measurementId = uploadData.measurement_id

      // Poll for results
      await pollForResults(measurementId)
    } catch (error) {
      console.error("Upload failed:", error)
      setError(error instanceof Error ? error.message : "Upload failed. Please try again.")
      setIsProcessing(false)
    }
  }

  const pollForResults = async (measurementId: number): Promise<void> => {
    const maxAttempts = 60 // 60 seconds max (increased for production)
    let attempts = 0

    const poll = async (): Promise<void> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/measurements/${measurementId}/`, {
          credentials: "include",
        })

        if (!response.ok) {
          throw new Error(`Failed to get measurement status: ${response.status}`)
        }

        const data = await response.json()

        if (data.status === "complete") {
          // Use the backend data directly (no conversion needed)
          setMeasurementResult(data)
          setIsProcessing(false)
          return
        } else if (data.status === "error") {
          setError(data.error_message || "Processing failed. Please try again.")
          setIsProcessing(false)
          return
        }

        // Still processing, continue polling
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000) // Poll every second
        } else {
          setError("Processing timeout. Please try again with a clearer image.")
          setIsProcessing(false)
        }
      } catch (error) {
        console.error("Polling error:", error)
        setError("Failed to get processing results. Please try again.")
        setIsProcessing(false)
      }
    }

    await poll()
  }

  // Get user initials for avatar
  const getUserInitials = () => {
    if (!user) return "U"
    const firstInitial = user.first_name ? user.first_name[0] : user.username[0]
    const lastInitial = user.last_name ? user.last_name[0] : ""
    return (firstInitial + lastInitial).toUpperCase()
  }

  // Get user display name
  const getUserDisplayName = () => {
    if (!user) return "User"
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`
    }
    return user.username
  }

  const resetUpload = () => {
    setUploadedImage(null)
    setIsProcessing(false)
    setMeasurementResult(null)
    setError(null)
    setUploadProgress(0)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
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
                    <p className="text-sm font-medium text-gray-900">{getUserDisplayName()}</p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                  </div>
                  <div className="py-1">
                    <button className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      <User className="mr-2 h-4 w-4" />
                      Profile
                    </button>
                    <button className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      <Settings className="mr-2 h-4 w-4" />
                      Settings
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Measure Your Feet</h2>
          <p className="text-gray-600">
            Upload a photo of your foot on paper to get accurate measurements and personalized shoe recommendations.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-8">
          {/* Upload Section */}
          <div className="">
            <div className="bg-white rounded-lg shadow border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center space-x-2">
                  <Camera className="h-5 w-5" />
                  <h3 className="text-lg font-semibold text-gray-900">Upload Foot Photo</h3>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Place your foot on a piece of paper and take a clear photo from directly above. Align your heel with
                  the back edge of the paper.
                </p>
              </div>
              <div className="p-6">
                {/* Error Display */}
                {error && (
                  <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
                    <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-red-900">Upload Error</p>
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  </div>
                )}

                {!uploadedImage ? (
                  <div
                    className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                      dragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
                    }`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                  >
                    <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <p className="text-lg font-medium text-gray-900 mb-2">Drop your image here, or click to browse</p>
                    <p className="text-sm text-gray-500 mb-4">Supports JPG, PNG, and HEIC files up to 10MB</p>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFileInput}
                      className="hidden"
                      id="file-upload"
                    />
                    <label
                      htmlFor="file-upload"
                      className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors cursor-pointer"
                    >
                      Choose File
                    </label>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="relative">
                      <Image
                        src={uploadedImage || "/placeholder.svg"}
                        alt="Uploaded foot image"
                        width={600}
                        height={400}
                        className="w-full h-64 object-cover rounded-lg border"
                      />
                      {isProcessing && (
                        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
                          <div className="text-white text-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
                            <p>Processing image...</p>
                            <p className="text-sm mt-1">This may take up to 60 seconds</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {!isProcessing && measurementResult && measurementResult.status === "complete" && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-center space-x-2 mb-3">
                          <Ruler className="h-5 w-5 text-green-600" />
                          <h3 className="font-medium text-green-900">Measurements Complete</h3>
                        </div>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">Length:</span>
                            <span className="ml-2 font-medium text-green-900">{measurementResult.length_inches}"</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Width:</span>
                            <span className="ml-2 font-medium text-green-900">{measurementResult.width_inches}"</span>
                          </div>
                        </div>
                        <button className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors">
                          View Shoe Recommendations
                        </button>
                      </div>
                    )}

                    <button
                      onClick={resetUpload}
                      className="w-full border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-md font-medium transition-colors"
                    >
                      Upload Another Photo
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Instructions */}
            <div className="bg-white rounded-lg shadow border border-gray-200 mt-6">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Photo Guidelines</h3>
                <p className="text-sm text-gray-600 mt-1">Follow these steps for accurate measurements</p>
              </div>
              <div className="p-6">
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Example Image */}
                  <div>
                    <h4 className="font-medium mb-3 text-gray-900">Example Photo</h4>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 bg-gray-50">
                      <div className="w-full h-32 bg-gray-200 rounded border flex items-center justify-center">
                        <div className="text-center text-gray-500">
                          <Camera className="h-8 w-8 mx-auto mb-2" />
                          <p className="text-sm">Example image will go here</p>
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 mt-2 text-center">
                        Foot placed on white paper, photographed from above
                      </p>
                    </div>
                  </div>

                  {/* Instructions */}
                  <div>
                    <h4 className="font-medium mb-3 text-gray-900">Steps to Follow</h4>
                    <div className="space-y-3 text-sm">
                      <div className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 mt-0.5">
                          1
                        </div>
                        <p className="text-gray-700">Place your foot on a white piece of paper (letter size)</p>
                      </div>
                      <div className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 mt-0.5">
                          2
                        </div>
                        <p className="text-gray-700">
                          Take the photo from directly above, ensuring the entire foot and paper edges are visible
                        </p>
                      </div>
                      <div className="flex items-start space-x-3">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 mt-0.5">
                          3
                        </div>
                        <p className="text-gray-700">
                          Ensure good lighting and avoid shadows for accurate measurements
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
