import React from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Area,
    ComposedChart
} from 'recharts';

// WHO Child Growth Standards (Simplified Weight-for-Age 0-24 months)
// Source: WHO Multicentre Growth Reference Study
const WHO_STANDARDS = [
    { age: 0, minWeight: 2.5, maxWeight: 4.4, median: 3.3 },
    { age: 2, minWeight: 4.3, maxWeight: 7.1, median: 5.6 },
    { age: 4, minWeight: 5.6, maxWeight: 8.7, median: 7.0 },
    { age: 6, minWeight: 6.4, maxWeight: 9.8, median: 7.9 },
    { age: 8, minWeight: 6.9, maxWeight: 10.7, median: 8.6 },
    { age: 10, minWeight: 7.4, maxWeight: 11.5, median: 9.2 },
    { age: 12, minWeight: 7.7, maxWeight: 12.0, median: 9.6 },
    { age: 14, minWeight: 8.1, maxWeight: 12.6, median: 10.1 },
    { age: 16, minWeight: 8.4, maxWeight: 13.1, median: 10.5 },
    { age: 18, minWeight: 8.8, maxWeight: 13.7, median: 10.9 },
    { age: 20, minWeight: 9.1, maxWeight: 14.2, median: 11.3 },
    { age: 22, minWeight: 9.4, maxWeight: 14.8, median: 11.8 },
    { age: 24, minWeight: 9.7, maxWeight: 15.3, median: 12.2 }
];

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                <p className="font-bold text-gray-700 mb-1">Age: {label} months</p>

                {payload.map((entry, index) => (
                    <p key={index} style={{ color: entry.color }} className="text-sm font-medium">
                        {entry.name}: {entry.value} kg
                    </p>
                ))}

                <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-500">
                    <p>WHO Normal Range: 2.5kg - 15.3kg</p>
                </div>
            </div>
        );
    }
    return null;
};

export default function GrowthChart({ data = [] }) {
    // Merge child data with standards structure for plotting
    // Note: Real implementation would interpolate, but this is a visual approximation
    const chartData = WHO_STANDARDS.map(std => {
        // Find closest data point from child records
        // Assuming data has { age_months, weight }
        const childRecord = data.find(d => Math.abs(d.age_months - std.age) < 1);

        return {
            name: `${std.age}m`,
            age: std.age,
            // Ranges for background areas
            malnutrition: std.minWeight, // Everything below this is risk
            normalRange: [std.minWeight, std.maxWeight], // Green zone

            // Child's actual data
            childWeight: childRecord ? childRecord.weight : null,

            // Reference lines
            median: std.median
        };
    });

    return (
        <div className="w-full h-[300px] bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                    📉 Growth Monitoring Chart
                </h3>
                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full border border-green-200">
                    WHO Standards (0-2y)
                </span>
            </div>

            <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                    <XAxis
                        dataKey="age"
                        label={{ value: 'Age (Months)', position: 'insideBottom', offset: -5 }}
                        tick={{ fontSize: 12 }}
                    />
                    <YAxis
                        label={{ value: 'Weight (kg)', angle: -90, position: 'insideLeft' }}
                        domain={[0, 16]}
                        tick={{ fontSize: 12 }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ paddingTop: '10px' }} />

                    {/* Malnutrition Risk Area (Red) */}
                    <Area
                        type="monotone"
                        dataKey="malnutrition"
                        name="Severe Risk (< -2SD)"
                        stroke="none"
                        fill="#fee2e2"
                        fillOpacity={0.6}
                    />

                    {/* Normal Range Area (Green) */}
                    {/* Recharts Area doesn't natively support range arrays easily in all versions, 
              so we act roughly: plot max and fill down, then overlay? 
              Actually, stacked areas are better. 
              Let's stick to simple Lines for Median and Min/Max for clarity in v1 
          */}

                    <Line
                        type="monotone"
                        dataKey="maxWeight"
                        name="Upper Limit (+2SD)"
                        stroke="#bbf7d0"
                        strokeWidth={2}
                        dot={false}
                        strokeDasharray="5 5"
                    />

                    <Line
                        type="monotone"
                        dataKey="median"
                        name="WHO Median"
                        stroke="#22c55e"
                        strokeWidth={2}
                        dot={false}
                    />

                    <Line
                        type="monotone"
                        dataKey="malnutrition"
                        name="Lower Limit (-2SD)"
                        stroke="#ef4444"
                        strokeWidth={2}
                        dot={false}
                        strokeDasharray="5 5"
                    />

                    {/* Child's Trajectory */}
                    <Line
                        type="monotone"
                        dataKey="childWeight"
                        name="Child's Weight"
                        stroke="#3b82f6"
                        strokeWidth={3}
                        dot={{ r: 4, fill: "#3b82f6", strokeWidth: 2, stroke: "#fff" }}
                        connectNulls
                    />

                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
}
