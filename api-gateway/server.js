const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const morgan = require('morgan');
const swaggerUi = require('swagger-ui-express');
const swaggerSpec = require('./config/swagger.config');
const { requireAuth } = require('./middlewares/auth.middleware');

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 4000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(morgan('dev')); // Logs HTTP requests to the console

// Swagger API Documentation Route
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// --- Routes ---
// You can later move these to a separate routes.js file in this same directory

/**
 * @swagger
 * /health:
 *   get:
 *     summary: API Gateway Health Check
 *     description: Returns the operational status of the gateway.
 *     responses:
 *       200:
 *         description: Gateway is up and running.
 */
app.get('/health', (req, res) => {
  res.status(200).json({
    success: true,
    service: 'api-gateway',
    status: 'up',
    timestamp: new Date().toISOString()
  });
});

/**
 * @swagger
 * /api/protected:
 *   get:
 *     summary: Dummy Protected Route
 *     description: Returns a success message if the user provides a valid JWT.
 *     responses:
 *       200:
 *         description: Successfully authenticated.
 *       401:
 *         description: Unauthorized.
 */
app.get('/api/protected', requireAuth, (req, res) => {
  res.status(200).json({
    success: true,
    message: 'Authentication successful! You have accessed a protected route.',
    user: req.user
  });
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    success: false,
    message: 'Internal Server Error',
    error: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Start Server
app.listen(PORT, () => {
  console.log(`🚀 API Gateway is running on http://localhost:${PORT}`);
});
