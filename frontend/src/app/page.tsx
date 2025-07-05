"use client"

import type React from "react"
import { useState } from "react"
import { Upload, Camera, Ruler, ShoppingBag, User, Settings, LogOut, ChevronDown } from "lucide-react"
import Image from "next/image"

export default function Dashboard() {
  const [dragActive, setDragActive] = useState(false)
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)

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
  
 const handleFile = (file: File) => {
  if (file.type.startsWith("image/")) {
    const formData = new FormData();
    formData.append("image", file);

    setIsProcessing(true);

    fetch("http://localhost:8000/api/upload/", {
      method: "POST",
      body: formData,
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) {
          console.error("Upload error:", data);
        } else {
          console.log("Upload success:", data);
        }
      })
      .catch((err) => console.error("Network error:", err))
      .finally(() => setIsProcessing(false));

    const reader = new FileReader();
    reader.onload = (e) => setUploadedImage(e.target?.result as string);
    reader.readAsDataURL(file);
  }
  };





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
            <div className="relative">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="flex items-center space-x-2 p-2 rounded-full hover:bg-gray-100 transition-colors"
              >
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  FL
                </div>
                <ChevronDown className="h-4 w-4 text-gray-500" />
              </button>
              {showDropdown && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">First Last</p>
                    <p className="text-xs text-gray-500">name@example.com</p>
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
                    <button className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
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
            Upload a photo of your insole on paper to get accurate measurements and personalized shoe recommendations.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-8">
          <div className="bg-white rounded-lg shadow border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                <Camera className="h-5 w-5" />
                <h3 className="text-lg font-semibold text-gray-900">Upload Insole Photo</h3>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Place your insole on a piece of paper and take a clear photo from directly above
              </p>
            </div>
            <div className="p-6">
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
                      alt="Uploaded insole"
                      width={600}
                      height={400}
                      className="w-full h-64 object-cover rounded-lg border"
                    />
                    {isProcessing && (
                      <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
                        <div className="text-white text-center">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
                          <p>Processing image...</p>
                        </div>
                      </div>
                    )}
                  </div>
                  {!isProcessing && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-3">
                        <Ruler className="h-5 w-5 text-green-600" />
                        <h3 className="font-medium text-green-900">Measurements Complete</h3>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Length:</span>
                          <span className="ml-2 font-medium text-green-900">26.5 cm</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Width:</span>
                          <span className="ml-2 font-medium text-green-900">10.2 cm</span>
                        </div>
                      </div>
                      <button className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-medium transition-colors">
                        View Shoe Recommendations
                      </button>
                    </div>
                  )}
                  <button
                    onClick={() => {
                      setUploadedImage(null)
                      setIsProcessing(false)
                    }}
                    className="w-full border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-md font-medium transition-colors"
                  >
                    Upload Another Photo
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
