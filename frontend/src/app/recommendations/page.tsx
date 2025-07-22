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
  Filter,
  X,
} from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"

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
  image_url?: string
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

// EXPANDED MOCK DATA for better filtering demonstration
const MOCK_USER_MEASUREMENTS: UserMeasurements = {
  length_inches: 10.5,
  width_inches: 4.2,
}

const ALL_MOCK_SHOES: Shoe[] = [
  // Nike shoes
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
    company: "Nike",
    model: "Air Force 1",
    gender: "U",
    us_size: 10.5,
    width_category: "D",
    function: "Casual",
    price_usd: 90.0,
    product_url: "https://nike.com/air-force-1",
    is_active: true,
    fit_score: 88,
    image_url: "/placeholder.svg?height=200&width=200&text=Nike+Air+Force+1",
  },
  {
    id: 3,
    company: "Nike",
    model: "Pegasus 40",
    gender: "W",
    us_size: 10.5,
    width_category: "D",
    function: "Running",
    price_usd: 130.0,
    product_url: "https://nike.com/pegasus-40",
    is_active: true,
    fit_score: 91,
    image_url: "/placeholder.svg?height=200&width=200&text=Nike+Pegasus+40",
  },

  // Adidas shoes
  {
    id: 4,
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
    id: 5,
    company: "Adidas",
    model: "Stan Smith",
    gender: "U",
    us_size: 10.5,
    width_category: "D",
    function: "Casual",
    price_usd: 80.0,
    product_url: "https://adidas.com/stan-smith",
    is_active: true,
    fit_score: 85,
    image_url: "/placeholder.svg?height=200&width=200&text=Adidas+Stan+Smith",
  },

  // New Balance shoes
  {
    id: 6,
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
    id: 7,
    company: "New Balance",
    model: "990v5",
    gender: "U",
    us_size: 10.5,
    width_category: "D",
    function: "Casual",
    price_usd: 185.0,
    product_url: "https://newbalance.com/990v5",
    is_active: true,
    fit_score: 87,
    image_url: "/placeholder.svg?height=200&width=200&text=New+Balance+990v5",
  },

  // Allbirds shoes
  {
    id: 8,
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
    id: 9,
    company: "Allbirds",
    model: "Tree Dashers",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Running",
    price_usd: 125.0,
    product_url: "https://allbirds.com/tree-dashers",
    is_active: true,
    fit_score: 84,
    image_url: "/placeholder.svg?height=200&width=200&text=Allbirds+Tree+Dashers",
  },

  // Hoka shoes
  {
    id: 10,
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
    id: 11,
    company: "Hoka",
    model: "Bondi 8",
    gender: "W",
    us_size: 10.5,
    width_category: "D",
    function: "Running",
    price_usd: 165.0,
    product_url: "https://hoka.com/bondi-8",
    is_active: true,
    fit_score: 83,
    image_url: "/placeholder.svg?height=200&width=200&text=Hoka+Bondi+8",
  },

  // On Cloud shoes
  {
    id: 12,
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
  {
    id: 13,
    company: "On Cloud",
    model: "Cloud 5",
    gender: "U",
    us_size: 10.5,
    width_category: "D",
    function: "Casual",
    price_usd: 140.0,
    product_url: "https://on-running.com/cloud-5",
    is_active: true,
    fit_score: 81,
    image_url: "/placeholder.svg?height=200&width=200&text=On+Cloud+5",
  },

  // Converse shoes
  {
    id: 14,
    company: "Converse",
    model: "Chuck Taylor All Star",
    gender: "U",
    us_size: 10.5,
    width_category: "D",
    function: "Casual",
    price_usd: 55.0,
    product_url: "https://converse.com/chuck-Taylor",
    is_active: true,
    fit_score: 75,
    image_url: "/placeholder.svg?height=200&width=200&text=Converse+Chuck+Taylor",
  },

  // Puma shoes
  {
    id: 15,
    company: "Puma",
    model: "Suede Classic",
    gender: "U",
    us_size: 10.5,
    width_category: "D",
    function: "Casual",
    price_usd: 70.0,
    product_url: "https://puma.com/suede-classic",
    is_active: true,
    fit_score: 78,
    image_url: "/placeholder.svg?height=200&width=200&text=Puma+Suede+Classic",
  },
  {
    id: 16,
    company: "Puma",
    model: "Velocity Nitro 3",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Running",
    price_usd: 110.0,
    product_url: "https://puma.com/velocity-nitro-3",
    is_active: true,
    fit_score: 82,
    image_url: "/placeholder.svg?height=200&width=200&text=Puma+Velocity+Nitro",
  },

  // Saucony shoes
  {
    id: 17,
    company: "Saucony",
    model: "Kinvara 14",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Running",
    price_usd: 110.0,
    product_url: "https://saucony.com/kinvara-14",
    is_active: true,
    fit_score: 86,
    image_url: "/placeholder.svg?height=200&width=200&text=Saucony+Kinvara+14",
  },

  // Danner shoes (Work/Hiking)
  {
    id: 18,
    company: "Danner",
    model: "Mountain 600",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Hiking",
    price_usd: 320.0,
    product_url: "https://danner.com/mountain-600",
    is_active: true,
    fit_score: 79,
    image_url: "/placeholder.svg?height=200&width=200&text=Danner+Mountain+600",
  },
  {
    id: 19,
    company: "Danner",
    model: "Bull Run",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Work",
    price_usd: 280.0,
    product_url: "https://danner.com/bull-run",
    is_active: true,
    fit_score: 77,
    image_url: "/placeholder.svg?height=200&width=200&text=Danner+Bull+Run",
  },

  // Thursday shoes (Work)
  {
    id: 20,
    company: "Thursday",
    model: "Captain Boot",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Work",
    price_usd: 199.0,
    product_url: "https://thursdayboots.com/captain",
    is_active: true,
    fit_score: 74,
    image_url: "/placeholder.svg?height=200&width=200&text=Thursday+Captain+Boot",
  },

  // Higher priced items for price filtering
  {
    id: 21,
    company: "Altra",
    model: "Lone Peak 7",
    gender: "U",
    us_size: 10.5,
    width_category: "W",
    function: "Hiking",
    price_usd: 140.0,
    product_url: "https://altra.com/lone-peak-7",
    is_active: true,
    fit_score: 88,
    image_url: "/placeholder.svg?height=200&width=200&text=Altra+Lone+Peak+7",
  },
  {
    id: 22,
    company: "Solomon",
    model: "Speedcross 5",
    gender: "M",
    us_size: 10.5,
    width_category: "D",
    function: "Hiking",
    price_usd: 130.0,
    product_url: "https://salomon.com/speedcross-5",
    is_active: true,
    fit_score: 80,
    image_url: "/placeholder.svg?height=200&width=200&text=Solomon+Speedcross+5",
  },
]

export default function RecommendationsPage() {
  const router = useRouter()
  const [user, setUser] = useState<AppUser | null>(null)
  const [showDropdown, setShowDropdown] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [allShoes, setAllShoes] = useState<Shoe[]>([]) // All shoes from "backend"
  const [filteredShoes, setFilteredShoes] = useState<Shoe[]>([]) // Filtered and sorted shoes
  const [userMeasurements, setUserMeasurements] = useState<UserMeasurements | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<"fit_score" | "price_low" | "price_high">("fit_score")
  const [showFilters, setShowFilters] = useState(false)

  // Load preferences from localStorage
  const [preferences, setPreferences] = useState<UserPreferences>({
    gender: [],
    brand: [],
    function: [],
    maxPrice: 1000,
  })

  // Check authentication and get user info
  useEffect(() => {
    checkAuth()
  }, [])

  // Load preferences and shoes when user is authenticated
  useEffect(() => {
    if (user) {
      loadSavedPreferences()
      loadAllShoes()
    }
  }, [user])

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

  const loadAllShoes = async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Get User Measurements
      let measurements = null
      try {
        // TODO: Uncomment when backend is ready
        /*
        const token = localStorage.getItem("token")
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

      // Load all shoes (simulating backend call)
      try {
        // TODO: Replace with actual backend call
        /*
        const token = localStorage.getItem("token")
        const shoesResponse = await fetch(`${API_BASE_URL}/api/shoes/all/`, {
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        })

        if (shoesResponse.ok) {
          const shoesData = await shoesResponse.json()
          setAllShoes(shoesData.shoes || [])
        } else {
          throw new Error(`Failed to load shoes: ${shoesResponse.status}`)
        }
        */

        // MOCK DATA - Using expanded shoe list
        setAllShoes(ALL_MOCK_SHOES)
      } catch (shoesError) {
        console.warn("Failed to load shoes from backend, using mock data:", shoesError)
        setAllShoes(ALL_MOCK_SHOES)
        setError("Using demo data. Backend integration pending.")
      }
    } catch (error) {
      console.error("Failed to load data:", error)
      setError(error instanceof Error ? error.message : "Failed to load shoe recommendations. Please try again later.")

      // FALLBACK: Use mock data even on error
      setAllShoes(ALL_MOCK_SHOES)
      setUserMeasurements(MOCK_USER_MEASUREMENTS)
    } finally {
      setIsLoading(false)
    }
  }

  const applyFiltersAndSorting = () => {
    let filtered = [...allShoes]

    // Apply gender filter
    if (preferences.gender.length > 0) {
      const genderCodes = preferences.gender.map((g) => (g === "Men" ? "M" : g === "Women" ? "W" : "U"))
      filtered = filtered.filter((shoe) => genderCodes.includes(shoe.gender))
    }

    // Apply brand filter
    if (preferences.brand.length > 0) {
      filtered = filtered.filter((shoe) => preferences.brand.includes(shoe.company))
    }

    // Apply function filter
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
              <p className="text-gray-600">Based on your foot measurements and preferences.</p>
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
            {/* Sort, Filter, and Results Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
              <div className="flex items-center space-x-4">
                <p className="text-gray-600">
                  Showing {filteredShoes.length} of {allShoes.length} shoes
                  <span className="ml-2 text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                    Frontend Filtering
                  </span>
                </p>

                {/* Mobile Filter Button */}
                <button
                  onClick={() => setShowFilters(true)}
                  className="sm:hidden flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors text-gray-900"
                >
                  <Filter className="h-4 w-4 text-gray-900" />
                  <span className="text-gray-900">Filters</span>
                  {getActiveFiltersCount() > 0 && (
                    <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
                      {getActiveFiltersCount()}
                    </span>
                  )}
                </button>
              </div>

              <div className="flex items-center space-x-4">
                {/* Desktop Filter Button */}
                <button
                  onClick={() => setShowFilters(true)}
                  className="hidden sm:flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors text-gray-900"
                >
                  <Filter className="h-4 w-4 text-gray-900" />
                  <span className="text-gray-900">Filters</span>
                  {getActiveFiltersCount() > 0 && (
                    <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
                      {getActiveFiltersCount()}
                    </span>
                  )}
                </button>

                <div className="flex items-center space-x-2">
                  <label htmlFor="sort-select" className="text-sm font-medium text-gray-700">
                    Sort:
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
            </div>

            {/* Active Filters Display */}
            {getActiveFiltersCount() > 0 && (
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-blue-900">Active Filters</h4>
                  <button onClick={clearAllFilters} className="text-sm text-blue-600 hover:text-blue-700">
                    Clear All
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {preferences.gender.map((gender) => (
                    <span
                      key={gender}
                      className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                    >
                      {gender}
                      <button onClick={() => handleFilterChange("gender", gender)} className="ml-1 hover:text-blue-600">
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                  {preferences.brand.map((brand) => (
                    <span
                      key={brand}
                      className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                    >
                      {brand}
                      <button onClick={() => handleFilterChange("brand", brand)} className="ml-1 hover:text-blue-600">
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                  {preferences.function.map((func) => (
                    <span
                      key={func}
                      className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                    >
                      {func}
                      <button onClick={() => handleFilterChange("function", func)} className="ml-1 hover:text-blue-600">
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                  {preferences.maxPrice < 1000 && (
                    <span className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                      Under ${preferences.maxPrice}
                      <button onClick={() => handlePriceChange(1000)} className="ml-1 hover:text-blue-600">
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  )}
                </div>
              </div>
            )}

            {error && (
              <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-yellow-800">
                  <strong>Note:</strong> {error}
                </p>
              </div>
            )}

            {filteredShoes.length === 0 ? (
              <div className="bg-white rounded-lg shadow border border-gray-200 p-8 text-center">
                <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No shoes match your filters</h3>
                <p className="text-gray-600 mb-4">Try adjusting your preferences to see more results.</p>
                <button
                  onClick={clearAllFilters}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
                >
                  Clear All Filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredShoes.map((shoe) => (
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

      {/* Filter Modal */}
      {showFilters && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Background overlay */}
          <div
            className="absolute inset-0"
            style={{ backgroundColor: "rgba(0, 0, 0, 0.3)" }}
            onClick={() => setShowFilters(false)}
          ></div>

          {/* Modal content */}
          <div className="relative bg-white rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Filter Shoes</h3>
                <button onClick={() => setShowFilters(false)} className="text-gray-400 hover:text-gray-600">
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Gender Filter */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Gender</h4>
                <div className="space-y-2">
                  {GENDER_OPTIONS.map((option) => (
                    <label key={option} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={preferences.gender.includes(option)}
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
                <h4 className="font-medium text-gray-900 mb-3">Brand</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {BRAND_OPTIONS.map((option) => (
                    <label key={option} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={preferences.brand.includes(option)}
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
                <h4 className="font-medium text-gray-900 mb-3">Function</h4>
                <div className="space-y-2">
                  {FUNCTION_OPTIONS.map((option) => (
                    <label key={option} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={preferences.function.includes(option)}
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
                    value={preferences.maxPrice}
                    onChange={(e) => handlePriceChange(Number.parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                  />
                  <div className="flex justify-between items-center text-sm text-gray-500">
                    <span>$0</span>
                    <div className="text-center">
                      <span className="font-medium text-gray-900 text-base">${preferences.maxPrice}</span>
                      <div className="text-xs text-gray-500">Current</div>
                    </div>
                    <span>$1000+</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 flex space-x-3">
              <button
                onClick={clearAllFilters}
                className="flex-1 border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-md font-medium transition-colors"
              >
                Clear All
              </button>
              <button
                onClick={() => setShowFilters(false)}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
              >
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
