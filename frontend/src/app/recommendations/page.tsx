"use client"
import { useState, useEffect } from "react"
import {
  ShoppingBag,
  User,
  LogOut,
  ChevronDown,
  ExternalLink,
  ArrowLeft,
  Ruler,
  DollarSign,
  Package,
  Star,
} from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"

// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface AppUser {
  id: number
  username: string
  first_name: string
  last_name: string
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
  image_url?: string // Optional shoe image
}

interface UserMeasurements {
  length_inches: number
  width_inches: number
}

// MOCK DATA - Remove this section when backend is ready
const MOCK_USER_MEASUREMENTS: UserMeasurements = {
  length_inches: 10.5,
  width_inches: 4.2,
}

const MOCK_SHOES: Shoe[] = [
  {
    id: 1,
    company: "Nike",
    model: "Air Max 270",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Running",
    price_usd: 150.0,
    product_url: "https://nike.com/air-max-270",
    is_active: true,
    fit_score: 95,
    image_url: "/placeholder.svg?height=200&width=200&text=Nike+Air+Max+270",
  },
  {
    id: 2,
    company: "Adidas",
    model: "Ultraboost 22",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Running",
    price_usd: 180.0,
    product_url: "https://adidas.com/ultraboost-22",
    is_active: true,
    fit_score: 92,
    image_url: "/placeholder.svg?height=200&width=200&text=Adidas+Ultraboost",
  },
  {
    id: 3,
    company: "New Balance",
    model: "Fresh Foam X 1080v12",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Running",
    price_usd: 160.0,
    product_url: "https://newbalance.com/1080v12",
    is_active: true,
    fit_score: 89,
    image_url: "/placeholder.svg?height=200&width=200&text=New+Balance+1080",
  },
  {
    id: 4,
    company: "Allbirds",
    model: "Tree Runners",
    gender: "U",
    us_size: 10.5,
    width_category: "D",
    function: "Casual",
    price_usd: 98.0,
    product_url: "https://allbirds.com/tree-runners",
    is_active: true,
    fit_score: 87,
    image_url: "/placeholder.svg?height=200&width=200&text=Allbirds+Tree+Runners",
  },
  {
    id: 5,
    company: "Hoka",
    model: "Clifton 9",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Running",
    price_usd: 140.0,
    product_url: "https://hoka.com/clifton-9",
    is_active: true,
    fit_score: 85,
    image_url: "/placeholder.svg?height=200&width=200&text=Hoka+Clifton+9",
  },
  {
    id: 6,
    company: "On Cloud",
    model: "Cloudstratus 3",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Running",
    price_usd: 170.0,
    product_url: "https://on-running.com/cloudstratus-3",
    is_active: true,
    fit_score: 83,
    image_url: "/placeholder.svg?height=200&width=200&text=On+Cloud+Stratus",
  },
]

export default function RecommendationsPage() {
  const router = useRouter()
  const [user, setUser] = useState<AppUser | null>(null)
  const [showDropdown, setShowDropdown] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [shoes, setShoes] = useState<Shoe[]>([])
  const [userMeasurements, setUserMeasurements] = useState<UserMeasurements | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<"fit_score" | "price_low" | "price_high">("fit_score")

  // Check authentication and get user info
  useEffect(() => {
    checkAuth()
  }, [])

  // Load shoes when user is authenticated
  useEffect(() => {
    if (user) {
      loadShoes()
    }
  }, [user, sortBy])

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

  const loadShoes = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const token = localStorage.getItem("token")
      if (!token) {
        setError("Authentication required. Please log in again.")
        router.push("/")
        return
      }

      // BACKEND INTEGRATION POINT 1: Get User Measurements
      // TODO: Replace mock data with actual API call
      // Expected endpoint: GET /api/measurements/latest/
      // Expected response: { length_inches: number, width_inches: number, created_at: string }
      // If no measurements found, return 404 or empty response

      let measurements = null
      try {
        // Uncomment when backend is ready:
        /*
        const measurementsResponse = await fetch(`${API_BASE_URL}/api/measurements/latest/`, {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        })

        if (measurementsResponse.ok) {
          measurements = await measurementsResponse.json()
          setUserMeasurements({
            length_inches: measurements.length_inches,
            width_inches: measurements.width_inches,
          })
        }
        */

        // MOCK DATA - Remove when backend is ready
        measurements = MOCK_USER_MEASUREMENTS
        setUserMeasurements(measurements)
      } catch (error) {
        console.warn("Could not load user measurements:", error)
      }

      // BACKEND INTEGRATION POINT 2: Get Shoe Recommendations
      // TODO: Replace mock data with actual API call
      // Expected endpoint: POST /api/shoes/search/
      // Expected request body:
      /*
      {
        "measurements": {
          "length_inches": 10.5,
          "width_inches": 4.2
        },
        "preferences": {
          "gender": ["Men", "Women"],
          "brands": ["Nike", "Adidas"],
          "functions": ["Running", "Casual"],
          "max_price": 200
        },
        "limit": 20
      }
      */
      // Expected response:
      /*
      {
        "shoes": [
          {
            "id": 1,
            "company": "Nike",
            "model": "Air Max 270",
            "gender": "M",
            "us_size": 10.5,
            "width_category": "D",
            "function": "Running",
            "price_usd": 150.00,
            "product_url": "https://nike.com/...",
            "is_active": true,
            "fit_score": 95,
            "image_url": "https://example.com/shoe-image.jpg" // Optional
          }
        ],
        "total_count": 25,
        "has_more": false
      }
      */

      let shoes: Shoe[] = []

      try {
        // Uncomment when backend is ready:
        /*
        const searchResponse = await fetch(`${API_BASE_URL}/api/shoes/search/`, {
          method: "POST",
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            measurements: measurements
              ? {
                  length_inches: measurements.length_inches,
                  width_inches: measurements.width_inches,
                }
              : null,
            preferences: {
              gender: [], // Could be populated from user preferences
              brands: [],
              functions: [],
              max_price: 1000,
            },
            limit: 20,
          }),
        })

        if (searchResponse.ok) {
          const searchData = await searchResponse.json()
          shoes = searchData.shoes || []
        } else if (searchResponse.status === 404) {
          // Fallback to all shoes endpoint if search not implemented
          const allShoesResponse = await fetch(`${API_BASE_URL}/api/shoes/`, {
            headers: {
              Authorization: `Token ${token}`,
            },
          })

          if (allShoesResponse.ok) {
            shoes = await allShoesResponse.json()
            
            // Apply client-side fit scoring if measurements available
            if (measurements) {
              shoes = shoes.map((shoe) => ({
                ...shoe,
                fit_score: calculateFitScore(shoe, measurements),
              }))
            }
          }
        } else {
          throw new Error(`Search failed: ${searchResponse.status}`)
        }
        */

        // MOCK DATA - Remove when backend is ready
        shoes = MOCK_SHOES
      } catch (searchError) {
        console.warn("Search endpoint error, using mock data:", searchError)
        // MOCK DATA - Remove when backend is ready
        shoes = MOCK_SHOES
      }

      // Apply sorting
      shoes = applySorting(shoes, sortBy)
      setShoes(shoes)
    } catch (error) {
      console.error("Failed to load recommendations:", error)
      setError(error instanceof Error ? error.message : "Failed to load shoe recommendations. Please try again later.")

      // FALLBACK: Use mock data even on error
      setShoes(MOCK_SHOES)
      setUserMeasurements(MOCK_USER_MEASUREMENTS)
    } finally {
      setIsLoading(false)
    }
  }

  // BACKEND INTEGRATION POINT 3: Fit Score Calculation
  // TODO: This should ideally be calculated on the backend
  // The backend should return fit_score as part of the shoe data
  // This client-side calculation is a fallback
  const calculateFitScore = (shoe: any, measurements: any): number => {
    if (!measurements || !shoe.us_size) return 0

    // Simple fit scoring algorithm - backend should implement more sophisticated logic
    const idealLength = measurements.length_inches
    const idealWidth = measurements.width_inches

    // Convert US size to approximate length (rough conversion)
    const shoeLengthInches = shoe.us_size * 0.33 + 7.5

    // Calculate length score (closer to ideal = higher score)
    const lengthDiff = Math.abs(shoeLengthInches - idealLength)
    const lengthScore = Math.max(0, 100 - lengthDiff * 20)

    // Width score based on width category
    let widthScore = 50 // Default for unknown width
    if (shoe.width_category === "N" && idealWidth < 3.5) widthScore = 90
    else if (shoe.width_category === "D" && idealWidth >= 3.5 && idealWidth <= 4.5) widthScore = 95
    else if (shoe.width_category === "W" && idealWidth > 4.5) widthScore = 90
    else if (shoe.width_category === "D") widthScore = 80

    // Combined score
    const fitScore = Math.round(lengthScore * 0.7 + widthScore * 0.3)
    return Math.max(0, Math.min(100, fitScore))
  }

  // Helper function to apply sorting
  const applySorting = (shoes: any[], sortBy: string): any[] => {
    return [...shoes].sort((a, b) => {
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

  const getFitScoreColor = (score: number) => {
    if (score >= 90) return "text-green-600 bg-green-100"
    if (score >= 80) return "text-yellow-600 bg-yellow-100"
    return "text-red-600 bg-red-100"
  }

  const getWidthLabel = (width: string) => {
    const widthMap = { N: "Narrow", D: "Regular", W: "Wide" }
    return widthMap[width as keyof typeof widthMap] || width
  }

  const getGenderLabel = (gender: string) => {
    const genderMap = { M: "Men", W: "Women", U: "Unisex" }
    return genderMap[gender as keyof typeof genderMap] || gender
  }

  if (isLoading) {
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
              <p className="text-gray-600">Based on your foot measurements, here are the best-fitting shoes for you.</p>
            </div>

            {userMeasurements && (
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Ruler className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-900">Your Measurements</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Length:</span>
                    <span className="ml-2 font-medium text-gray-900">{userMeasurements.length_inches}"</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Width:</span>
                    <span className="ml-2 font-medium text-gray-900">{userMeasurements.width_inches}"</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-8">
          {/* Results Section */}
          <div>
            {/* Sort and Results Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
              <div>
                <p className="text-gray-600">
                  Showing {shoes.length} personalized recommendations
                  <span className="ml-2 text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">Using Mock Data</span>
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <label htmlFor="sort-select" className="text-sm font-medium text-gray-700">
                  Sort by:
                </label>
                <select
                  id="sort-select"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                >
                  <option value="fit_score">Best Fit</option>
                  <option value="price_low">Price: Low to High</option>
                  <option value="price_high">Price: High to Low</option>
                </select>
              </div>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-yellow-800">
                  <strong>Note:</strong> Using mock data for demonstration. {error}
                </p>
              </div>
            )}

            {shoes.length === 0 ? (
              <div className="bg-white rounded-lg shadow border border-gray-200 p-8 text-center">
                <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No recommendations available</h3>
                <p className="text-gray-600">Please upload a foot photo to get personalized recommendations.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {shoes.map((shoe) => (
                  <div
                    key={shoe.id}
                    className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow"
                  >
                    {/* Shoe Image */}
                    {shoe.image_url && (
                      <div className="aspect-square bg-gray-50 flex items-center justify-center">
                        <img
                          src={shoe.image_url || "/placeholder.svg"}
                          alt={`${shoe.company} ${shoe.model}`}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    )}

                    <div className="p-6">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {shoe.company} {shoe.model}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {getGenderLabel(shoe.gender)} • {shoe.function}
                          </p>
                        </div>
                        {shoe.fit_score && (
                          <div className="flex items-center space-x-1">
                            <Star className="h-4 w-4 text-yellow-400 fill-current" />
                            <div
                              className={`px-2 py-1 rounded-full text-xs font-medium ${getFitScoreColor(shoe.fit_score)}`}
                            >
                              {shoe.fit_score}% fit
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                        <div>
                          <span className="text-gray-600">Size:</span>
                          <span className="ml-2 font-medium text-gray-900">US {shoe.us_size}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Width:</span>
                          <span className="ml-2 font-medium text-gray-900">{getWidthLabel(shoe.width_category)}</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-1">
                          <DollarSign className="h-4 w-4 text-gray-500" />
                          <span className="text-lg font-bold text-gray-900">${shoe.price_usd.toFixed(2)}</span>
                        </div>
                        <a
                          href={shoe.product_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
                        >
                          <span>View Product</span>
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
