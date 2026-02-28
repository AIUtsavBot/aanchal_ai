const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');

const app = express();
const PORT = 3001;
const TARGET = 'https://aanchal-ai-6ns2.onrender.com';

// 1. Enable CORS for all incoming requests from the Expo Web app (localhost:8081)
app.use(cors({ origin: true, credentials: true }));

// 2. Setup the proxy middleware to forward requests to the Render backend
app.use(
    '/',
    createProxyMiddleware({
        target: TARGET,
        changeOrigin: true, // This is critical for Render to accept the host header
        secure: false, // Bypass SSL certificate validation if there's a strict CA issue
        onProxyReq: (proxyReq, req, res) => {
            // Remove headers that might cause the remote server to block the request
            proxyReq.removeHeader('origin');
            proxyReq.removeHeader('referer');
            console.log(`[PROXY] ${req.method} ${req.originalUrl}`);
        },
        onProxyRes: (proxyRes, req, res) => {
            // Strip the CORS headers coming directly from the backend to prevent conflicts
            // with our own `cors()` middleware above.
            delete proxyRes.headers['access-control-allow-origin'];
            delete proxyRes.headers['access-control-allow-methods'];
            delete proxyRes.headers['access-control-allow-headers'];
            delete proxyRes.headers['access-control-allow-credentials'];
        },
        onError: (err, req, res) => {
            console.error(`[PROXY ERROR] ${err.message}`);
            res.status(500).send('Proxy Error');
        }
    })
);

app.listen(PORT, () => {
    console.log(`\n==============================================`);
    console.log(`🚀 Aanchal AI Robust Express Proxy Running`);
    console.log(`==============================================`);
    console.log(`🌐 Listening on: http://localhost:${PORT}`);
    console.log(`🔄 Forwarding to: ${TARGET}`);
    console.log(`\nYour mobile app in Web Mode will use this to bypass CORS.`);
    console.log(`Keep this terminal running while testing in the browser!\n`);
});
