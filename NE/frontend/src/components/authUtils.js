const TOKEN_KEY = 'jwt_token';

export const getToken = () => {
    const token = localStorage.getItem(TOKEN_KEY);
    console.log(`[authUtils] GET: Retrieved token from localStorage:`, token ? 'Token exists' : 'Token missing');
    return token;
};

export const setToken = (token) => {
    localStorage.setItem(TOKEN_KEY, token);
    console.log(`[authUtils] SET: Token stored in localStorage`);
};

export const removeToken = () => {
    localStorage.removeItem(TOKEN_KEY);
    console.log(`[authUtils] REMOVE: Token removed from localStorage`);
};

const USERNAME_KEY = 'username';

export const setUsername = (username) => {
    localStorage.setItem(USERNAME_KEY, username);
    console.log(`[authUtils] SET: Username stored:`, username);
};

export const getUsername = () => {
    const username = localStorage.getItem(USERNAME_KEY);
    console.log(`[authUtils] GET: Retrieved username:`, username);
    return username;
};

// Enhanced auth headers with better error handling
export const getAuthHeaders = () => {
    const token = getToken();
    console.log(`[authUtils] getAuthHeaders: Token present:`, !!token);
    
    if (!token) {
        console.warn('[authUtils] WARNING: No token found for auth headers');
        return {
            'Content-Type': 'application/json'
        };
    }
    
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
};

export const getAuthHeadersMultipart = () => {
    const token = getToken();
    console.log(`[authUtils] getAuthHeadersMultipart: Token present:`, !!token);
    
    if (!token) {
        console.warn('[authUtils] WARNING: No token found for multipart auth headers');
        return {};
    }
    
    return {
        'Authorization': `Bearer ${token}`
    };
};

export const ensureValidToken = async () => {
    const token = getToken();
    
    if (!token) {
        console.warn('[authUtils] No token found');
        return false;
    }
    
    // Check if token is about to expire and refresh if needed
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000;
        const now = Date.now();
        const bufferTime = 15 * 60 * 1000;
        
        if (exp - now < bufferTime) {
            console.log('[authUtils] Token needs refresh, attempting...');
            return await refreshTokenIfNeeded();
        }
        
        return true;
    } catch (error) {
        console.error('[authUtils] Error validating token:', error);
        return false;
    }
};


// Enhanced token validation
export const validateToken = () => {
    const token = getToken();
    console.log(`[authUtils] validateToken: Checking token validity`);
    
    if (!token) {
        console.log('[authUtils] validateToken: No token found');
        return false;
    }
    
    try {
        // Check if token is expired
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000; // Convert to milliseconds
        const now = Date.now();
        
        console.log(`[authUtils] validateToken: Token expires at:`, new Date(exp));
        console.log(`[authUtils] validateToken: Current time:`, new Date(now));
        console.log(`[authUtils] validateToken: Time remaining:`, Math.floor((exp - now) / 1000 / 60), 'minutes');
        
        if (exp < now) {
            console.log('[authUtils] validateToken: Token has expired');
            removeToken();
            return false;
        }
        
        console.log('[authUtils] validateToken: Token is valid for user:', payload.username, 'role:', payload.role);
        return true;
    } catch (error) {
        console.error('[authUtils] validateToken: Error parsing token:', error);
        removeToken();
        return false;
    }
};

// Enhanced token refresh
export const refreshTokenIfNeeded = async () => {
    try {
        const token = getToken();
        if (!token) {
            console.log('[authUtils] refreshTokenIfNeeded: No token to refresh');
            return false;
        }

        // Check if token is expired or about to expire
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000; // Convert to milliseconds
        const now = Date.now();
        const bufferTime = 5 * 60 * 1000; // 5 minutes buffer

        console.log(`[authUtils] refreshTokenIfNeeded: Token expires in:`, Math.floor((exp - now) / 1000 / 60), 'minutes');

        if (exp - now < bufferTime) {
            // Token is about to expire, refresh it
            console.log('[authUtils] refreshTokenIfNeeded: Token needs refresh, calling API...');
            
            const response = await fetch('http://127.0.0.1:5001/refresh-token', {
                method: 'POST',
                headers: getAuthHeaders()
            });

            if (response.ok) {
                const data = await response.json();
                setToken(data.token);
                console.log('[authUtils] refreshTokenIfNeeded: Token refreshed successfully');
                return true;
            } else {
                console.warn('[authUtils] refreshTokenIfNeeded: Token refresh failed');
                // If refresh fails, clear token to force re-login
                removeToken();
                return false;
            }
        }
        
        console.log('[authUtils] refreshTokenIfNeeded: Token does not need refresh');
        return true;
    } catch (error) {
        console.error('[authUtils] refreshTokenIfNeeded: Error refreshing token:', error);
        return false;
    }
};

// New function: Ensure authenticated requests
export const ensureAuthenticatedRequest = async () => {
    const isValid = validateToken();
    if (!isValid) {
        console.log('[authUtils] ensureAuthenticatedRequest: Token invalid, redirecting to login');
        window.location.href = '/login';
        return false;
    }
    
    const refreshed = await refreshTokenIfNeeded();
    if (!refreshed) {
        console.log('[authUtils] ensureAuthenticatedRequest: Token refresh failed, redirecting to login');
        window.location.href = '/login';
        return false;
    }
    
    return true;
};