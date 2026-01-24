import React from 'react'
import { Phone, MapPin } from 'lucide-react'
import { getRiskColor, getRiskBadgeColor } from '../utils/helpers'

export default function PatientCard({ mother }) {
  if (!mother) return null

  return (
    <div className={`p-6 rounded-lg border-2 ${getRiskColor(mother.risk)} shadow-md hover:shadow-lg transition`}>
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
        </div>
        <div className="text-right ml-4">
          <p className="text-3xl font-bold opacity-70">{(mother.risk * 100).toFixed(0)}%</p>
          <p className="text-xs text-gray-600">Risk Score</p>
        </div>
      </div>
    </div>
  )
}