
import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Uncaught error:", error, errorInfo);
        this.setState({ error, errorInfo });
    }

    handleReload = () => {
        window.location.reload();
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center px-4 py-12">
                    <div className="max-w-md w-full space-y-8 text-center">
                        <div>
                            <h2 className="mt-6 text-3xl font-extrabold text-slate-800">
                                Something went wrong
                            </h2>
                            <p className="mt-2 text-sm text-slate-500">
                                We encountered an unexpected error. Please try reloading the page.
                            </p>
                        </div>

                        <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-left">
                            <h3 className="text-sm font-medium text-red-700">Error Details</h3>
                            <div className="mt-2 text-sm text-red-600 font-mono text-xs overflow-auto max-h-32">
                                <p>{this.state.error && this.state.error.toString()}</p>
                            </div>
                        </div>

                        <button
                            onClick={this.handleReload}
                            className="glass-btn-primary w-full py-3 rounded-xl"
                        >
                            Reload Page
                        </button>

                        <div className="text-xs text-slate-400 mt-4">
                            If this persists, please contact support.
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
