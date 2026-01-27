
import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        // Update state so the next render will show the fallback UI.
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        // You can also log the error to an error reporting service
        console.error("Uncaught error:", error, errorInfo);
        this.setState({ error, errorInfo });
    }

    handleReload = () => {
        window.location.reload();
    };

    render() {
        if (this.state.hasError) {
            // You can render any custom fallback UI
            return (
                <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
                    <div className="max-w-md w-full space-y-8 text-center">
                        <div>
                            <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                                Something went wrong
                            </h2>
                            <p className="mt-2 text-sm text-gray-600">
                                We encountered an unexpected error. Please try reloading the page.
                            </p>
                        </div>

                        <div className="rounded-md bg-red-50 p-4 text-left">
                            <div className="flex">
                                <div className="ml-3">
                                    <h3 className="text-sm font-medium text-red-800">
                                        Error Details
                                    </h3>
                                    <div className="mt-2 text-sm text-red-700 font-mono text-xs overflow-auto max-h-32">
                                        <p>{this.state.error && this.state.error.toString()}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div>
                            <button
                                onClick={this.handleReload}
                                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                            >
                                Reload Page
                            </button>
                        </div>

                        <div className="text-xs text-gray-500 mt-4">
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
