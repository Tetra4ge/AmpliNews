const swaggerJsdoc = require('swagger-jsdoc');

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Transformation Intelligence API Gateway',
      version: '1.0.0',
      description: 'API documentation for the Monolith to Microservices Transformation Gateway',
    },
    servers: [
      {
        url: 'http://localhost:4000',
        description: 'Development server',
      },
    ],
  },
  // Pointing to where your endpoints will be defined for Swagger to read the comments
  apis: ['./routes/*.js', './controllers/*.js', './server.js'],
};

const swaggerSpec = swaggerJsdoc(options);

module.exports = swaggerSpec;
