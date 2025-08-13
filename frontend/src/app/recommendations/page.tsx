"use client"
import { useState, useEffect, useRef } from "react"
import {
  ShoppingBag,
  User,
  LogOut,
  ChevronDown,
  ArrowLeft,
  SlidersHorizontal,
  Filter,
  AlertCircle,
  Camera,
  ExternalLink,
  Ruler,
} from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"

// API configuration
const API_BASE_URL = "https://shoeshopper.onrender.com"

// Cache configuration
const CACHE_DURATION_HOURS = 1
const CACHE_KEYS = {
  CATEGORIES: 'categoriesCache',
  CATEGORIES_TIME: 'categoriesCacheTime'
} as const

// Options for filters
const GENDER_OPTIONS = ["Men", "Women", "Unisex"]
const BRAND_OPTIONS = [
  "Adidas",
  "Allbirds",
  "Altra",
  "Converse",
  "Danner",
  "Hoka",
  "New Balance",
  "Nike",
  "On Cloud",
  "Puma",
  "Saucony",
  "Solomon",
  "Thursday",
]
const FUNCTION_OPTIONS = ["casual", "hiking", "work", "running"]

interface AppUser {
  id: number
  username: string
  first_name?: string
  last_name?: string
  email: string
}

interface Shoe {
  id: number
  company: string
  model: string
  gender: "M" | "W" | "U"
  us_size: number
  width_category: "N" | "D" | "W"
  function: string
  price_usd: number
  product_url: string
  is_active: boolean
  fit_score?: number
  shoe_image?: string
  image_url?: string
  insole_length?: number
  insole_width?: number
  insole_perimeter?: number
  insole_area?: number
}

interface UserMeasurements {
  length_inches: number
  width_inches: number
}

interface UserPreferences {
  gender: string[]
  brand: string[]
  function: string[]
  maxPrice: number
}

interface CategoryOption {
  value: string
  label: string
}

interface Categories {
  companies: string[]
  genders: CategoryOption[]
  widths: CategoryOption[]
  functions: CategoryOption[]
}

// Type validation for cached data
const validateCategories = (data: any): data is Categories => {
  return data && 
         typeof data === 'object' &&
         Array.isArray(data.companies) &&
         Array.isArray(data.genders) &&
         Array.isArray(data.widths) &&
         Array.isArray(data.functions) &&
         data.genders.every((g: any) => g && typeof g.value === 'string' && typeof g.label === 'string') &&
         data.widths.every((w: any) => w && typeof w.value === 'string' && typeof w.label === 'string') &&
         data.functions.every((f: any) => f && typeof f.value === 'string' && typeof f.label === 'string')
}

// Fallback categories to eliminate code duplication
const createFallbackCategories = (): Categories => ({
  companies: BRAND_OPTIONS,
  genders: [
    { value: "M", label: "Men" },
    { value: "W", label: "Women" }, 
    { value: "U", label: "Unisex" }
  ],
  widths: [
    { value: "N", label: "Narrow" },
    { value: "D", label: "Regular" },
    { value: "W", label: "Wide" }
  ],
  functions: FUNCTION_OPTIONS.map(f => ({ value: f, label: f.charAt(0).toUpperCase() + f.slice(1) }))
})

// Safe cache operations
const saveToCache = (data: Categories): void => {
  try {
    localStorage.setItem(CACHE_KEYS.CATEGORIES, JSON.stringify(data))
    localStorage.setItem(CACHE_KEYS.CATEGORIES_TIME, Date.now().toString())
  } catch (error) {
    console.warn('Failed to cache categories - continuing without cache:', error)
  }
}

const clearCache = (): void => {
  try {
    localStorage.removeItem(CACHE_KEYS.CATEGORIES)
    localStorage.removeItem(CACHE_KEYS.CATEGORIES_TIME)
  } catch (error) {
    console.warn('Failed to clear category cache:', error)
  }
}

export default function RecommendationsPage() {
  const router = useRouter()
  const [user, setUser] = useState<AppUser | null>(null)
  const dataLoadedRef = useRef(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingData, setIsLoadingData] = useState(false)
  const [allShoes, setAllShoes] = useState<Shoe[]>([])
  const [filteredShoes, setFilteredShoes] = useState<Shoe[]>([])
  const [userMeasurements, setUserMeasurements] = useState<UserMeasurements | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<"fit_score" | "price_low" | "price_high">("fit_score")
  const [showFilters, setShowFilters] = useState(false)
  const [categories, setCategories] = useState<Categories | null>(null)
  const [guestSessionId, setGuestSessionId] = useState<string | null>(null)

  // Load preferences from localStorage
  const [preferences, setPreferences] = useState<UserPreferences>({
    gender: [],
    brand: [],
    function: [],
    maxPrice: 1000,
  })

  // Initialize guest session for guest users
  const initializeGuestSession = () => {
    const isGuest = localStorage.getItem("isGuest") === "true"
    if (isGuest && !guestSessionId) {
      // Try to get existing session ID from localStorage (created when "Try as Guest" was clicked)
      const existingSessionId = localStorage.getItem("guestSessionId")
      if (existingSessionId) {
        setGuestSessionId(existingSessionId)
        console.log("Using existing guest session ID:", existingSessionId.substring(0, 8) + "...")
      } else {
        console.warn("No guest session ID found - session should have been created when 'Try as Guest' was clicked")
        // User should go back and upload a foot image first
      }
    }
  }

  // Check authentication and get user info
  useEffect(() => {
    checkAuth()
    // Initialize guest session ID for guest users
    initializeGuestSession()
  }, [])

  // Load preferences, categories and shoes when auth check is complete
  useEffect(() => {
    if (!isLoading && !dataLoadedRef.current) {
      dataLoadedRef.current = true
      loadSavedPreferences()
      loadCategories()
      loadAllShoes()
    }
  }, [isLoading])

  // Apply filters and sorting whenever preferences, sorting, or shoes change
  useEffect(() => {
    applyFiltersAndSorting()
  }, [allShoes, preferences, sortBy])

  const loadSavedPreferences = () => {
    try {
      const savedPreferences = localStorage.getItem("userPreferences")
      if (savedPreferences) {
        const prefs = JSON.parse(savedPreferences)
        setPreferences(prefs)
      }
    } catch (error) {
      console.error("Error loading saved preferences:", error)
    }
  }

  const savePreferences = (newPreferences: UserPreferences) => {
    try {
      localStorage.setItem("userPreferences", JSON.stringify(newPreferences))
      setPreferences(newPreferences)
    } catch (error) {
      console.error("Error saving preferences:", error)
    }
  }

  const loadCategories = async () => {
    try {
      // Check cache first with validation
      const cachedData = localStorage.getItem(CACHE_KEYS.CATEGORIES)
      const cacheTime = localStorage.getItem(CACHE_KEYS.CATEGORIES_TIME)
      
      if (cachedData && cacheTime) {
        const hoursSinceCache = (Date.now() - parseInt(cacheTime)) / (1000 * 60 * 60)
        if (hoursSinceCache < CACHE_DURATION_HOURS) {
          try {
            const parsedData = JSON.parse(cachedData)
            if (validateCategories(parsedData)) {
              setCategories(parsedData)
              console.log("✅ Loaded validated cached categories")
              return
            } else {
              console.warn("Cached categories failed validation, clearing cache")
              clearCache()
            }
          } catch (parseError) {
            console.warn("Failed to parse cached categories, clearing cache:", parseError)
            clearCache()
          }
        } else {
          console.log("Cache expired, clearing and fetching fresh data")
          clearCache()
        }
      }
      
      // Fetch fresh categories from API
      const response = await fetch(`${API_BASE_URL}/api/categories/`)
      if (response.ok) {
        const categoryData = await response.json()
        
        if (validateCategories(categoryData)) {
          setCategories(categoryData)
          saveToCache(categoryData)
          console.log("✅ Loaded and cached fresh categories")
        } else {
          console.warn("API returned invalid category structure, using fallback")
          const fallbackCategories = createFallbackCategories()
          setCategories(fallbackCategories)
        }
      } else {
        if (response.status === 429) {
          console.warn("Rate limit exceeded, using fallback categories")
        } else {
          console.warn(`API request failed with status ${response.status}, using fallback`)
        }
        const fallbackCategories = createFallbackCategories()
        setCategories(fallbackCategories)
      }
    } catch (error) {
      console.error("Error loading categories, using fallback:", error)
      const fallbackCategories = createFallbackCategories()
      setCategories(fallbackCategories)
    }
  }

  const checkAuth = async () => {
    const token = localStorage.getItem("token")
    const isGuest = localStorage.getItem("isGuest") === "true"
    
    if (!token && !isGuest) {
      router.push("/")
      return
    }
    
    if (isGuest) {
      // Guest user, no auth check needed
      setIsLoading(false)
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

  const loadAllShoes = async () => {
    setIsLoadingData(true)
    setError(null)

    try {
      const token = localStorage.getItem("token")
      const isGuest = localStorage.getItem("isGuest") === "true"

      // Get User Measurements - REAL API CALL
      let measurements = null
      try {
        const headers: { [key: string]: string } = {
          "Content-Type": "application/json",
        }
        
        // Only add auth header if user is authenticated
        if (token && !isGuest) {
          headers.Authorization = `Token ${token}`
        }
        
        // Include guest session ID for guest users
        if (isGuest && guestSessionId) {
          headers["X-Guest-Session-ID"] = guestSessionId
        }
        
        const measurementsResponse = await fetch(`${API_BASE_URL}/api/measurements/latest/`, {
          headers,
          credentials: "include", // Important: Include session cookies for guest isolation
        })

        if (measurementsResponse.ok) {
          measurements = await measurementsResponse.json()
          setUserMeasurements({
            length_inches: measurements.length_inches,
            width_inches: measurements.width_inches,
          })
          console.log("✅ Loaded real user measurements:", measurements)
        } else {
          console.warn("No user measurements found, user needs to upload foot image first")
          setError("Please upload a foot image first to get personalized recommendations")
          return
        }
      } catch (error) {
        console.error("Could not load user measurements:", error)
        
        // Better error messages for mobile users
        let errorMessage = "Failed to load your foot measurements. Please upload a foot image first."
        if (error instanceof TypeError && error.message.includes("NetworkError")) {
          errorMessage = "Network error loading measurements. Please check your internet connection and try again."
        } else if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
          errorMessage = "Cannot reach server to load measurements. Please check your internet connection."
        }
        
        setError(errorMessage)
        return
      }

      // Load recommendations from backend - REAL API CALL
      try {
        const headers: { [key: string]: string } = {
          "Content-Type": "application/json",
        }
        
        // Only add auth header if user is authenticated
        if (token && !isGuest) {
          headers.Authorization = `Token ${token}`
        }
        
        // Include guest session ID for guest users
        if (isGuest && guestSessionId) {
          headers["X-Guest-Session-ID"] = guestSessionId
        }
        
        const recommendationsResponse = await fetch(`${API_BASE_URL}/api/recommendations/`, {
          headers,
          credentials: "include", // Important: Include session cookies for guest isolation
        })

        if (recommendationsResponse.ok) {
          const recommendationsData = await recommendationsResponse.json()
          console.log("✅ Loaded real recommendations:", recommendationsData)

          // The backend returns an object with recommendations array
          const shoes = Array.isArray(recommendationsData)
            ? recommendationsData
            : recommendationsData.recommendations || []

          setAllShoes(shoes)
          console.log(`Loaded ${shoes.length} real shoe recommendations`)
        } else {
          throw new Error(`Failed to load recommendations: ${recommendationsResponse.status}`)
        }
      } catch (recommendationsError) {
        console.error("Failed to load recommendations from backend:", recommendationsError)
        
        // Better error messages for mobile users
        let errorMessage = "Failed to load shoe recommendations. Please try again later."
        if (recommendationsError instanceof TypeError && recommendationsError.message.includes("NetworkError")) {
          errorMessage = "Network error loading recommendations. Please check your internet connection."
        } else if (recommendationsError instanceof TypeError && recommendationsError.message.includes("Failed to fetch")) {
          errorMessage = "Cannot reach server to load recommendations. Please check your internet connection."
        }
        
        setError(errorMessage)
        setAllShoes([]) // Clear any existing data
      }
    } catch (error) {
      console.error("Failed to load data:", error)
      
      // Better error messages for mobile users
      let errorMessage = "Failed to load shoe recommendations. Please try again later."
      if (error instanceof TypeError && error.message.includes("NetworkError")) {
        errorMessage = "Network error. Please check your internet connection and try again."
      } else if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
        errorMessage = "Cannot reach server. Please check your internet connection."
      } else if (error instanceof Error) {
        errorMessage = error.message
      }
      
      setError(errorMessage)
      setAllShoes([]) // Clear any existing data
    } finally {
      setIsLoadingData(false)
    }
  }

  const applyFiltersAndSorting = () => {
    let filtered = [...allShoes]

    // Apply gender filter with optimized lookup
    if (preferences.gender.length > 0 && categories) {
      // Create lookup map for performance (O(1) instead of O(n))
      const genderLabelToCode = categories.genders.reduce((map, option) => {
        map[option.label] = option.value
        return map
      }, {} as Record<string, string>)
      
      const genderCodes = preferences.gender.map((g) => {
        return genderLabelToCode[g] || (g === "Men" ? "M" : g === "Women" ? "W" : "U")
      })
      filtered = filtered.filter((shoe) => genderCodes.includes(shoe.gender))
    }

    // Apply brand filter (no mapping needed, company names are direct)
    if (preferences.brand.length > 0) {
      filtered = filtered.filter((shoe) => preferences.brand.includes(shoe.company))
    }

    // Apply function filter (no mapping needed, values are direct)
    if (preferences.function.length > 0) {
      filtered = filtered.filter((shoe) => preferences.function.includes(shoe.function))
    }

    // Apply price filter
    if (preferences.maxPrice < 1000) {
      filtered = filtered.filter((shoe) => shoe.price_usd <= preferences.maxPrice)
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case "fit_score":
          return (b.fit_score || 0) - (a.fit_score || 0)
        case "price_low":
          return a.price_usd - b.price_usd
        case "price_high":
          return b.price_usd - a.price_usd
        default:
          return 0
      }
    })

    setFilteredShoes(filtered)
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

  const handleFilterChange = (category: keyof UserPreferences, value: string) => {
    if (category === "maxPrice") return

    const newPreferences = {
      ...preferences,
      [category]: (preferences[category] as string[]).includes(value)
        ? (preferences[category] as string[]).filter((item) => item !== value)
        : [...(preferences[category] as string[]), value],
    }
    savePreferences(newPreferences)
  }

  const handlePriceChange = (price: number) => {
    const newPreferences = { ...preferences, maxPrice: price }
    savePreferences(newPreferences)
  }

  const clearAllFilters = () => {
    const newPreferences = { gender: [], brand: [], function: [], maxPrice: 1000 }
    savePreferences(newPreferences)
  }

  const getActiveFiltersCount = () => {
    return (
      preferences.gender.length +
      preferences.brand.length +
      preferences.function.length +
      (preferences.maxPrice < 1000 ? 1 : 0)
    )
  }

  // Get user initials for avatar
  const getUserInitials = () => {
    const isGuest = localStorage.getItem("isGuest") === "true"
    if (isGuest) return "G"
    if (!user) return "U"
    const firstInitial = user.first_name ? user.first_name[0] : user.username[0]
    const lastInitial = user.last_name ? user.last_name[0] : ""
    return (firstInitial + lastInitial).toUpperCase()
  }

  // Get user display name
  const getUserDisplayName = () => {
    const isGuest = localStorage.getItem("isGuest") === "true"
    if (isGuest) return "Guest"
    if (!user) return "User"
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`
    }
    return user.username
  }

  // Get shoe image URL with proper fallback
  const getShoeImageUrl = (shoe: Shoe) => {
    // First try the computed image_url field from the backend
    if (shoe.image_url) {
      return shoe.image_url
    }

    // Fallback to shoe_image field if available
    if (shoe.shoe_image) {
      // If it's a full URL, use it directly
      if (shoe.shoe_image.startsWith("http")) {
        return shoe.shoe_image
      }
      // If it's a relative path, prepend the API base URL
      return `${API_BASE_URL}${shoe.shoe_image}`
    }

    // Final fallback to placeholder
    return `/placeholder.svg?height=200&width=200&text=${encodeURIComponent(shoe.company + " " + shoe.model)}`
  }

  // Get fit score color
  const getFitScoreColor = (score: number) => {
    if (score >= 90) return "text-green-600 bg-green-50"
    if (score >= 75) return "text-yellow-600 bg-yellow-50"
    return "text-red-600 bg-red-50"
  }

  // Get fit score label
  const getFitScoreLabel = (score: number) => {
    if (score >= 90) return "Excellent Fit"
    if (score >= 75) return "Good Fit"
    if (score >= 60) return "Fair Fit"
    return "Poor Fit"
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Setting up your session...</p>
        </div>
      </div>
    )
  }

  if (isLoadingData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your personalized recommendations...</p>
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
            <div className="flex items-center space-x-2">
              <ShoppingBag className="h-6 w-6 text-blue-600" />
              <span className="font-semibold text-gray-900">Shoe Shopper</span>
            </div>

            {/* User dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="flex items-center space-x-2 px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 transition-colors"
              >
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  {getUserInitials()}
                </div>
                <ChevronDown className="h-4 w-4 text-gray-500" />
              </button>

              {showDropdown && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">{getUserDisplayName()}</p>
                    <p className="text-xs text-gray-500">
                      {localStorage.getItem("isGuest") === "true" ? "Guest User" : user?.email}
                    </p>
                  </div>
                  <div className="py-1">
                    {localStorage.getItem("isGuest") !== "true" && (
                      <>
                        <button
                          onClick={() => router.push("/account")}
                          className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        >
                          <User className="mr-2 h-4 w-4" />
                          Account
                        </button>
                        <hr className="my-1" />
                      </>
                    )}
                    {localStorage.getItem("isGuest") === "true" ? (
                      <button
                        onClick={() => {
                          localStorage.removeItem("isGuest")
                          localStorage.removeItem("guestSessionId") // Clean up guest session
                          localStorage.removeItem("userPreferences") // Clean up preferences
                          router.push("/")
                        }}
                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <LogOut className="mr-2 h-4 w-4" />
                        Exit Guest Mode
                      </button>
                    ) : (
                      <button
                        onClick={handleLogout}
                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <LogOut className="mr-2 h-4 w-4" />
                        Log out
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header with back button and measurements */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <Link
              href="/upload"
              className="flex items-center space-x-2 text-blue-600 hover:text-blue-700 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Upload</span>
            </Link>
          </div>

          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Your Shoe Recommendations</h2>
              <p className="text-gray-600">Based on your foot measurements and preferences.</p>
            </div>

            {userMeasurements && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2 flex items-center">
                  <Ruler className="h-4 w-4 mr-2" />
                  Your Foot Measurements
                </h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-blue-700">Length:</span>
                    <span className="font-mono ml-2 text-gray-900">{userMeasurements.length_inches}"</span>
                  </div>
                  <div>
                    <span className="text-blue-700">Width:</span>
                    <span className="font-mono ml-2 text-gray-900">{userMeasurements.width_inches}"</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5" />
              <span className="font-medium">Error:</span>
            </div>
            <p className="mt-1">{error}</p>
            {error.includes("upload a foot image") && (
              <button
                onClick={() => router.push("/upload")}
                className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Upload Foot Image
              </button>
            )}
          </div>
        )}

        {/* No measurements state */}
        {!isLoading && !isLoadingData && !error && allShoes.length === 0 && !userMeasurements && (
          <div className="text-center py-12">
            <Camera className="h-16 w-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Foot Measurements Found</h3>
            <p className="text-gray-600 mb-4">
              Please upload a photo of your foot on a piece of paper to get personalized shoe recommendations.
            </p>
            <button
              onClick={() => router.push("/upload")}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Upload Foot Image
            </button>
          </div>
        )}

        {/* Controls */}
        {allShoes.length > 0 && (
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
            {/* Filter button */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <SlidersHorizontal className="h-4 w-4 text-gray-700" />
                <span className="text-gray-700">Filters</span>
                {getActiveFiltersCount() > 0 && (
                  <span className="bg-blue-600 text-white text-xs rounded-full px-2 py-1">
                    {getActiveFiltersCount()}
                  </span>
                )}
              </button>

              {getActiveFiltersCount() > 0 && (
                <button onClick={clearAllFilters} className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                  Clear all
                </button>
              )}
            </div>

            {/* Sort dropdown */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-700">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as "fit_score" | "price_low" | "price_high")}
                className="border border-gray-300 rounded-lg px-3 py-2 bg-white text-sm text-gray-900"
              >
                <option value="fit_score">Best Fit</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
              </select>
            </div>
          </div>
        )}

        <div className="flex gap-8">
          {/* Filters Sidebar */}
          {showFilters && allShoes.length > 0 && (
            <div className="w-72 flex-shrink-0">
              <div className="bg-white border border-gray-200 rounded-lg p-6 sticky top-8">
                <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                  <Filter className="h-4 w-4 mr-2" />
                  Filters
                </h3>

                {/* Gender Filter */}
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-3">Gender</h4>
                  <div className="space-y-2">
                    {(categories?.genders || []).map((option) => (
                      <label key={option.value} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={preferences.gender.includes(option.label)}
                          onChange={() => handleFilterChange("gender", option.label)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{option.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Brand Filter */}
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-3">Brand</h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {(categories?.companies || []).map((company) => (
                      <label key={company} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={preferences.brand.includes(company)}
                          onChange={() => handleFilterChange("brand", company)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{company}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Function Filter */}
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-3">Function</h4>
                  <div className="space-y-2">
                    {(categories?.functions || []).map((option) => (
                      <label key={option.value} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={preferences.function.includes(option.value)}
                          onChange={() => handleFilterChange("function", option.value)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">{option.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Price Filter */}
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-3">Max Price</h4>
                  <input
                    type="range"
                    min="50"
                    max="1000"
                    step="25"
                    value={preferences.maxPrice}
                    onChange={(e) => handlePriceChange(Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-gray-500 mt-1">
                    <span>$50</span>
                    <span className="font-medium">${preferences.maxPrice}</span>
                    <span>$1000+</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Results */}
          <div className="flex-1">
            {filteredShoes.length === 0 && allShoes.length > 0 && (
              <div className="text-center py-12">
                <p className="text-gray-600 mb-4">No shoes match your current filters.</p>
                <button
                  onClick={clearAllFilters}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Clear Filters
                </button>
              </div>
            )}

            {filteredShoes.length > 0 && (
              <>
                <div className="flex items-center justify-between mb-6">
                  <p className="text-gray-600">
                    Showing {filteredShoes.length} shoe{filteredShoes.length !== 1 ? "s" : ""}
                    {allShoes.length !== filteredShoes.length && ` of ${allShoes.length}`}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredShoes.map((shoe) => (
                    <div
                      key={shoe.id}
                      className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="aspect-square relative bg-gray-50">
                        <img
                          src={getShoeImageUrl(shoe) || "/placeholder.svg"}
                          alt={`${shoe.company} ${shoe.model}`}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            // Fallback if image fails to load
                            e.currentTarget.src = `/placeholder.svg?height=200&width=200&text=${encodeURIComponent(shoe.company + " " + shoe.model)}`
                          }}
                        />
                        {shoe.fit_score && (
                          <div
                            className={`absolute top-3 left-3 px-2 py-1 rounded-full text-xs font-medium ${getFitScoreColor(shoe.fit_score)}`}
                          >
                            {shoe.fit_score}% fit
                          </div>
                        )}
                      </div>

                      <div className="p-4">
                        <div className="mb-2">
                          <h3 className="font-semibold text-gray-900">{shoe.company}</h3>
                          <p className="text-gray-600 text-sm">{shoe.model}</p>
                        </div>

                        <div className="flex items-center justify-between mb-3">
                          <span className="text-lg font-bold text-gray-900">${shoe.price_usd}</span>
                          <div className="text-sm text-gray-500">
                            Size {shoe.us_size} {shoe.width_category}
                          </div>
                        </div>

                        {shoe.fit_score && (
                          <div className="mb-3">
                            <div className="flex items-center justify-between text-sm mb-1">
                              <span className="text-gray-700">Fit Score</span>
                              <span className={`font-medium ${getFitScoreColor(shoe.fit_score).split(" ")[0]}`}>
                                {getFitScoreLabel(shoe.fit_score)}
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${shoe.fit_score >= 90 ? "bg-green-500" : shoe.fit_score >= 75 ? "bg-yellow-500" : "bg-red-500"}`}
                                style={{ width: `${shoe.fit_score}%` }}
                              ></div>
                            </div>
                          </div>
                        )}

                        <div className="flex items-center justify-between text-sm text-gray-600 mb-3">
                          <span className="px-2 py-1 bg-gray-100 rounded text-xs">{shoe.function}</span>
                          <span>{shoe.gender === "M" ? "Men's" : shoe.gender === "W" ? "Women's" : "Unisex"}</span>
                        </div>

                        <a
                          href={shoe.product_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center justify-center w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                        >
                          <span>View Product</span>
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
