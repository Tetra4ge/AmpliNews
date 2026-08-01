const jwt = require('jsonwebtoken');

const requireAuth = (req, res, next) => {
  try {
    // 1. Get the token from the Authorization header
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ 
        success: false, 
        message: 'Authentication required. No token provided.' 
      });
    }

    const token = authHeader.split(' ')[1];

    // 2. Verify the token using the Supabase JWT Secret
    // Supabase signs their JWTs using the secret provided in your dashboard
    const decoded = jwt.verify(token, process.env.SUPABASE_JWT_SECRET);
    
    // 3. Attach the decoded user payload to the request object
    req.user = decoded;
    
    // 4. Move to the next middleware or route handler
    next();
  } catch (error) {
    console.error('JWT Verification Error:', error.message);
    return res.status(401).json({ 
      success: false, 
      message: 'Invalid or expired token.' 
    });
  }
};

module.exports = { requireAuth };
