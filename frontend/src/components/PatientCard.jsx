import React, { useState } from 'react'
import { Phone, MapPin, Baby, ChevronDown, ChevronUp, Loader } from 'lucide-react'
import { getRiskColor, getRiskBadgeColor } from '../utils/helpers'
import GrowthChart from './GrowthChart'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function PatientCard({ mother }) {
  const [showGrowth, setShowGrowth] = useState(false)
  const [childrenData, setChildrenData] = useState([])
  const [loadingGrowth, setLoadingGrowth] = useState(false)

  if (!mother) return null

  const isPostnatal = mother.status === 'Postnatal' || mother.status === 'Delivered' || mother.delivery_status === 'delivered' || mother.active_system === 'santanraksha'

  const handleToggleGrowth = async () => {
    if (!showGrowth) {
      // Fetch if opening
      if (childrenData.length === 0) {
        setLoadingGrowth(true)
        try {
          // Use the endpoint we just created
          const res = await fetch(`${API_URL}/api/delivery/children/${mother.id}`)
          const data = await res.json()
          if (data.success && data.children) {
            setChildrenData(data.children)
          }
        } catch (e) {
          console.error("Failed to fetch children", e)
        } finally {
          setLoadingGrowth(false)
        }
      }
    }
    setShowGrowth(!showGrowth)
  }

  return (
    <div className={`p-6 rounded-lg border-2 ${getRiskColor(mother.risk)} shadow-md hover:shadow-lg transition bg-white`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-bold">{mother.name}</h3>
            <span className={`px-3 py-1 rounded-full text-white text-xs font-bold ${getRiskBadgeColor(mother.status)}`}>
              {mother.status}
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-600 text-xs">Age</p>
              <p className="font-semibold">{mother.age} years</p>
            </div>
            <div>
              <p className="text-gray-600 text-xs">Gravida</p>
              <p className="font-semibold">{mother.gravida}</p>
            </div>
            <div className="flex items-center gap-1">
              <Phone className="w-4 h-4 text-gray-500" />
              <p className="font-semibold">{mother.phone}</p>
            </div>
            <div className="flex items-center gap-1">
              <MapPin className="w-4 h-4 text-gray-500" />
              <p className="font-semibold text-xs">{mother.location}</p>
            </div>
          </div>

          {/* Postnatal Actions */}
          {isPostnatal && (
            <div className="mt-4 pt-3 border-t border-gray-100">
              <button
                onClick={handleToggleGrowth}
                className="flex items-center gap-2 text-sm font-semibold text-teal-600 hover:text-teal-800 transition-colors"
              >
                <Baby className="w-4 h-4" />
                {showGrowth ? 'Hide Growth Charts' : 'View Child Growth'}
                {showGrowth ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            </div>
          )}
        </div>
        <div className="text-right ml-4">
          <p className="text-3xl font-bold opacity-70">{(mother.risk * 100).toFixed(0)}%</p>
          <p className="text-xs text-gray-600">Risk Score</p>
        </div>
      </div>

      {/* Expanded Growth Section */}
      {showGrowth && (
        <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
          {loadingGrowth ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <Loader className="w-6 h-6 animate-spin mr-2" />
              Loading child records...
            </div>
          ) : childrenData.length > 0 ? (
            <div className="space-y-6">
              {childrenData.map((child, idx) => (
                <div key={idx} className="bg-teal-50 p-4 rounded-xl">
                  <h4 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
                    👶 {child.name}
                    <span className="text-xs font-normal text-gray-500">({child.gender})</span>
                  </h4>
                  <GrowthChart data={child.growth_history || []} />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4 text-gray-500 italic bg-gray-50 rounded-lg">
              No child records found linked to this profile.
            </div>
          )}
        </div>
      )}
    </div>
  )
}