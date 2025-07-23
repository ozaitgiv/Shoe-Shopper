"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Upload, Camera, Ruler, ShoppingBag, User, LogOut, ChevronDown, AlertCircle, Filter } from "lucide-react"
import Image from "next/image"
import { useRouter } from "next/navigation"

// API configuration
const API_BASE_URL = "https://shoeshopper.onrender.com"

const GENDER_OPTIONS = ["Men", "Women", "Unisex"]
const BRAND_OPTIONS = [
  "Adidas",
  "Allbirds",
  "Altra",
  "Converse",
  "Danner",
  "Doc Marten",
  "Hoka",
  "Muji",
  "New Balance",
  "Nike",
  "On Cloud",
  "Puma",
  "Saucony",
  "Solomon",
  "Thursday",
  "Vivobarefoot",
]
const FUNCTION_OPTIONS = ["Casual", "Hiking", "Work", "Running"]

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

interface UserPreferences {
  gender: string[]
  brand: string[]
  function: string[]
  maxPrice: number
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

  const [filters, setFilters] = useState<UserPreferences>({
    gender: [],
    brand: [],
    function: [],
    maxPrice: 1000,
  })

  const [showFilters, setShowFilters] = useState(true)

  // Check authentication and get user info
  useEffect(() => {
    checkAuth()
  }, [])

  // Load saved preferences on component mount
  useEffect(() => {
    loadSavedPreferences()
  }, [])

  const loadSavedPreferences = () => {
    try {
      const savedPreferences = localStorage.getItem("userPreferences")
      if (savedPreferences) {
        const preferences = JSON.parse(savedPreferences)
        setFilters(preferences)
      }
    } catch (error) {
      console.error("Error loading saved preferences:", error)
    }
  }

  const savePreferences = (newFilters: UserPreferences) => {
    try {
      localStorage.setItem("userPreferences", JSON.stringify(newFilters))
    } catch (error) {
      console.error("Error saving preferences:", error)
    }
  }

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

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(e.type === "dragenter" || e.type === "dragover")
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0])
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) handleFile(e.target.files[0])
  }

  const validateFile = (file: File): string | null => {
    if (!file.type.startsWith("image/")) return "Please upload an image file (JPG, PNG, HEIC)"
    if (file.size > 10 * 1024 * 1024) return "File size must be less than 10MB"
    return null
  }

  const handleFile = async (file: File) => {
    setError(null)
    setMeasurementResult(null)
    setUploadProgress(0)

    const validationError = validateFile(file)
    if (validationError) {
      setError(validationError)
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => setUploadedImage(e.target?.result as string)
    reader.readAsDataURL(file)

    setIsProcessing(true)

    try {
      const csrfResponse = await fetch(`${API_BASE_URL}/api/csrf/`, {
        credentials: "include",
      })
      if (!csrfResponse.ok) throw new Error("Failed to get CSRF token")
      const { csrfToken } = await csrfResponse.json()

      const formData = new FormData()
      formData.append("image", file)

      const token = localStorage.getItem("token")
      if (!token) throw new Error("User not authenticated")

      const uploadResponse = await fetch(`${API_BASE_URL}/api/measurements/upload/`, {
        method: "POST",
        headers: {
          Authorization: `Token ${token}`,
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
      await pollForResults(uploadData.measurement_id)
    } catch (error) {
      console.error("Upload failed:", error)
      setError(error instanceof Error ? error.message : "Upload failed. Please try again.")
      setIsProcessing(false)
    }
  }

  const pollForResults = async (measurementId: number): Promise<void> => {
    const maxAttempts = 60
    let attempts = 0
    const token = localStorage.getItem("token")

    const poll = async (): Promise<void> => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/measurements/${measurementId}/`, {
          method: "GET",
          headers: {
            Authorization: `Token ${token}`,
          },
        })

        if (!response.ok) {
          throw new Error(`Failed to get measurement status: ${response.status}`)
        }

        const data = await response.json()

        if (data.status === "complete") {
          setMeasurementResult(data)
          setIsProcessing(false)
          return
        } else if (data.status === "error") {
          setError(data.error_message || "Processing failed. Please try again.")
          setIsProcessing(false)
          return
        }

        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 1000)
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

  const handleFilterChange = (category: keyof UserPreferences, value: string) => {
    if (category === "maxPrice") return // Handle price separately

    const newFilters = {
      ...filters,
      [category]: (filters[category] as string[]).includes(value)
        ? (filters[category] as string[]).filter((item) => item !== value)
        : [...(filters[category] as string[]), value],
    }
    setFilters(newFilters)
    savePreferences(newFilters)
  }

  const handlePriceChange = (price: number) => {
    const newFilters = { ...filters, maxPrice: price }
    setFilters(newFilters)
    savePreferences(newFilters)
  }

  const handleSelectAll = (category: keyof UserPreferences, options: string[]) => {
    if (category === "maxPrice") return // Handle price separately

    const currentArray = filters[category] as string[]
    const newFilters = {
      ...filters,
      [category]: currentArray.length === options.length ? [] : [...options],
    }
    setFilters(newFilters)
    savePreferences(newFilters)
  }

  const isAllSelected = (category: keyof UserPreferences, options: string[]) => {
    if (category === "maxPrice") return false
    return (filters[category] as string[]).length === options.length
  }

  const clearAllFilters = () => {
    const newFilters = { gender: [], brand: [], function: [], maxPrice: 1000 }
    setFilters(newFilters)
    savePreferences(newFilters)
  }

  const navigateToRecommendations = () => {
    // Save current preferences before navigating
    savePreferences(filters)
    router.push("/recommendations")
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
                    <button
                      onClick={() => router.push("/account")}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Measure Your Feet</h2>
          <p className="text-gray-600">
            Upload a photo of your foot on paper to get accurate measurements and personalized shoe recommendations.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Filter Section */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow border border-gray-200 sticky top-8">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Filter className="h-5 w-5" />
                    <h3 className="text-lg font-semibold text-gray-900">Your Preferences</h3>
                  </div>
                  <button
                    onClick={() => setShowFilters(!showFilters)}
                    className="lg:hidden text-gray-500 hover:text-gray-700"
                  >
                    <ChevronDown
                      className={`h-4 w-4 transform transition-transform ${showFilters ? "rotate-180" : ""}`}
                    />
                  </button>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Set your preferences to get personalized shoe recommendations
                </p>
              </div>

              <div className={`${showFilters ? "block" : "hidden lg:block"}`}>
                <div className="p-6 space-y-6">
                  {/* Gender Filter */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">Gender</h4>
                      <button
                        onClick={() => handleSelectAll("gender", GENDER_OPTIONS)}
                        className="text-xs text-blue-600 hover:text-blue-700"
                      >
                        {isAllSelected("gender", GENDER_OPTIONS) ? "Deselect All" : "Select All"}
                      </button>
                    </div>
                    <div className="space-y-2">
                      {GENDER_OPTIONS.map((option) => (
                        <label key={option} className="flex items-center">
                          <input
                            type="checkbox"
                            checked={filters.gender.includes(option)}
                            onChange={() => handleFilterChange("gender", option)}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Brand Filter */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">Brand</h4>
                      <button
                        onClick={() => handleSelectAll("brand", BRAND_OPTIONS)}
                        className="text-xs text-blue-600 hover:text-blue-700"
                      >
                        {isAllSelected("brand", BRAND_OPTIONS) ? "Deselect All" : "Select All"}
                      </button>
                    </div>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {BRAND_OPTIONS.map((option) => (
                        <label key={option} className="flex items-center">
                          <input
                            type="checkbox"
                            checked={filters.brand.includes(option)}
                            onChange={() => handleFilterChange("brand", option)}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Function Filter */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">Function</h4>
                      <button
                        onClick={() => handleSelectAll("function", FUNCTION_OPTIONS)}
                        className="text-xs text-blue-600 hover:text-blue-700"
                      >
                        {isAllSelected("function", FUNCTION_OPTIONS) ? "Deselect All" : "Select All"}
                      </button>
                    </div>
                    <div className="space-y-2">
                      {FUNCTION_OPTIONS.map((option) => (
                        <label key={option} className="flex items-center">
                          <input
                            type="checkbox"
                            checked={filters.function.includes(option)}
                            onChange={() => handleFilterChange("function", option)}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">{option}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Max Price Filter */}
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Max Price</h4>
                    <div className="space-y-3">
                      <input
                        type="range"
                        min="0"
                        max="1000"
                        step="25"
                        value={filters.maxPrice}
                        onChange={(e) => handlePriceChange(Number.parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                      />
                      <div className="flex justify-between text-sm text-gray-500">
                        <span>$0</span>
                        <span className="font-medium text-gray-900">${filters.maxPrice}</span>
                        <span>$1000+</span>
                      </div>
                    </div>
                  </div>

                  {/* Clear Filters */}
                  <button
                    onClick={clearAllFilters}
                    className="w-full text-sm text-gray-600 hover:text-gray-800 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Clear All Filters
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Upload Section */}
          <div className="lg:col-span-3">
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
                      <p className="text-sm text-gray-500 mb-4">
                        Supports JPG, PNG, BMP, WebP, and AVIF files up to 10MB
                      </p>
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
                          className="w-full h-64 object-contain rounded-lg border bg-gray-50"
                        />
                        {isProcessing && (
                          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
                            <div className="text-center">
                              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
                              <p className="text-white font-medium">Processing image...</p>
                              <p className="text-gray-200 text-sm mt-1">This may take up to 60 seconds</p>
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
                              <span className="ml-2 font-medium text-green-900">
                                {measurementResult.length_inches}"
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-600">Width:</span>
                              <span className="ml-2 font-medium text-green-900">{measurementResult.width_inches}"</span>
                            </div>
                          </div>
                          <button
                            onClick={navigateToRecommendations}
                            className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
                          >
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
                      <img
                        src="/Images/foot-example.jpg"
                        alt="Example of foot placed on white paper for measurement"
                        width={300}
                        height={240}
                        className="w-full rounded-lg shadow-sm"
                      />
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
    </div>
  )
}
