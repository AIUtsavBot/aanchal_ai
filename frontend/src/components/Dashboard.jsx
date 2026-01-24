import React from 'react'
import { Users, AlertCircle, Activity, Clock } from 'lucide-react'

export default function Dashboard({ data = {} }) {
  const stats = [
    {
      label: 'Total Mothers',
      value: data.totalMothers || 0,
      icon: Users,
      color: 'blue',
      description: 'Active registrations'
    },
    {
      label: 'High Risk Cases',
      value: data.highRiskCount || 0,
      icon: AlertCircle,
      color: 'red',
      description: 'Require immediate attention'
    },
    {
      label: 'ANC Compliance',
      value: data.compliance || '92%',
      icon: Activity,
      color: 'yellow',
      description: 'Latest week performance'
    },
    {
      label: 'Appointments',
      value: data.appointments || 0,
      icon: Clock,
      color: 'green',
      description: 'Scheduled this month'
    }
  ]

  const colorClasses = {
    blue: 'border-l-4 border-blue-500',
    red: 'border-l-4 border-red-500',
    yellow: 'border-l-4 border-yellow-500',
    green: 'border-l-4 border-green-500'
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat, idx) => {
        const Icon = stat.icon
        return (
          <div
            key={idx}
            className={`bg-white p-6 rounded-lg shadow-md ${colorClasses[stat.color]} hover:shadow-lg transition`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">{stat.label}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                <p className="text-xs text-gray-500 mt-1">{stat.description}</p>
              </div>
              <Icon className="w-12 h-12 text-gray-400 opacity-30" />
            </div>
          </div>
        )
      })}
    </div>
  )
}