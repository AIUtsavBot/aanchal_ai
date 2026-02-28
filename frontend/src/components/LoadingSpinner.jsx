import React from 'react';
import { Loader } from 'lucide-react';

const LoadingSpinner = () => {
    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="flex flex-col items-center gap-3">
                <Loader className="w-10 h-10 text-blue-500 animate-spin" />
                <p className="text-slate-400 font-medium text-sm">Loading...</p>
            </div>
        </div>
    );
};

export default LoadingSpinner;
